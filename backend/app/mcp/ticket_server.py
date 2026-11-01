"""Ticket MCP server with fail-closed controlled writes."""

from collections.abc import Callable

from mcp.server import MCPServer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.mcp.contracts import (
    ControlledWriteOutput,
    TicketDraftOutput,
    TicketHistoryOutput,
    TicketOutput,
)
from backend.app.models.ticket import Ticket
from backend.app.models.ticket_event import TicketEvent
from backend.app.services.approvals import ApprovalError, ApprovalService


def create_ticket_server(
    session_factory: Callable[[], Session], *, controlled_writes_enabled: bool = False
) -> MCPServer:
    server = MCPServer("telecom-ticket", version="1.0.0")

    @server.tool(structured_output=True)
    def get_ticket(ticket_id: int) -> TicketOutput:
        """Get one support ticket."""

        with session_factory() as session:
            ticket = session.get(Ticket, ticket_id)
            if ticket is None:
                raise ValueError("ticket_not_found")
            return TicketOutput(
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                customer_id=ticket.customer_id,
                subject=ticket.subject,
                description=ticket.description,
                status=ticket.status,
                priority=ticket.priority,
            )

    @server.tool(structured_output=True)
    def get_ticket_history(ticket_id: int) -> TicketHistoryOutput:
        """Get ordered ticket history."""

        with session_factory() as session:
            if session.get(Ticket, ticket_id) is None:
                raise ValueError("ticket_not_found")
            events = session.scalars(
                select(TicketEvent)
                .where(TicketEvent.ticket_id == ticket_id)
                .order_by(TicketEvent.created_at, TicketEvent.id)
            ).all()
            return TicketHistoryOutput(
                ticket_id=ticket_id,
                events=[
                    {
                        "id": event.id,
                        "event_type": event.event_type,
                        "description": event.description,
                        "actor_type": event.actor_type,
                        "created_at": event.created_at.isoformat(),
                    }
                    for event in events
                ],
            )

    @server.tool(structured_output=True)
    def draft_ticket_update(
        ticket_id: int,
        status: str | None = None,
        priority: str | None = None,
        note: str | None = None,
    ) -> TicketDraftOutput:
        """Draft, but never execute, a controlled ticket update."""

        with session_factory() as session:
            if session.get(Ticket, ticket_id) is None:
                raise ValueError("ticket_not_found")
        return TicketDraftOutput(
            operation="update_ticket",
            payload={
                "ticket_id": ticket_id,
                "status": status,
                "priority": priority,
                "note": note,
            },
        )

    @server.tool(structured_output=True)
    def update_ticket(
        ticket_id: int,
        status: str | None = None,
        priority: str | None = None,
        approval_id: int | None = None,
        execution_request_id: str | None = None,
    ) -> ControlledWriteOutput:
        """Execute an exact approved update atomically and once."""

        if (
            not controlled_writes_enabled
            or approval_id is None
            or not execution_request_id
        ):
            return ControlledWriteOutput(
                message="Ticket update denied: verified approval required."
            )
        payload = {"ticket_id": ticket_id, "status": status, "priority": priority}
        with session_factory() as session, session.begin():
            service = ApprovalService(session)
            try:
                approval = service.verify(
                    approval_id=approval_id,
                    operation="update_ticket",
                    payload=payload,
                    execution_request_id=execution_request_id,
                )
            except ApprovalError as error:
                return ControlledWriteOutput(
                    code="approval_invalid", message=str(error)
                )
            ticket = session.get(Ticket, ticket_id)
            if ticket is None:
                return ControlledWriteOutput(
                    code="ticket_not_found", message="Ticket not found"
                )
            if status is not None:
                ticket.status = status
            if priority is not None:
                ticket.priority = priority
            event = TicketEvent(
                ticket_id=ticket.id,
                event_type="approved_update",
                description="Approved ticket fields updated",
                actor_type="supervisor",
            )
            session.add(event)
            session.flush()
            service.consume(approval, execution_request_id)
            return ControlledWriteOutput(
                executed=True,
                code="executed",
                message="Ticket updated",
                ticket_id=ticket.id,
                event_id=event.id,
            )

    @server.tool(structured_output=True)
    def create_ticket(
        customer_id: int,
        subject: str,
        description: str,
        priority: str = "medium",
        approval_id: int | None = None,
        execution_request_id: str | None = None,
    ) -> ControlledWriteOutput:
        """Create one ticket from an exact approved payload, atomically and once."""

        if (
            not controlled_writes_enabled
            or approval_id is None
            or not execution_request_id
        ):
            return ControlledWriteOutput(
                message="Ticket creation denied: verified approval required."
            )
        payload = {
            "customer_id": customer_id,
            "subject": subject,
            "description": description,
            "priority": priority,
        }
        with session_factory() as session, session.begin():
            service = ApprovalService(session)
            try:
                approval = service.verify(
                    approval_id=approval_id,
                    operation="create_ticket",
                    payload=payload,
                    execution_request_id=execution_request_id,
                )
            except ApprovalError as error:
                return ControlledWriteOutput(
                    code="approval_invalid", message=str(error)
                )
            ticket = Ticket(
                ticket_number=f"AI-{execution_request_id.replace('-', '')[:20]}",
                customer_id=customer_id,
                subject=subject,
                description=description,
                priority=priority,
                status="open",
            )
            session.add(ticket)
            session.flush()
            event = TicketEvent(
                ticket_id=ticket.id,
                event_type="approved_creation",
                description="Ticket created after human approval",
                actor_type="supervisor",
            )
            session.add(event)
            session.flush()
            service.consume(approval, execution_request_id)
            return ControlledWriteOutput(
                executed=True,
                code="executed",
                message="Ticket created",
                ticket_id=ticket.id,
                event_id=event.id,
            )

    return server
