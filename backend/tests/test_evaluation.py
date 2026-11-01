"""Phase 12 deterministic evaluation tests."""

from qdrant_client import QdrantClient
from sqlalchemy import Connection, func, select
from sqlalchemy.orm import Session

from backend.app.evaluation.dataset import DATASET_VERSION, load_dataset
from backend.app.evaluation.ragas_runner import _load_ragas
from backend.app.evaluation.runner import (
    THRESHOLDS,
    persist_report,
    run_deterministic_evaluation,
)
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.models.evaluation_score import EvaluationScore


def _retriever() -> TelecomRetriever:
    client = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    ingest_knowledge(client, collection_name="evaluation", embeddings=embeddings)
    return TelecomRetriever(client, "evaluation", embeddings, minimum_score=0.03)


def test_versioned_dataset_has_required_coverage() -> None:
    cases = load_dataset()
    assert DATASET_VERSION == "1.0.0"
    assert len(cases) == 40
    assert {case.category for case in cases} == {
        "sim",
        "roaming",
        "billing",
        "plan",
        "network",
        "ticket",
        "unsupported",
        "restricted",
        "security",
        "approval",
    }


def test_installed_ragas_metrics_load_with_current_langchain() -> None:
    api = _load_ragas()
    assert api["Faithfulness"].__module__.startswith("ragas.metrics")
    assert api["ResponseRelevancy"].__module__.startswith("ragas.metrics")


def test_deterministic_evaluation_is_reproducible() -> None:
    retriever = _retriever()
    first = run_deterministic_evaluation(retriever)
    second = run_deterministic_evaluation(retriever)
    assert first == second
    assert first.cases == 40
    assert all(first.metrics[name] >= value for name, value in THRESHOLDS.items())


def test_evaluation_report_persists_versions_and_scores(
    test_db_connection: Connection,
) -> None:
    report = run_deterministic_evaluation(_retriever())
    with Session(
        bind=test_db_connection, join_transaction_mode="create_savepoint"
    ) as session:
        run_id = persist_report(
            session,
            report,
            model="deterministic",
            retriever_version="hybrid-reranked-v1",
            prompt_version="structured-resolution-v1",
            knowledge_version="fictional-corpus-v1",
        )
        session.commit()
        count = session.scalar(
            select(func.count())
            .select_from(EvaluationScore)
            .where(EvaluationScore.evaluation_run_id == run_id)
        )
    assert count == len(report.metrics)
