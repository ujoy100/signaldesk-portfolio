"""Phase 13–14 telemetry, privacy, retry, and recovery tests."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.observability import (
    TelemetryRecorder,
    begin_correlation,
    correlation_id_var,
    estimate_model_cost,
)
from backend.app.reliability import RetryExhausted, retry_idempotent
from backend.app.services.knowledge_lifecycle import (
    KnowledgeAuthorizationError,
    KnowledgeLifecycleService,
)


def test_http_correlation_is_returned_and_recorded_without_pii() -> None:
    client = TestClient(create_app(Settings(_env_file=None)))
    response = client.get("/health", headers={"X-Correlation-ID": "trace-123"})
    assert response.headers["X-Correlation-ID"] == "trace-123"

    recorder = TelemetryRecorder()
    token = begin_correlation("trace-safe")
    try:
        recorder.record(
            "test.event",
            customer="jane@example.test",
            access_token="must-not-record",
        )
    finally:
        correlation_id_var.reset(token)
    event = recorder.events[0]
    assert event.correlation_id == "trace-safe"
    assert event.attributes["customer"] == "[REDACTED_EMAIL]"
    assert "access_token" not in event.attributes


def test_versioned_cost_estimate_is_explicit() -> None:
    assert estimate_model_cost("openai:gpt-4.1-mini", 1000, 500) == 0.0012
    assert estimate_model_cost("unknown", 1000, 500) == 0.0


def test_idempotent_retry_uses_bounded_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    operation = Mock(side_effect=[TimeoutError(), TimeoutError(), "ok"])
    monkeypatch.setattr("backend.app.reliability.time.sleep", lambda _: None)
    assert retry_idempotent(operation, attempts=3) == "ok"
    assert operation.call_count == 3


def test_retry_exhaustion_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backend.app.reliability.time.sleep", lambda _: None)
    with pytest.raises(RetryExhausted, match="exhausted"):
        retry_idempotent(Mock(side_effect=OSError()), attempts=2)


def test_reconciliation_is_fail_closed_for_non_admin() -> None:
    service = KnowledgeLifecycleService(
        Mock(), Mock(), Mock(), "test", approval_execution_enabled=True
    )
    with pytest.raises(KnowledgeAuthorizationError, match="Admin"):
        service.reconcile_pending(actor_id=1, role="supervisor")
