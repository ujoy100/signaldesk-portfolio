# Phase 7 command reference

```bash
.venv/bin/pytest backend/tests/test_support_workflow.py -q
DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  .venv/bin/python -m backend.scripts.setup_checkpoints
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  .venv/bin/pytest backend/tests/test_checkpoint_postgres.py -q
curl -X POST http://127.0.0.1:8000/api/v1/support/issues \
  -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \
  -d '{"issue":"How do I activate my SIM?"}'
```

Runtime configuration uses `DATABASE_URL`, Qdrant settings, and
`AUTH_JWT_SECRET`. Never commit tokens or secrets. The application assumes the
official checkpoint tables were provisioned before startup and performs no
request-time checkpoint DDL.
