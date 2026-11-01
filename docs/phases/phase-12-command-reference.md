# Phase 12 command reference

Install the evaluation-only dependencies explicitly:

```bash
uv sync --frozen --extra evaluation
```

Run the deterministic 40-case gate without a provider call:

```bash
uv run python -m backend.scripts.run_deterministic_evaluation
```

```bash
TEST_DATABASE_URL='postgresql+psycopg:///telecom_test_db' \
  uv run pytest backend/tests/test_evaluation.py -q
```

Genuine paid evaluation, hard-limited to two cases by the script:

```bash
RUN_REAL_RAGAS=yes uv run python -m backend.scripts.run_ragas_evaluation
```

Never enable the paid command in ordinary CI. Credentials load from ignored
environment configuration through Pydantic `SecretStr`.

Build and smoke-test the isolated evaluation image:

```bash
docker build --target evaluation -t signaldesk-evaluation:local -f backend/Dockerfile .
docker run --rm signaldesk-evaluation:local python -c \
  "from backend.app.evaluation.ragas_runner import _load_ragas; print(_load_ragas()['Faithfulness'].__name__)"
```
