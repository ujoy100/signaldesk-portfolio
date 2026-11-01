"""Repeatable Qdrant ingestion for fictional telecom knowledge."""

import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from backend.app.core.config import get_settings
from backend.app.knowledge.client import create_qdrant_client
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.loader import DEFAULT_KNOWLEDGE_PATH, load_knowledge_chunks


def stable_chunk_id(document: Document) -> str:
    """Generate the same Qdrant UUID for the same versioned chunk."""

    metadata = document.metadata
    content_hash = hashlib.sha256(document.page_content.encode("utf-8")).hexdigest()
    identity = ":".join(
        (
            metadata["document_id"],
            metadata["version"],
            str(metadata["chunk_index"]),
            content_hash,
        )
    )
    return str(uuid5(NAMESPACE_URL, identity))


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    dimensions: int,
) -> None:
    """Create a missing collection; never recreate an existing collection."""

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimensions,
                distance=models.Distance.COSINE,
            ),
        )
        return

    collection = client.get_collection(collection_name)
    vector_config = collection.config.params.vectors
    existing_size = getattr(vector_config, "size", None)
    if existing_size != dimensions:
        raise RuntimeError(
            f"Collection {collection_name!r} has vector size {existing_size}; "
            f"expected {dimensions}. Refusing to recreate it."
        )


def ingest_knowledge(
    client: QdrantClient,
    *,
    collection_name: str,
    embeddings: DeterministicTelecomEmbeddings,
    knowledge_path: Path = DEFAULT_KNOWLEDGE_PATH,
) -> dict[str, int]:
    """Validate, chunk, embed, and upsert the fictional corpus."""

    chunks = load_knowledge_chunks(knowledge_path)
    ensure_collection(client, collection_name, embeddings.dimensions)
    vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
    points = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        payload = {**chunk.metadata, "content": chunk.page_content}
        points.append(
            models.PointStruct(
                id=stable_chunk_id(chunk),
                vector=vector,
                payload=payload,
            )
        )
    client.upsert(collection_name=collection_name, points=points, wait=True)
    return {
        "documents": len({chunk.metadata["document_id"] for chunk in chunks}),
        "chunks": len(chunks),
    }


def main() -> None:
    settings = get_settings()
    client = create_qdrant_client(settings)
    embeddings = DeterministicTelecomEmbeddings(settings.embedding_dimensions)
    result = ingest_knowledge(
        client,
        collection_name=settings.qdrant_collection,
        embeddings=embeddings,
    )
    print(
        f"Fictional knowledge indexed: documents={result['documents']}, "
        f"chunks={result['chunks']}"
    )


if __name__ == "__main__":
    main()
