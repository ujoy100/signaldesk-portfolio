# Phase 11 command reference

```bash
TEST_DATABASE_URL='postgresql+psycopg:///telecom_test_db' \
  uv run pytest backend/tests/test_auth.py \
  backend/tests/test_security_hardening.py \
  backend/tests/test_mcp_gateway.py \
  backend/tests/test_approvals.py \
  backend/tests/test_knowledge_admin_api.py \
  backend/tests/test_support_api.py -q
```

Full acceptance checks use the commands recorded in `docs/phase-tracker.md`.
All database writes must target `telecom_test_db`.
