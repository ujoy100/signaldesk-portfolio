# Phase 5 Command Reference

```bash
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  uv run pytest backend/tests/test_mcp_servers.py -q
```

The tests cover discovery, knowledge/customer/ticket invocation, structured
outputs, invalid arguments, missing records, and controlled-write denial.
