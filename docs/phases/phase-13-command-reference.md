# Phase 13 command reference

```bash
uv run pytest backend/tests/test_observability_reliability.py -q
```

No unauthenticated monitoring endpoint is exposed. Production deployments may
attach a structured-log or trace exporter to `TelemetryRecorder.events` while
preserving the documented redaction and field allowlist.
