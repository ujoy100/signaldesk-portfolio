"""Pydantic contracts for knowledge administration."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.knowledge.models import KnowledgeMetadata


class KnowledgeUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    media_type: Literal["text/plain", "text/markdown", "application/json"]
    content: str = Field(min_length=20, max_length=1_000_000)
    metadata: KnowledgeMetadata


class KnowledgeVersionResponse(BaseModel):
    document_id: int
    stable_id: str
    version_id: int
    version: str
    checksum: str
    status: str
    unchanged: bool = False


class KnowledgePromotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: int = Field(gt=0)
    execution_request_id: str = Field(min_length=8, max_length=100)


class KnowledgePromotionApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_id: str = Field(min_length=8, max_length=100)


class KnowledgeDeactivationRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
