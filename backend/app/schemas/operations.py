"""Strict read-only operational API contracts."""

from pydantic import BaseModel, ConfigDict, Field


class OperationalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SessionInfo(OperationalModel):
    actor_id: int
    role: str
    display_name: str


class EvaluationRunView(OperationalModel):
    id: int
    evaluation_type: str
    dataset_name: str
    model_name: str | None
    status: str
    configuration: str | None


class ApprovalListItem(OperationalModel):
    id: int
    thread_id: str
    status: str
    action_type: str
    action_payload: dict
    consumed: bool
    action_description: str
    expires_at: str | None
    ticket_number: str | None = None
    current_ticket_status: str | None = None
    current_ticket_priority: str | None = None


class KnowledgeVersionListItem(OperationalModel):
    id: int
    document_id: int
    version: str
    status: str
    promotion_state: str
    promotion_error: str | None


class FeedbackCreate(OperationalModel):
    thread_id: str = Field(min_length=8, max_length=100)
    customer_id: int | None = Field(default=None, gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


class FeedbackView(OperationalModel):
    id: int
    thread_id: str
    rating: int
    comment: str | None
