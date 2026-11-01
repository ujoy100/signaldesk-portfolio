# Phase 4 Command Reference

```bash
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic upgrade head
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  uv run pytest backend/tests/test_knowledge_lifecycle.py \
  backend/tests/test_knowledge_admin_api.py -q
```

Head `61f42e7c9a10` and schema consistency were verified. Final repository
validation passed 66 tests; rerun the command to obtain the current count after
future changes.

Knowledge administration requires `AUTH_JWT_SECRET` outside Git. Promotion
remains unavailable until Phase 9; no command should bypass that gate.
