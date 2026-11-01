"""Typed contracts for telecom knowledge and retrieval evidence."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeMetadata(BaseModel):
    """Required metadata stored with each Qdrant knowledge chunk."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]+$")
    source: str
    service: str
    category: str
    version: str
    active: bool = True
    access_roles: list[str] = Field(default_factory=lambda: ["public"])
    page: int | None = Field(default=None, ge=1)
    section: str
    title: str


class KnowledgeRecord(BaseModel):
    """One source document before LangChain chunking."""

    metadata: KnowledgeMetadata
    content: str = Field(min_length=20)


class Evidence(BaseModel):
    """Auditable evidence returned by the retrieval layer."""

    chunk_id: str
    document_id: str
    source: str
    title: str
    section: str
    page: int | None
    version: str
    service: str
    category: str
    content: str
    score: float
    retrieval_signals: list[str]


class RetrievalResponse(BaseModel):
    """Retrieval result with explicit insufficient-evidence behavior."""

    answered: bool
    strategy: Literal["vector", "keyword", "hybrid", "hybrid_reranked"]
    evidence: list[Evidence]
    reason: str | None = None


class RetrievalFilters(BaseModel):
    """Metadata and access constraints applied before retrieval."""

    service: str | None = None
    category: str | None = None
    version: str | None = None
    access_roles: list[str] = Field(default_factory=lambda: ["public"])
    active_only: bool = True
