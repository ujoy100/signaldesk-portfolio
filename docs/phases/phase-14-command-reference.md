# Phase 14 command reference

```bash
TEST_DATABASE_URL='postgresql+psycopg:///telecom_test_db' \
  uv run pytest backend/tests/test_observability_reliability.py \
  backend/tests/test_knowledge_lifecycle.py \
  backend/tests/test_checkpoint_postgres.py \
  backend/tests/test_approvals.py backend/tests/test_mcp_gateway.py -q
```

Reconciliation is an application service operation, not a database repair
script. It must run with an authenticated active Admin and normal approval,
Gateway and Qdrant configuration.
