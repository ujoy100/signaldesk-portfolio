# Phase 15 command reference

```bash
cd frontend
npm run lint
npm test
npm run build
npm run test:e2e
npm run dev
```

Focused backend UI-contract tests:

```bash
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
  uv run pytest \
  backend/tests/test_feedback_api.py \
  backend/tests/test_operations_api.py \
  backend/tests/test_support_api.py \
  backend/tests/test_knowledge_admin_api.py -q
```

Set only the public backend origin in `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

No OpenAI, database, JWT-signing, or Qdrant secret belongs in a `VITE_` variable.

Playwright uses installed Google Chrome by default and targets the real Compose origin:

```bash
docker compose up -d --build backend frontend
cd frontend
PLAYWRIGHT_BASE_URL=http://localhost:5173 \
PLAYWRIGHT_BROWSER_CHANNEL=chrome npm run test:e2e
```

The test process obtains short-lived JWTs by executing the development-only CLI inside the backend container. Tokens remain captured in process memory and are never printed by the suite. The CLI rejects production and only permits seeded fictional identities:

```bash
docker compose exec -T backend \
  python -m backend.scripts.issue_development_token support_agent
```

Do not paste this command's output into logs or documentation. Browser artifacts on failure are ignored; sanitized acceptance screenshots are stored under `docs/screenshots/`.
