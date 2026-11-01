# Phase 6 Command Reference

```bash
uv run pytest backend/tests/test_auth.py backend/tests/test_mcp_gateway.py -q
```

External callers must supply a valid HS256 bearer token whose audience matches
`AUTH_JWT_AUDIENCE`. If `AUTH_JWT_SECRET` is absent, authentication fails closed.
Secrets and tokens must never be passed as MCP tool arguments or written to
audit details.
