"""Privacy-safe correlation, timings, counters, and cost estimates."""

import contextvars
import json
import logging
from dataclasses import asdict, dataclass, field
from time import perf_counter
from uuid import uuid4

from backend.app.core.security import redact_pii

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)

MODEL_PRICING_USD_PER_MILLION = {
    "openai:gpt-4.1-mini": {"input": 0.40, "output": 1.60, "version": "2026-10-26"}
}


@dataclass(frozen=True)
class TelemetryEvent:
    name: str
    correlation_id: str
    duration_ms: float | None = None
    outcome: str = "success"
    attributes: dict[str, str | int | float | bool | None] = field(default_factory=dict)


class TelemetryRecorder:
    """Small exporter-neutral recorder; production exporters can consume events."""

    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []
        self.logger = logging.getLogger("telecom.telemetry")

    def record(
        self,
        name: str,
        *,
        started: float | None = None,
        outcome: str = "success",
        **attributes: str | float | bool | None,
    ) -> None:
        safe = {
            key: redact_pii(str(value)) if isinstance(value, str) else value
            for key, value in attributes.items()
            if "token" not in key.lower() and "credential" not in key.lower()
        }
        event = TelemetryEvent(
            name=name,
            correlation_id=correlation_id_var.get() or "uncorrelated",
            duration_ms=round((perf_counter() - started) * 1000, 3)
            if started is not None
            else None,
            outcome=outcome,
            attributes=safe,
        )
        self.events.append(event)
        self.logger.info(json.dumps(asdict(event), sort_keys=True))


def begin_correlation(value: str | None = None) -> contextvars.Token[str]:
    return correlation_id_var.set(value or str(uuid4()))


def estimate_model_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING_USD_PER_MILLION.get(model)
    if pricing is None:
        return 0.0
    return round(
        (
            input_tokens * float(pricing["input"])
            + output_tokens * float(pricing["output"])
        )
        / 1_000_000,
        8,
    )


telemetry = TelemetryRecorder()
