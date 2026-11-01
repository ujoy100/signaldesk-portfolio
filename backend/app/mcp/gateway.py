"""MCP Gateway with namespaced discovery, authorization, routing, and audit."""

import json
from collections.abc import Awaitable, Callable, Mapping
from time import perf_counter
from uuid import uuid4

import anyio
from mcp.client import Client
from mcp.server import MCPServer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.auth import authenticate_bearer_token
from backend.app.core.config import Settings
from backend.app.mcp.contracts import (
    GatewayPrincipal,
    GatewayResponse,
    ToolError,
)
from backend.app.models.audit_event import AuditEvent
from backend.app.models.role import Role
from backend.app.models.user import User
from backend.app.observability import TelemetryRecorder
from backend.app.services.approvals import ApprovalError, ApprovalService

AuditWriter = Callable[[dict], Awaitable[None]]

READ_POLICIES = {
    "support_agent": {"knowledge", "customer", "ticket"},
    "supervisor": {"knowledge", "customer", "ticket"},
    "admin": {"knowledge", "customer", "ticket"},
    "customer": {"knowledge"},
}
CONTROLLED_WRITES = {
    "ticket.create_ticket",
    "ticket.update_ticket",
    "knowledge.promote_knowledge",
}


def create_database_audit_writer(
    session_factory: Callable[[], Session],
) -> AuditWriter:
    """Persist gateway decisions without storing tool arguments or secrets."""

    async def write(event: dict) -> None:
        with session_factory() as session:
            session.add(
                AuditEvent(
                    actor_type="user",
                    actor_id=event["actor_id"],
                    action="mcp_gateway_call",
                    resource_type="mcp_tool",
                    resource_id=f"{event['namespace']}.{event['tool']}",
                    outcome="allowed" if event["allowed"] else "denied",
                    details=json.dumps(
                        {
                            "request_id": event["request_id"],
                            "subject": event["subject"],
                            "role": event["role"],
                            "error_code": event["error_code"],
                        },
                        sort_keys=True,
                    ),
                )
            )
            session.commit()

    return write


