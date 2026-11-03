FROM python:3.13-alpine AS base
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apk upgrade --no-cache \
    && pip install --no-cache-dir uv==0.13.6
COPY pyproject.toml uv.lock ./

FROM base AS evaluation
RUN apk add --no-cache git \
    && uv sync --frozen --no-dev --extra evaluation --no-install-project
COPY backend ./backend
COPY alembic.ini ./alembic.ini
CMD ["python", "-m", "backend.scripts.run_ragas_evaluation"]

FROM base AS runtime
RUN uv sync --frozen --no-dev --no-install-project \
    && python -c "import importlib.util; assert importlib.util.find_spec('ragas') is None; assert importlib.util.find_spec('diskcache') is None" \
    && /usr/local/bin/python -m pip uninstall --yes uv pip \
    && rm pyproject.toml uv.lock
COPY backend ./backend
COPY alembic.ini ./alembic.ini
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
