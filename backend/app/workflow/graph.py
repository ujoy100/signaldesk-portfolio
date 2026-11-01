"""Frozen deterministic support workflow implemented as a genuine StateGraph."""

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from time import perf_counter
from typing import Any, Protocol, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import ValidationError
from qdrant_client.http.exceptions import ResponseHandlingException
from sqlalchemy.orm import Session

from backend.app.knowledge.models import RetrievalFilters, RetrievalResponse
from backend.app.mcp.contracts import (
    CustomerPlanOutput,
    GatewayPrincipal,
    ServiceStatusOutput,
    TicketHistoryOutput,
)
from backend.app.mcp.gateway import MCPGateway
from backend.app.observability import TelemetryRecorder
from backend.app.schemas.support import (
    InvestigationResult,
    ResolutionEvidence,
    SupportResolution,
    TicketDraft,
)
from backend.app.services.approvals import ApprovalService
from backend.app.workflow.investigation import (
    InvestigationRunner,
    InvestigationUnavailable,
)


class Retriever(Protocol):
    def retrieve(self, query: str, **kwargs: Any) -> RetrievalResponse: ...


class SupportState(TypedDict, total=False):
    issue: str
    thread_id: str
    customer_id: int | None
    ticket_id: int | None
    propose_ticket_update: bool
    principal: dict
    issue_type: str
    complexity: str
    required_tools: list[str]
    evidence: list[dict]
    errors: list[str]
    resolution: dict
    investigation: dict
    approval_id: int
    approval_decision: str
    execution_result: dict
    status: str


