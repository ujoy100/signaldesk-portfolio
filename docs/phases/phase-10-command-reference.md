# Phase 10 command reference

Model runtime configuration in the ignored `.env` or deployment secret store:

```bash
DEEP_AGENT_MODEL='openai:gpt-4.1-mini'
OPENAI_API_KEY='secret-value'
```

Provider credentials must be supplied as environment or deployment secrets.
Leaving `DEEP_AGENT_MODEL` unset keeps complex investigations fail-closed and
does not affect simple deterministic workflows.

```bash
TEST_DATABASE_URL='postgresql+psycopg:///telecom_test_db' \
  uv run pytest backend/tests/test_deep_investigation.py \
  backend/tests/test_support_workflow.py -q
```

The CI tests use an injected deterministic runner. They do not claim a genuine
model invocation.

Genuine opt-in acceptance:

```bash
RUN_PHASE10_MODEL_TEST=yes \
TEST_DATABASE_URL='postgresql+psycopg:///telecom_test_db' \
  uv run pytest backend/tests/test_deep_investigation_openai.py -q
```

Verified result on 2026-10-26: **1 passed in 8.77s**. The test uses only
fictional records and an isolated in-memory Qdrant collection. Do not add `-s`
in automated logs and never echo provider credentials.
