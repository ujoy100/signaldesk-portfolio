# Phase 16 — Docker Compose environment

**Status: DONE.** Images, startup ordering, health, migrations, checkpoints, fictional seeding, authenticated real-HTTP workflows, dependency degradation and non-destructive persistence were validated on 2026-10-26.

The topology contains PostgreSQL 17, Qdrant, an explicit Alembic migration job, an explicit LangGraph checkpoint provisioning job, FastAPI, and the Nginx-served Vite build. PostgreSQL and Qdrant use project-scoped named volumes. Neither datastore publishes a host port, so existing Mac services are neither reused nor overwritten. Only the UI and API bind loopback ports.

The optional `seed` profile invokes the existing repeatable fictional loader; it never resets data. Migration and checkpoint setup finish before FastAPI starts and are never performed by ordinary requests. Official MCP servers and the enforcing Gateway retain the frozen in-process backend transport; Compose does not add an unauthenticated network bypass.

Runtime secrets are mounted from ignored `secrets/*.txt` files through Compose secrets and Pydantic's file-secret source. OpenAI use remains optional and opt-in via the host environment; no provider key is copied into an image or Compose file.

Root and frontend Docker ignore rules exclude local environment files (while
retaining public `.env.example` templates), `secrets/`, private key/certificate
formats, caches, reports and build artifacts. Compose builds the backend's
production `runtime` target. A separate `evaluation` target installs the RAGAS
extra and Git executable required by RAGAS imports; it is not used by the API
service.

The backend obtains the database password from `DATABASE_PASSWORD_FILE`; it is URL-escaped in memory and is not emitted by Compose configuration. The development seed adds three fictional active identities and eight fictional Qdrant documents without deleting existing rows or collections.

## Acceptance evidence

- PostgreSQL, Qdrant, backend and frontend reached healthy state; migration and checkpoint jobs exited successfully.
- Real HTTP acceptance returned two grounded citations for SIM activation, rejected invalid/expired JWTs with 401 and an unauthorized approval with 403.
- A material ticket edit generated a replacement approval; its authorized execution changed one ticket and created exactly one `approved_update` event.
- Feedback submission/history and approval-controlled knowledge promotion passed; one active promoted point was verified directly in Qdrant.
- With Qdrant stopped, support returned HTTP 200 with `insufficient_evidence=true` and `knowledge_unavailable`, then recovered after restart.
- Before/after restart counts were identical: two tickets, one feedback row and nine Qdrant points.
- The corrected frontend health probe uses `127.0.0.1`, avoiding an Alpine `localhost` IPv6 false-negative.
- Public-release validation built runtime, evaluation and frontend images; the
  runtime contained neither RAGAS nor diskcache, and image inspection found no
  project environment or secret files.

Known limitation: qdrant-client 1.20 reports a compatibility warning with Qdrant 1.15.5. The validated operations pass; dependencies were not replaced merely to suppress the warning.

## Recovery and safety

`docker compose restart backend frontend` preserves both named volumes. Use `docker compose ps` and `docker compose logs --tail=200 SERVICE` to inspect failure. Re-run `migrate` or `checkpoints` explicitly; both are additive/idempotent. Never use `down -v` for routine operation because it deletes persistent volumes.

The test database is not part of the development stack. Backend write tests continue to require a separately provisioned database explicitly named `telecom_test_db`.
