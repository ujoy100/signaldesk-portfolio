"""Strict contracts at workflow, API, and approval boundaries."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ResolutionEvidence(StrictModel):
    source_type: Literal["knowledge", "customer", "ticket", "system"]
    source_id: str
    title: str
    content: str
    document_id: str | None = None
    version: str | None = None
    score: float | None = Field(default=None, ge=0, le=1)
    signals: list[str] = Field(default_factory=list)


class InvestigationToolCall(StrictModel):
    tool: Literal[
        "knowledge.search_knowledge_base",
        "knowledge.get_policy",
        "customer.get_customer_plan",
        "customer.check_roaming_status",
        "customer.get_active_services",
        "ticket.get_ticket",
        "ticket.get_ticket_history",
    ]
    request_id: str
    purpose: str


class InvestigationFinding(StrictModel):
    finding: str
    evidence_ids: list[str] = Field(default_factory=list)


class InvestigationResult(StrictModel):
    issue_classification: Literal["roaming", "billing", "network", "general"]
    investigation_summary: str
    supporting_evidence: list[ResolutionEvidence]
    citations: list[str]
    tool_calls_performed: list[InvestigationToolCall]
    findings: list[InvestigationFinding]
    uncertainties: list[str]
    recommended_next_steps: list[str]
    status: Literal["completed", "insufficient_evidence", "escalate"]

    @model_validator(mode="after")
    def citations_must_reference_evidence(self) -> "InvestigationResult":
        evidence_ids = {item.source_id for item in self.supporting_evidence}
        if not set(self.citations).issubset(evidence_ids):
            raise ValueError("citations must reference supporting evidence")
        return self


class TicketDraft(StrictModel):
    operation: Literal["update_ticket", "create_ticket"]
    payload: dict


class SupportResolution(StrictModel):
    issue_type: str
    likely_cause: str
    evidence: list[ResolutionEvidence]
    confidence: float = Field(ge=0, le=1)
    next_steps: list[str]
    action_required: bool
    requires_human_approval: bool
    ticket_draft: TicketDraft | None = None
    insufficient_evidence: bool = False

    @model_validator(mode="after")
    def validate_action_consistency(self) -> "SupportResolution":
        if self.action_required != (self.ticket_draft is not None):
            raise ValueError("action_required must match ticket_draft presence")
        if self.requires_human_approval != self.action_required:
            raise ValueError("all controlled actions require human approval")
        if self.insufficient_evidence and self.confidence != 0:
            raise ValueError("insufficient evidence must have zero confidence")
        return self


class SupportIssueRequest(StrictModel):
    issue: str = Field(min_length=3, max_length=2000)
    thread_id: str | None = Field(default=None, min_length=8, max_length=100)
    customer_id: int | None = Field(default=None, gt=0)
    ticket_id: int | None = Field(default=None, gt=0)
    propose_ticket_update: bool = False


class WorkflowResponse(StrictModel):
    thread_id: str
    status: Literal["completed", "approval_pending", "failed"]
    resolution: SupportResolution | None = None
    approval_id: int | None = None
    error: str | None = None
    workflow_mode: Literal["deterministic", "deep_agent"] | None = None


class ApprovalDecisionRequest(StrictModel):
    decision: Literal["approve", "edit", "reject"]
    edited_action: TicketDraft | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_edit(self) -> "ApprovalDecisionRequest":
        if (self.decision == "edit") != (self.edited_action is not None):
            raise ValueError("edited_action is required only for edit decisions")
        return self


class ApprovalResponse(StrictModel):
    approval_id: int
    thread_id: str
    status: Literal["pending", "approved", "rejected", "expired", "executed"]
    action_type: str
    action_payload: dict
    expires_at: str | None
