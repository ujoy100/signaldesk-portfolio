# Phase 17 — GitHub Actions CI/CD evaluation gate

**Status: IN PROGRESS.** Public-main commit `3124016` passes the application,
evaluation, secret/dependency and browser checks; the strict backend container
scan still fails. Public protection requires four checks, excluding the enabled
image-security job. The original private repository still has the plan-related
HTTP 403 protection blocker. See [current reconciliation](phase-17-reconciliation.md)
for exact evidence and remaining acceptance gaps. Historical validation sections
below retain their original dates and private-development scope; they do not
establish closure for the public portfolio or original private repository.

## Workflow architecture

`ci.yml` runs on pull requests, pushes to `main`, and manual dispatch. Its independent least-privilege jobs cover:

- backend locked dependency installation, Ruff, isolated PostgreSQL migrations, Alembic consistency, Qdrant-backed/backend tests, deterministic evaluation thresholds, and lock validation;
- production-only Python dependency export and vulnerability audit, excluding
  the explicitly isolated evaluation extra;
- frontend `npm ci`, ESLint, Vitest, production build, and production-dependency audit;
- Gitleaks plus pull-request dependency review; and
- reproducible backend/frontend multi-stage image builds and Compose-model validation.

`browser-acceptance.yml` provisions ephemeral CI-only Compose secret files, starts the complete isolated stack, seeds only fictional data, and runs the existing five Playwright scenarios in hosted Google Chrome. The public workflow retains only six allowlisted fictional screenshots after successful acceptance for seven days; it does not upload authenticated traces, HAR or videos. It stops services with `docker compose down`, never `down -v`.

`paid-evaluations.yml` is deliberately separate and manual. It requires the exact dispatch confirmation and references `paid-evaluation` plus `OPENAI_API_KEY` from GitHub Actions secrets. The public environment is not configured: its required-reviewer protection must be established before any optional paid run; the workflow reference alone does not enforce that protection. It bounds execution to the existing Phase 10 model scenario and two-case genuine RAGAS runner. No paid provider call occurs in ordinary CI.

Dependabot proposes weekly GitHub Actions, npm, and uv updates. Actions use controlled major release lines and explicit workflow permissions; Dependabot review is required before merging updates.

## Trust and data boundaries

CI uses only a disposable `telecom_test_db`, a pinned Qdrant container, deterministic fictional data, and clearly marked CI-only credentials. Development `.env` and `secrets/*.txt` are never read. Provider credentials are unavailable to pull-request and default push jobs. Images are built but never pushed, and no workflow deploys—deployment remains Phase 18.

The browser token issuer is invoked only inside the ephemeral backend container. It remains a CLI, rejects production, and has no public route. Playwright keeps JWTs in process/browser memory and asserts that local/session storage stay empty.

## Required hosted acceptance

Before closure, the owner must review and selectively stage Phase 1–17 source, migrations, tests, workflows, lockfiles, screenshots, and documentation; inspect the staged diff and secret scan; commit/push with explicit approval; then verify all required GitHub checks. Protect `main`, require reviewed pull requests and the backend, frontend, security, image-build, and browser checks. Configure the `paid-evaluation` environment with required reviewers before any optional paid run.

Hosted evidence now exists for public `3124016`; local tests alone remain insufficient. Unresolved acceptance items are the failing container check, the specification/public required-check discrepancy, original private-repository protection and repository-scope decisions, and protected-environment setup before optional paid execution. See the reconciliation; no acceptance criterion is relaxed.

## Local validation evidence — 27 October 2026

