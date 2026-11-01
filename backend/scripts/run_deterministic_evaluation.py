"""Run the reproducible, provider-free Phase 12 threshold gate."""

import json

from qdrant_client import QdrantClient

from backend.app.evaluation.runner import run_deterministic_evaluation
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.retrieval import TelecomRetriever


def main() -> None:
    client = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    collection = "deterministic_ci_evaluation"
    ingest_knowledge(client, collection_name=collection, embeddings=embeddings)
    report = run_deterministic_evaluation(
        TelecomRetriever(client, collection, embeddings, minimum_score=0.03)
    )
    print(json.dumps(report.__dict__, indent=2, sort_keys=True))
    if not report.passed:
        raise SystemExit("Deterministic evaluation thresholds failed")


if __name__ == "__main__":
    main()
