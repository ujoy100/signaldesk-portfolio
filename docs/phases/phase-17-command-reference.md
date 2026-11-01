# Phase 17 command reference

## Local workflow validation

```bash
python -c 'import pathlib, yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path(".github").rglob("*.yml")]; print("YAML parsed")'
docker run --rm -v "$PWD:/repo" rhysd/actionlint:1.7.7
```

## Reproduce default quality gates

```bash
uv sync --frozen
uv run ruff check backend
uv run ruff format --check backend
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run pytest backend/tests -q
uv run python -m backend.scripts.run_deterministic_evaluation
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic current
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic heads
DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run alembic check
uv lock --check

npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

Compose/browser checks require the ignored development secrets described in `secrets/README.md`:

```bash
docker compose config --quiet
docker compose up -d --build --wait
docker compose --profile tools run --rm seed
npm --prefix frontend run test:e2e
docker compose ps
```

Do not run `docker compose down -v`. Do not run the paid workflow by default.

## Reproduce the first hosted backend failure environment

```bash
AUTH_JWT_SECRET=ci-only-jwt-secret-with-sufficient-entropy \
AUTH_JWT_AUDIENCE=telecom-ci \
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db \
uv run pytest \
  backend/tests/test_auth.py \
  backend/tests/test_database_urls.py \
  backend/tests/test_checkpoint_postgres.py \
  backend/tests/test_security_hardening.py -q
```

This uses the isolated test database. Never substitute a development or
production database. SQLAlchemy URL display strings redact passwords; checkpoint
connections must use `backend.app.db.urls.postgres_checkpoint_url` rather than
`str(engine.url)`.

CI provisions both independently managed schemas against the same isolated URL:

```bash
DATABASE_URL=postgresql+psycopg://.../telecom_test_db \
  uv run alembic upgrade head
DATABASE_URL=postgresql+psycopg://.../telecom_test_db \
  uv run python -m backend.scripts.setup_checkpoints
```

The second command uses official, idempotent `PostgresSaver.setup()`; it does
not replace Alembic or run from an ordinary request.

## Pre-commit audit (owner-authorized publication only)

```bash
git status --short
git diff --check
git check-ignore -v .env frontend/.env secrets/postgres_password.txt secrets/auth_jwt_secret.txt
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Stage reviewed paths explicitly; never use `git add .`. This batch does not stage, commit, push, change branch protection, or dispatch paid evaluation.

## Portfolio hardening validation — 1 November 2026

See `../public-release-audit.md` and `../actions-review.md` for results and
immutable action provenance. Commands run from the repository root included:

```bash
TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db .venv/bin/pytest backend/tests -q
DATABASE_URL=postgresql+psycopg:///telecom_test_db .venv/bin/alembic current
DATABASE_URL=postgresql+psycopg:///telecom_test_db .venv/bin/alembic heads
DATABASE_URL=postgresql+psycopg:///telecom_test_db .venv/bin/alembic check
uv lock --check
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend audit --audit-level=moderate
uv run python -m backend.scripts.run_deterministic_evaluation
```

The paid Deep Agents and two-case RAGAS commands were explicitly opted in for
this task; do not enable them in routine CI. Optional evaluation pip-audit still
fails on its documented frozen dependencies; the runtime audit passes.

Browser/HTTP validation used `COMPOSE_PROJECT_NAME=signaldesk-release-audit`
and the equivalent of `COMPOSE_FILE=compose.yaml:compose.acceptance.yaml`, with
only `telecom_test_db` and separate volumes. CI browser acceptance now uses the
same dedicated override. Stop stacks without `-v`. Existing development volumes
must remain intact. Node's harness-level NO_COLOR/FORCE_COLOR warning is cosmetic;
RAGAS and Qdrant upstream compatibility warnings are documented, not suppressed.
