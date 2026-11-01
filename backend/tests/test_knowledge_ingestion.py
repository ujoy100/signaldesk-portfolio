"""Qdrant ingestion tests using isolated in-memory storage."""

import pytest
from qdrant_client import QdrantClient

from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge


@pytest.fixture
def knowledge_store() -> tuple[QdrantClient, DeterministicTelecomEmbeddings, str]:
    client = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    collection = "test_telecom_knowledge"
    return client, embeddings, collection


def test_ingestion_is_repeatable_with_stable_ids(knowledge_store) -> None:
    client, embeddings, collection = knowledge_store

    first = ingest_knowledge(client, collection_name=collection, embeddings=embeddings)
    first_count = client.count(collection, exact=True).count
    second = ingest_knowledge(client, collection_name=collection, embeddings=embeddings)

    assert first == {"documents": 8, "chunks": 8}
    assert second == first
    assert client.count(collection, exact=True).count == first_count == 8


def test_ingestion_payload_contains_required_metadata(knowledge_store) -> None:
    client, embeddings, collection = knowledge_store
    ingest_knowledge(client, collection_name=collection, embeddings=embeddings)

    records, _ = client.scroll(collection, limit=10, with_payload=True)

    required = {
        "document_id",
        "source",
        "service",
        "category",
        "version",
        "active",
        "access_roles",
        "page",
        "section",
        "title",
        "chunk_index",
        "content",
    }
    assert records
    assert all(required <= set(record.payload or {}) for record in records)
