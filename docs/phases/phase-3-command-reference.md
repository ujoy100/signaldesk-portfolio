# Phase 3 Command Reference

## Retrieval tests

```bash
uv run pytest backend/tests/test_retrieval.py -q
```

Tests cover every strategy, metadata filters, access-role filtering, evidence
fields, explicit no-answer behavior, and benchmark thresholds.

## Benchmark

```bash
uv run python -m backend.app.knowledge.benchmark
```

The command uses isolated in-memory Qdrant and prints JSON metrics for all four
strategies. It does not call an LLM or external API.

## Full backend validation

```bash
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run pytest backend/tests -q
uv run ruff check backend
uv run ruff format --check backend
```

The expanded retrieval regression file passes 15 tests, including all four
strategies returning no-answer for the unsupported Mars service question.
Run the full suite for the current repository-wide total.
