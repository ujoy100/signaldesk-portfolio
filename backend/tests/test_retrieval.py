"""Hybrid retrieval, filtering, evidence, and no-answer tests."""

import pytest
from qdrant_client import QdrantClient

from backend.app.knowledge.benchmark import STRATEGIES, run_benchmark
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.models import RetrievalFilters
from backend.app.knowledge.retrieval import TelecomRetriever


@pytest.fixture
def retriever() -> TelecomRetriever:
    client = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(256)
    collection = "test_retrieval"
    ingest_knowledge(client, collection_name=collection, embeddings=embeddings)
    return TelecomRetriever(client, collection, embeddings, minimum_score=0.03)


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_retrieval_strategies_find_policy_code(
    retriever: TelecomRetriever, strategy: str
) -> None:
    result = retriever.retrieve(
        "Explain ROAM-PASS-24",
        strategy=strategy,
        limit=3,
    )

    assert result.answered
    assert result.evidence[0].document_id == "policy-roaming-001"
    assert result.evidence[0].source.startswith("fictional://")
    assert result.evidence[0].section
    assert result.evidence[0].version == "2.0"


def test_metadata_filter_limits_service(retriever: TelecomRetriever) -> None:
    result = retriever.retrieve(
        "invoice dispute",
        filters=RetrievalFilters(service="billing"),
    )

    assert result.answered
    assert all(item.service == "billing" for item in result.evidence)


def test_mobile_data_troubleshooting_question_remains_grounded(
    retriever: TelecomRetriever,
) -> None:
    result = retriever.retrieve(
        "My mobile internet is not working even though I have an active data plan. "
        "What should I check?",
        filters=RetrievalFilters(
            access_roles=["public", "support_agent"], active_only=True
        ),
    )

    assert result.answered
    assert result.evidence[0].document_id == "guide-network-001"
    assert result.evidence[0].score >= 0.8


def test_public_access_excludes_internal_runbook(retriever: TelecomRetriever) -> None:
    public = retriever.retrieve("CREDIT-HITL-50", strategy="keyword")
    agent = retriever.retrieve(
        "CREDIT-HITL-50",
        strategy="keyword",
        filters=RetrievalFilters(access_roles=["support_agent"]),
    )

    assert not public.answered
    assert agent.answered
    assert agent.evidence[0].document_id == "runbook-credit-001"


def test_irrelevant_question_returns_explicit_no_answer(
    retriever: TelecomRetriever,
) -> None:
    result = retriever.retrieve("lunar handset recycling color")

    assert not result.answered
    assert result.evidence == []
    assert result.reason is not None


def test_inactive_version_is_never_returned(retriever: TelecomRetriever) -> None:
    result = retriever.retrieve("ROAM-PASS-OLD automatic overages", limit=10)

    assert all(
        item.document_id != "policy-roaming-legacy-001" for item in result.evidence
    )


def test_retrieval_benchmark_has_measurable_metrics(
    retriever: TelecomRetriever,
) -> None:
    results = run_benchmark(retriever)

    assert set(results) == set(STRATEGIES)
    assert all(result["cases"] == 14 for result in results.values())
    assert results["hybrid_reranked"]["recall_at_3"] >= 0.8
    assert results["hybrid_reranked"]["no_answer_accuracy"] == 1.0


@pytest.mark.parametrize(
    "query",
    [
        "How do I activate my SIM card?",
        "I got a new mobile card. How can I start using it?",
    ],
)
def test_activation_paraphrases_rerank_to_activation_guide(
    retriever: TelecomRetriever, query: str
) -> None:
    result = retriever.retrieve(query, strategy="hybrid_reranked", limit=3)

    assert result.answered
    assert result.evidence[0].document_id == "guide-sim-activation-001"


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_unsupported_mars_service_question_returns_no_answer(
    retriever: TelecomRetriever, strategy: str
) -> None:
    result = retriever.retrieve(
        "Does my telecom provider offer mobile service on Mars?",
        strategy=strategy,
    )

    assert not result.answered
    assert result.evidence == []