- `actionlint` 1.7.7: passed with no findings across all workflows.
- PyYAML parsing: all three workflows plus Dependabot configuration parsed successfully.
- Gitleaks 8.24.3: redacted `--no-git` scan of 213 tracked/non-ignored intended files (about 1.45 MB) found no leaks. Ignored local secret values were excluded from the temporary audit tree.
- Backend: Ruff format check reported 121 files formatted; Ruff lint passed; pytest reported 116 passed and one intentionally skipped paid-model test in 5.08 seconds.
- Deterministic 40-case gate passed: recall@3 0.7895, MRR 0.7895, abstention 0.8333, authorization/approval/schema safety 1.0.
- Alembic current and heads both reported `c3e7a91d5f20`; autogenerate consistency found no new operations.
- Frontend locked install succeeded; ESLint passed; Vitest reported 6 passed; production build passed; production dependency audit found zero vulnerabilities.
- Backend and frontend Docker image builds passed; Compose configuration was valid; the four already-running application services remained healthy.
- Playwright reran against the real healthy Compose stack in installed Chrome: 5 browser acceptance tests passed in 15.3 seconds.
- `uv lock --check` resolved 148 packages and `git diff --check` passed.

These results validate repository content locally. They are not substitutes for required GitHub-hosted workflow runs, so the phase remains IN PROGRESS.

## First hosted-run remediation — 27 October 2026

The first GitHub-hosted backend job reached 114 passed, two failed, and one
skipped. Both failures were runner-environment integration issues, not weakened
security controls:

- The fail-closed authentication test constructed `Settings(_env_file=None)`.
  That disables dotenv loading but intentionally does not ignore process
  environment variables, so the CI job's required `AUTH_JWT_SECRET` configured
  the test unexpectedly. The test now explicitly supplies
  `auth_jwt_secret=None`; the implementation continues to fail closed when the
  effective setting is absent.
- `str(test_db_engine.url)` uses SQLAlchemy's safe display representation and
  replaces a password with `***`. The checkpoint test passed that redacted URI
  to `AsyncPostgresSaver`, causing password authentication failure for the CI
  PostgreSQL user. `postgres_checkpoint_url()` now changes only the driver name
  and calls `render_as_string(hide_password=False)`, preserving percent-escaped
  credentials for the actual driver. Runtime workflow creation and checkpoint
  schema provisioning use the same converter.

Focused CI-style regression reported 7 passed. The complete backend suite with
CI authentication environment variables reported 117 passed and one
intentionally skipped paid-model test in 5.33 seconds; Ruff reported 123 files
formatted and lint clean. A dedicated unit test covers special-character
credential escaping. GitHub-hosted rerun evidence is still required.

## Second hosted-run remediation — 27 October 2026

The second hosted backend run connected successfully but failed because the
fresh CI database had Alembic application tables only; the official LangGraph
checkpoint tables had not been provisioned. CI now runs
`backend.scripts.setup_checkpoints` immediately after `alembic upgrade head`,
using the same job-level `DATABASE_URL`. The checkpoint integration test also
uses a focused fixture calling the same exported `setup_checkpoint_schema()`
function. This keeps the test independently reliable while the explicit CI step
continues to validate deployment-style provisioning. Ordinary API requests do
not create schemas.

Fresh-database validation used a new ephemeral PostgreSQL 17 container named
`telecom_test_db` with no volume. All Alembic migrations applied, official
`PostgresSaver.setup()` succeeded twice (idempotency), the four official tables
(`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, and
`checkpoint_migrations`) were present, and the reconstruction test passed in
1.81 seconds. The container was then auto-removed. Full regression reported 117
passed and one paid test skipped in 4.99 seconds; Ruff and actionlint passed.
Phase 17 remains IN PROGRESS pending the next GitHub-hosted result.

## Third hosted-run remediation — 27 October 2026

The run for commit `016ef6d` proved checkpoint provisioning successful: schema
setup, Alembic verification, all 117 backend tests, and the deterministic gate
passed. The job failed only afterward in `uv lock --check`. Global
`UV_FROZEN=true` makes uv implicitly use its lock-existence mode
(`--check-exists`), which cannot be combined with explicit `--check`. The
redundant global variable was removed; dependency installation remains frozen
through the explicit `uv sync --frozen` command, while `uv lock --check` now
performs the intended consistency verification. Hosted rerun evidence is still
required before Phase 17 closure.