class MCPGateway:
    """Route calls through MCP clients; never invoke server functions directly."""

    def __init__(
        self,
        servers: Mapping[str, MCPServer],
        *,
        audit_writer: AuditWriter | None = None,
        timeout_seconds: float = 5.0,
        approval_session_factory: Callable[[], Session] | None = None,
        identity_session_factory: Callable[[], Session] | None = None,
        telemetry_recorder: TelemetryRecorder | None = None,
    ) -> None:
        self.servers = dict(servers)
        self.audit_writer = audit_writer
        self.timeout_seconds = timeout_seconds
        self.approval_session_factory = approval_session_factory
        self.identity_session_factory = identity_session_factory
        self.telemetry = telemetry_recorder

    async def invoke_authenticated(
        self,
        token: str,
        settings: Settings,
        namespace: str,
        tool: str,
        arguments: dict,
        *,
        approval_id: int | None = None,
        execution_request_id: str | None = None,
    ) -> GatewayResponse:
        """Authenticate an external request before MCP routing."""

        authenticated = authenticate_bearer_token(token, settings)
        return await self.invoke(
            namespace,
            tool,
            arguments,
            GatewayPrincipal(
                subject=authenticated.subject,
                role=authenticated.role,
                actor_id=authenticated.actor_id,
            ),
            approval_id=approval_id,
            execution_request_id=execution_request_id,
        )

    async def discover(self, principal: GatewayPrincipal) -> dict[str, list[str]]:
        allowed_namespaces = READ_POLICIES.get(principal.role, set())
        discovered: dict[str, list[str]] = {}
        for namespace, server in self.servers.items():
            if namespace not in allowed_namespaces:
                continue
            async with Client(server, raise_exceptions=False) as client:
                tools = await client.list_tools()
                discovered[namespace] = [tool.name for tool in tools.tools]
        return discovered

    async def invoke(
        self,
        namespace: str,
        tool: str,
        arguments: dict,
        principal: GatewayPrincipal,
        *,
        approval_id: int | None = None,
        execution_request_id: str | None = None,
    ) -> GatewayResponse:
        request_id = str(uuid4())
        started = perf_counter()
        qualified = f"{namespace}.{tool}"
        if self.identity_session_factory is not None:
            if principal.actor_id is None:
                return await self._denied(
                    request_id, namespace, tool, principal, "database_identity_required"
                )
            with self.identity_session_factory() as identity_session:
                database_role = identity_session.scalar(
                    select(Role.name)
                    .join(User, User.role_id == Role.id)
                    .where(
                        User.id == principal.actor_id,
                        User.is_active.is_(True),
                    )
                )
            if database_role != principal.role:
                return await self._denied(
                    request_id, namespace, tool, principal, "identity_role_mismatch"
                )
        if namespace not in READ_POLICIES.get(principal.role, set()):
            return await self._denied(
                request_id, namespace, tool, principal, "role_not_authorized"
            )
        if qualified in CONTROLLED_WRITES:
            if (
                self.approval_session_factory is None
                or approval_id is None
                or execution_request_id is None
                or principal.role not in {"supervisor", "admin"}
            ):
                return await self._denied(
                    request_id,
                    namespace,
                    tool,
                    principal,
                    "verified_human_approval_required",
                )
            action_payload = dict(arguments)
            action_payload.pop("approval_id", None)
            action_payload.pop("execution_request_id", None)
            try:
                with self.approval_session_factory() as approval_session:
                    ApprovalService(approval_session).verify(
                        approval_id=approval_id,
                        operation=tool,
                        payload=action_payload,
                        execution_request_id=execution_request_id,
                    )
            except ApprovalError:
                return await self._denied(
                    request_id,
                    namespace,
                    tool,
                    principal,
                    "approval_invalid_or_mismatched",
                )
            arguments = {
                **action_payload,
                "approval_id": approval_id,
                "execution_request_id": execution_request_id,
            }
        server = self.servers.get(namespace)
        if server is None:
            return await self._error(
                request_id,
                namespace,
                tool,
                principal,
                "service_unavailable",
                "MCP namespace is unavailable",
                retryable=True,
            )

        attempts = 2
        for attempt in range(attempts):
            try:
                with anyio.fail_after(self.timeout_seconds):
                    async with Client(
                        server,
                        raise_exceptions=False,
                        read_timeout_seconds=self.timeout_seconds,
                    ) as client:
                        available = await client.list_tools()
                        if tool not in {item.name for item in available.tools}:
                            return await self._error(
                                request_id,
                                namespace,
                                tool,
                                principal,
                                "unsupported_tool",
                                "Tool is not exposed by this MCP server",
                            )
                        result = await client.call_tool(tool, arguments)
                        if result.is_error:
                            return await self._error(
                                request_id,
                                namespace,
                                tool,
                                principal,
                                "tool_error",
                                "MCP tool rejected the request",
                            )
                        response = GatewayResponse(
                            request_id=request_id,
                            namespace=namespace,
                            tool=tool,
                            allowed=True,
                            result=result.structured_content or {},
                        )
                        await self._audit(response, principal)
                        if self.telemetry:
                            self.telemetry.record(
                                "mcp.tool",
                                started=started,
                                namespace=namespace,
                                tool=tool,
                                request_id=request_id,
                            )
                        return response
            except (TimeoutError, OSError) as error:
                if attempt + 1 == attempts:
                    return await self._error(
                        request_id,
                        namespace,
                        tool,
                        principal,
                        "service_unavailable",
                        type(error).__name__,
                        retryable=True,
                    )
        raise AssertionError("unreachable")

    async def _denied(
        self,
        request_id: str,
        namespace: str,
        tool: str,
        principal: GatewayPrincipal,
        reason: str,
    ) -> GatewayResponse:
        response = GatewayResponse(
            request_id=request_id,
            namespace=namespace,
            tool=tool,
            allowed=False,
            error=ToolError(code="access_denied", message=reason),
        )
        await self._audit(response, principal)
        if self.telemetry:
            self.telemetry.record(
                "mcp.tool",
                outcome="denied",
                namespace=namespace,
                tool=tool,
                request_id=request_id,
                error_code="access_denied",
            )
        return response

    async def _error(
        self,
        request_id: str,
        namespace: str,
        tool: str,
        principal: GatewayPrincipal,
        code: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> GatewayResponse:
        response = GatewayResponse(
            request_id=request_id,
            namespace=namespace,
            tool=tool,
            allowed=False,
            error=ToolError(code=code, message=message, retryable=retryable),
        )
        await self._audit(response, principal)
        if self.telemetry:
            self.telemetry.record(
                "mcp.tool",
                outcome="error",
                namespace=namespace,
                tool=tool,
                request_id=request_id,
                error_code=code,
                retryable=retryable,
            )
        return response

    async def _audit(
        self, response: GatewayResponse, principal: GatewayPrincipal
    ) -> None:
        if self.audit_writer:
            await self.audit_writer(
                {
                    "request_id": response.request_id,
                    "subject": principal.subject,
                    "actor_id": principal.actor_id,
                    "role": principal.role,
                    "namespace": response.namespace,
                    "tool": response.tool,
                    "allowed": response.allowed,
                    "error_code": response.error.code if response.error else None,
                }
            )
