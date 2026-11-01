# Phase 9 command reference

```bash
DATABASE_URL=postgresql+psycopg:///telecom_test_db .venv/bin/alembic upgrade head
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  .venv/bin/pytest backend/tests/test_approvals.py -q
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  .venv/bin/pytest backend/tests/test_knowledge_lifecycle.py \
  backend/tests/test_knowledge_admin_api.py -q
curl -X POST http://127.0.0.1:8000/api/v1/approvals/123/decisions \
  -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \
  -d '{"decision":"approve"}'
```

Validation on 2026-10-25:

```text
Ruff format: 100 files already formatted
Ruff lint: All checks passed
Knowledge promotion migration: c3e7a91d5f20
Backend pytest: 93 passed in 2.61s
Alembic current/heads: c3e7a91d5f20 (head)
Alembic check: No new upgrade operations detected
uv lock --check: resolved 91 packages in 13ms
git diff --check: passed
```
