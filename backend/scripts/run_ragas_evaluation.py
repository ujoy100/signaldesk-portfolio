"""Run the explicitly opted-in, bounded genuine RAGAS evaluation."""

import json
import os

from qdrant_client import QdrantClient

from backend.app.core.config import Settings
from backend.app.evaluation.ragas_runner import run_bounded_ragas
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.retrieval import TelecomRetriever


def main() -> None:
    if os.getenv("RUN_REAL_RAGAS") != "yes":
        raise SystemExit("Set RUN_REAL_RAGAS=yes to authorize bounded paid evaluation")
    settings = Settings()
    client = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    collection = "bounded_ragas_fictional"
    ingest_knowledge(client, collection_name=collection, embeddings=embeddings)
    report = run_bounded_ragas(
        TelecomRetriever(client, collection, embeddings, minimum_score=0.03),
        settings,
        max_cases=2,
    )
    print(json.dumps(report.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
