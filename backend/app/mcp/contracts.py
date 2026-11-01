"""Typed MCP tool contracts."""

from pydantic import BaseModel, ConfigDict, Field


class StrictToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ToolError(StrictToolModel):
    code: str
    message: str
    retryable: bool = False


class KnowledgeSearchOutput(StrictToolModel):
    answered: bool
    evidence: list[dict]
    reason: str | None = None


class PolicyOutput(StrictToolModel):
    found: bool
    policy_code: str
    evidence: list[dict]


class SourceDetailsOutput(StrictToolModel):
    found: bool
    document_id: str
    source: str | None = None
    title: str | None = None
    version: str | None = None
    active: bool | None = None


class KnowledgePromotionOutput(StrictToolModel):
    executed: bool
    version_id: int
    status: str
    promotion_state: str


class CustomerProfileOutput(StrictToolModel):
    customer_id: int
    customer_number: str
    full_name: str
    email: str | None


class CustomerPlanOutput(StrictToolModel):
    customer_id: int
    plan_code: str
    plan_name: str
    status: str


class ServiceStatusOutput(StrictToolModel):
    customer_id: int
    service: str
    status: str
    basis: str


class ActiveServicesOutput(StrictToolModel):
    customer_id: int
    services: list[dict]


class TicketOutput(StrictToolModel):
    ticket_id: int
    ticket_number: str
    customer_id: int
    subject: str
    description: str
    status: str
    priority: str


class TicketHistoryOutput(StrictToolModel):
    ticket_id: int
    events: list[dict]


class TicketDraftOutput(StrictToolModel):
    operation: str
    payload: dict
    requires_approval: bool = True
    executable: bool = False


class ControlledWriteOutput(StrictToolModel):
    executed: bool = False
    code: str = "approval_required"
    message: str = "Controlled ticket writes require verified human approval."
    ticket_id: int | None = None
    event_id: int | None = None


class GatewayPrincipal(StrictToolModel):
    subject: str = Field(min_length=1)
    role: str
    actor_id: int | None = None


class GatewayResponse(StrictToolModel):
    request_id: str
    namespace: str
    tool: str
    allowed: bool
    result: dict | None = None
    error: ToolError | None = None