class SupportWorkflow:
    """Injectable graph runtime; authoritative data is only read through Gateway."""

    def __init__(
        self,
        retriever: Retriever,
        gateway: MCPGateway,
        session_factory: Callable[[], Session],
        *,
        checkpointer: Any,
        investigator: InvestigationRunner | None = None,
        telemetry_recorder: TelemetryRecorder | None = None,
    ) -> None:
        self.retriever = retriever
        self.gateway = gateway
        self.session_factory = session_factory
        self.investigator = investigator
        self.telemetry = telemetry_recorder
        self.graph = self._build().compile(checkpointer=checkpointer)

    def _build(self) -> StateGraph:
        graph = StateGraph(SupportState)
        graph.add_node(
            "classify_issue", self._timed("classify_issue", self.classify_issue)
        )
        graph.add_node(
            "retrieve_knowledge",
            self._timed("retrieve_knowledge", self.retrieve_knowledge),
        )
        graph.add_node(
            "investigate_complex_issue",
            self._timed("investigate_complex_issue", self.investigate_complex_issue),
        )
        graph.add_node(
            "determine_required_tools",
            self._timed("determine_required_tools", self.determine_required_tools),
        )
        graph.add_node(
            "check_customer_data",
            self._timed("check_customer_data", self.check_customer_data),
        )
        graph.add_node(
            "check_ticket_history",
            self._timed("check_ticket_history", self.check_ticket_history),
        )
        graph.add_node(
            "aggregate_evidence",
            self._timed("aggregate_evidence", self.aggregate_evidence),
        )
        graph.add_node(
            "generate_structured_resolution",
            self._timed("generate_structured_resolution", self.generate_resolution),
        )
        graph.add_node(
            "create_approval", self._timed("create_approval", self.create_approval)
        )
        graph.add_node(
            "human_approval", self._timed("human_approval", self.human_approval)
        )
        graph.add_node(
            "execute_action", self._timed("execute_action", self.execute_action)
        )
        graph.add_node("audit_log", self._timed("audit_log", self.audit_log))
        graph.add_node(
            "final_response", self._timed("final_response", self.final_response)
        )
        graph.add_edge(START, "classify_issue")
        graph.add_conditional_edges(
            "classify_issue",
            lambda state: state["complexity"],
            {
                "simple": "retrieve_knowledge",
                "investigation": "investigate_complex_issue",
            },
        )
        graph.add_edge("investigate_complex_issue", "generate_structured_resolution")
        graph.add_edge("retrieve_knowledge", "determine_required_tools")
        graph.add_edge("determine_required_tools", "check_customer_data")
        graph.add_edge("check_customer_data", "check_ticket_history")
        graph.add_edge("check_ticket_history", "aggregate_evidence")
        graph.add_edge("aggregate_evidence", "generate_structured_resolution")
        graph.add_conditional_edges(
            "generate_structured_resolution",
            lambda state: (
                "approval" if state["resolution"]["action_required"] else "final"
            ),
            {"approval": "create_approval", "final": "final_response"},
        )
        graph.add_edge("create_approval", "human_approval")
        graph.add_conditional_edges(
            "human_approval",
            lambda state: (
                "execute"
                if state["approval_decision"] in {"approve", "edit"}
                else "final"
            ),
            {"execute": "execute_action", "final": "final_response"},
        )
        graph.add_edge("execute_action", "audit_log")
        graph.add_edge("audit_log", "final_response")
        graph.add_edge("final_response", END)
        return graph

    def _timed(self, name: str, function: Callable) -> Callable:
        if self.telemetry is None:
            return function
        if iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                started = perf_counter()
                try:
                    result = await function(*args, **kwargs)
                    self.telemetry.record(f"workflow.node.{name}", started=started)
                    return result
                except Exception:
                    self.telemetry.record(
                        f"workflow.node.{name}", started=started, outcome="error"
                    )
                    raise

            return async_wrapper

        @wraps(function)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            started = perf_counter()
            try:
                result = function(*args, **kwargs)
                self.telemetry.record(f"workflow.node.{name}", started=started)
                return result
            except Exception:
                self.telemetry.record(
                    f"workflow.node.{name}", started=started, outcome="error"
                )
                raise

        return sync_wrapper

    def classify_issue(self, state: SupportState) -> dict:
        issue = state["issue"].lower()
        kind = (
            "roaming"
            if "roam" in issue
            else "sim_activation"
            if "sim" in issue
            else "billing"
            if any(word in issue for word in ("bill", "charge", "invoice"))
            else "network"
            if any(word in issue for word in ("network", "outage", "signal"))
            else "general"
        )
        repeated = any(
            word in issue
            for word in ("repeated", "recurring", "again", "multiple times", "history")
        )
        multi_source = (
            kind in {"roaming", "billing", "network"}
            and repeated
            and (
                (
                    state.get("customer_id") is not None
                    and state.get("ticket_id") is not None
                )
                or any(
                    word in issue
                    for word in ("policy", "eligibility", "activation", "records")
                )
            )
        )
        return {
            "issue_type": kind,
            "complexity": "investigation" if multi_source else "simple",
            "errors": [],
            "evidence": [],
        }

    def retrieve_knowledge(self, state: SupportState) -> dict:
        try:
            principal = self._principal(state)
            result = self.retriever.retrieve(
                state["issue"],
                strategy="hybrid_reranked",
                filters=RetrievalFilters(
                    access_roles=["public", principal.role], active_only=True
                ),
            )
        except (OSError, RuntimeError, ValueError, ResponseHandlingException):
            return {"errors": [*state.get("errors", []), "knowledge_unavailable"]}
        evidence = [
            ResolutionEvidence(
                source_type="knowledge",
                source_id=item.chunk_id,
                title=item.title,
                content=item.content,
                document_id=item.document_id,
                version=item.version,
                score=item.score,
                signals=item.retrieval_signals,
            ).model_dump()
            for item in result.evidence
        ]
        errors = state.get("errors", [])
        if not result.answered:
            errors = [*errors, "insufficient_knowledge"]
        return {"evidence": evidence, "errors": errors}

    async def investigate_complex_issue(self, state: SupportState) -> dict:
        if self.investigator is None:
            return {
                "errors": [*state.get("errors", []), "investigation_unavailable"],
                "investigation": self._failed_investigation(state).model_dump(),
            }
        try:
            result = await self.investigator.investigate(
                issue=state["issue"],
                issue_type=state["issue_type"],
                customer_id=state.get("customer_id"),
                ticket_id=state.get("ticket_id"),
                principal=self._principal(state),
            )
        except InvestigationUnavailable:
            result = self._failed_investigation(state)
            return {
                "errors": [*state.get("errors", []), "investigation_failed_safely"],
                "investigation": result.model_dump(),
            }
        return {
            "investigation": result.model_dump(),
            "evidence": [item.model_dump() for item in result.supporting_evidence],
        }

    @staticmethod
    def _failed_investigation(state: SupportState) -> InvestigationResult:
        issue_type = state["issue_type"]
        if issue_type not in {"roaming", "billing", "network"}:
            issue_type = "general"
        return InvestigationResult(
            issue_classification=issue_type,
            investigation_summary="The bounded investigation was unavailable.",
            supporting_evidence=[],
            citations=[],
            tool_calls_performed=[],
            findings=[],
            uncertainties=[
                "No validated multi-source investigation result is available."
            ],
            recommended_next_steps=["Escalate for manual investigation."],
            status="escalate",
        )

    def determine_required_tools(self, state: SupportState) -> dict:
        tools = []
        if state.get("customer_id"):
            tools.append(
                "customer.check_roaming_status"
                if state["issue_type"] == "roaming"
                else "customer.get_customer_plan"
            )
        if state.get("ticket_id"):
            tools.append("ticket.get_ticket_history")
        return {"required_tools": tools}

    def _principal(self, state: SupportState) -> GatewayPrincipal:
        return GatewayPrincipal.model_validate(state["principal"])

    async def check_customer_data(self, state: SupportState) -> dict:
        selected = next(
            (x for x in state.get("required_tools", []) if x.startswith("customer.")),
            None,
        )
        if not selected:
            return {}
        response = await self.gateway.invoke(
            "customer",
            selected.split(".")[1],
            {"customer_id": state["customer_id"]},
            self._principal(state),
        )
        if not response.allowed:
            return {"errors": [*state.get("errors", []), "customer_tool_unavailable"]}
        try:
            contract = (
                ServiceStatusOutput
                if selected.endswith("check_roaming_status")
                else CustomerPlanOutput
            ).model_validate(response.result)
        except ValidationError:
            return {
                "errors": [*state.get("errors", []), "invalid_customer_tool_output"]
            }
        item = ResolutionEvidence(
            source_type="customer",
            source_id=response.request_id,
            title=selected,
            content=contract.model_dump_json(),
            signals=["mcp_gateway"],
        ).model_dump()
        return {"evidence": [*state.get("evidence", []), item]}

    async def check_ticket_history(self, state: SupportState) -> dict:
        if "ticket.get_ticket_history" not in state.get("required_tools", []):
            return {}
        response = await self.gateway.invoke(
            "ticket",
            "get_ticket_history",
            {"ticket_id": state["ticket_id"]},
            self._principal(state),
        )
        if not response.allowed:
            return {"errors": [*state.get("errors", []), "ticket_tool_unavailable"]}
        try:
            contract = TicketHistoryOutput.model_validate(response.result)
        except ValidationError:
            return {"errors": [*state.get("errors", []), "invalid_ticket_tool_output"]}
        item = ResolutionEvidence(
            source_type="ticket",
            source_id=response.request_id,
            title="ticket history",
            content=contract.model_dump_json(),
            signals=["mcp_gateway"],
        ).model_dump()
        return {"evidence": [*state.get("evidence", []), item]}

    def aggregate_evidence(self, state: SupportState) -> dict:
        return {}

    def generate_resolution(self, state: SupportState) -> dict:
        evidence = [
            ResolutionEvidence.model_validate(x) for x in state.get("evidence", [])
        ]
        draft = None
        if state.get("propose_ticket_update") and state.get("ticket_id"):
            draft = TicketDraft(
                operation="update_ticket",
                payload={
                    "ticket_id": state["ticket_id"],
                    "status": "resolved",
                    "priority": None,
                },
            )
        confidence = (
            round(
                sum(
                    (item.score if item.score is not None else 1.0) for item in evidence
                )
                / len(evidence),
                4,
            )
            if evidence
            else 0.0
        )
        investigation = (
            InvestigationResult.model_validate(state["investigation"])
            if state.get("investigation")
            else None
        )
        has_evidence = bool(evidence)
        insufficient = not has_evidence or (
            investigation is not None
            and investigation.status in {"insufficient_evidence", "escalate"}
        )
        resolution = SupportResolution(
            issue_type=state["issue_type"],
            likely_cause=investigation.investigation_summary
            if investigation and has_evidence
            else "Evidence supports the listed guidance."
            if has_evidence
            else "Insufficient evidence to determine a cause.",
            evidence=evidence,
            confidence=0.0 if insufficient else confidence,
            next_steps=investigation.recommended_next_steps
            if investigation
            else ["Follow the cited guidance."]
            if has_evidence
            else ["Escalate for manual investigation."],
            action_required=draft is not None and not insufficient,
            requires_human_approval=draft is not None and not insufficient,
            ticket_draft=draft if not insufficient else None,
            insufficient_evidence=insufficient,
        )
        return {"resolution": resolution.model_dump()}

    def create_approval(self, state: SupportState) -> dict:
        resolution = SupportResolution.model_validate(state["resolution"])
        assert resolution.ticket_draft is not None
        with self.session_factory() as session, session.begin():
            approval = ApprovalService(session).request(
                thread_id=state["thread_id"],
                draft=resolution.ticket_draft,
                ticket_id=state.get("ticket_id"),
            )
            approval_id = approval.id
        return {"approval_id": approval_id, "status": "approval_pending"}

    def human_approval(self, state: SupportState) -> dict:
        decision = interrupt(
            {"approval_id": state["approval_id"], "thread_id": state["thread_id"]}
        )
        return {"approval_decision": decision["decision"]}

    async def execute_action(self, state: SupportState) -> dict:
        resolution = SupportResolution.model_validate(state["resolution"])
        assert resolution.ticket_draft is not None
        execution_id = str(uuid4())
        response = await self.gateway.invoke(
            "ticket",
            resolution.ticket_draft.operation,
            resolution.ticket_draft.payload,
            self._principal(state),
            approval_id=state["approval_id"],
            execution_request_id=execution_id,
        )
        return {
            "execution_result": response.model_dump(),
            "status": "completed"
            if response.allowed and response.result and response.result.get("executed")
            else "failed",
        }

    def audit_log(self, state: SupportState) -> dict:
        return {}

    def final_response(self, state: SupportState) -> dict:
        return {
            "status": "completed"
            if state.get("approval_decision") == "reject"
            else state.get("status", "completed")
        }
