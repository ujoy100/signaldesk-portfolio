# Phase 2 Command Reference

## Start Qdrant for local development

Using the official container directly for Phase 2 validation:

```bash
docker pull qdrant/qdrant:latest
docker run --rm --name telecom-qdrant -p 6333:6333 qdrant/qdrant:latest
```

Persistent Docker Compose orchestration is intentionally deferred to Phase 16.

## Ingest fictional knowledge

```bash
uv run python -m backend.app.knowledge.ingestion
```

Verified twice against temporary Qdrant on 2026-10-25:
`Fictional knowledge indexed: documents=6, chunks=6`.

## Run Phase 2 tests

```bash
uv run pytest backend/tests/test_knowledge_ingestion.py -q
```

These tests use isolated in-memory Qdrant storage and do not modify a local
server collection.
