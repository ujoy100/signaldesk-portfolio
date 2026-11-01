"""Deterministic retrieval benchmark for the fictional telecom corpus."""

import json
from dataclasses import dataclass

from qdrant_client import QdrantClient

from backend.app.core.config import get_settings
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.models import RetrievalFilters
from backend.app.knowledge.retrieval import TelecomRetriever

STRATEGIES = ("vector", "keyword", "hybrid", "hybrid_reranked")


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    relevant_document: str | None
    access_roles: tuple[str, ...] = ("public",)


CASES = (
    BenchmarkCase("How do I recover a locked SIM PUK?", "faq-sim-puk-001"),
    BenchmarkCase("What does policy ROAM-PASS-24 include?", "policy-roaming-001"),
    BenchmarkCase("I want to dispute an invoice charge", "policy-billing-001"),
    BenchmarkCase("mobile internet has no signal", "guide-network-001"),
    BenchmarkCase("How do I activate my ICCID?", "guide-sim-activation-001"),
    BenchmarkCase("How do I activate my SIM card?", "guide-sim-activation-001"),
    BenchmarkCase(
        "I got a new mobile card. How can I start using it?",
        "guide-sim-activation-001",
    ),
    BenchmarkCase(
        "My card is locked after bad security PIN attempts", "faq-sim-puk-001"
    ),
    BenchmarkCase("Will travel data stop after the allowance?", "policy-roaming-001"),
    BenchmarkCase(
        "What requires supervisor approval for a large credit?",
        "runbook-credit-001",
        ("support_agent",),
    ),
    BenchmarkCase("What is the lunar handset recycling color?", None),
    BenchmarkCase("Give me policy code UNKNOWN-SPACE-99", None),
    BenchmarkCase("Does my telecom provider offer mobile service on Mars?", None),
    BenchmarkCase("Can I use the network in an underwater city on Neptune?", None),
)


def run_benchmark(retriever: TelecomRetriever, *, limit: int = 3) -> dict:
    """Compare recall@k, MRR, and no-answer accuracy across strategies."""

    results = {}
    positive_count = sum(case.relevant_document is not None for case in CASES)
    negative_count = len(CASES) - positive_count
    for strategy in STRATEGIES:
        hits = 0
        reciprocal_rank = 0.0
        correct_no_answer = 0
        for case in CASES:
            response = retriever.retrieve(
                case.query,
                strategy=strategy,
                filters=RetrievalFilters(access_roles=list(case.access_roles)),
                limit=limit,
            )
            document_ids = [item.document_id for item in response.evidence]
            if case.relevant_document is None:
                correct_no_answer += int(not response.answered)
                continue
            if case.relevant_document in document_ids:
                hits += 1
                reciprocal_rank += 1.0 / (
                    document_ids.index(case.relevant_document) + 1
                )
        results[strategy] = {
            "recall_at_3": round(hits / positive_count, 4),
            "mean_reciprocal_rank": round(reciprocal_rank / positive_count, 4),
            "no_answer_accuracy": round(correct_no_answer / negative_count, 4),
            "cases": len(CASES),
        }
    return results


def main() -> None:
    settings = get_settings()
    client = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(settings.embedding_dimensions)
    ingest_knowledge(
        client,
        collection_name=settings.qdrant_collection,
        embeddings=embeddings,
    )
    retriever = TelecomRetriever(
        client,
        settings.qdrant_collection,
        embeddings,
        minimum_score=settings.retrieval_min_score,
    )
    print(json.dumps(run_benchmark(retriever), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
