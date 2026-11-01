# Implementation Phase Tracker

**Frozen source of truth:** *Telecom Agentic AI Support Platform — Frozen Project Documentation*, v1.0, Section 20.

| Phase | Scope (abbreviated from frozen document) | Status |
|---|---|---|
| 0 | Repository, environment, React/Vite, FastAPI skeleton, config | **DONE** |
| 1 | PostgreSQL, Alembic, mock telecom data | **DONE** |
| 2 | Qdrant, embeddings, metadata, ingestion | **DONE** |
| 3 | Hybrid retrieval, reranking, citations, no-answer | **DONE** |
| 4 | Knowledge lifecycle and admin updates | **DONE** |
| 5 | Telecom MCP servers | **DONE** |
| 6 | MCP Gateway, policy, authorization, audit | **DONE** |
| 7 | LangGraph state, nodes, routing, checkpoints | **DONE** |
| 8 | Pydantic structured outputs and tool contracts | **DONE** |
| 9 | Human approval and resumable state | **DONE** |
| 10 | Bounded Deep Agent investigations | **DONE** |
| 11 | Security controls and permission checks | **DONE** |
| 12 | RAGAS and agent/safety/system evaluations | **DONE** |
| 13 | Observability, usage, latency, cost, feedback | **DONE** |
| 14 | Reliability, failure handling, idempotency | **DONE** |
| 15 | Full React operational UI | **DONE** |
| 16 | Docker Compose for complete local stack | **DONE** |
| 17 | GitHub Actions CI/CD evaluation gate | **IN PROGRESS** |
| 18 | Cloud deployment and production configuration | PENDING |
| 19 | Final docs, diagrams, screenshots, release notes | PENDING |

## Retained security blockers — 2026-11-01

Hosted commit `558ddfb` passed backend/migrations/evaluation, frontend quality,
strict secrets and real Compose browser acceptance (`41314181754`). CI
`41314181794` built both runtime images, then correctly failed the strict Trivy
job: frontend **0 HIGH/CRITICAL**, backend **46 HIGH rows / 10 distinct CVEs,
0 CRITICAL and 0 Python-package findings** after current stable OS upgrades.
These remaining upstream Debian advisories are explicitly tracked in SECURITY.md;
no suppression was added. Full npm audit is now enforced in CI, and the isolated
evaluation image build is included. Original favicon and browser title complete
the SignalDesk branding; frontend lint, 7 tests and build passed locally again.
Phase 17 stays **IN PROGRESS** for the failing container gate, required-check/PR
criteria and branch protection. Phases 18 and 19 stay **PENDING**.

## Runtime image remediation checkpoint — 2026-11-01

The stricter hosted scan for `86b8c53` exposed additional backend OS/build-tooling
findings and three fixable frontend OS rows; browser and application checks
passed. Python remains 3.13, now on Debian Trixie with available security updates;
Alpine packages are patched, uv CLI is 0.13.6, and pip/uv/build manifests are removed
from the API runtime after installation. Application dependency locks are unchanged.
The gate remains strict, including unfixed HIGH/CRITICAL advisories. Local Docker
cleanup was explicitly approved for audit-only images, but daemon I/O failures
prevented confirming cleanup; all volumes and development images remain protected.
Final hosted results must establish the retained publication blockers.
Phase 17 remains **IN PROGRESS**, Phases 18/19 **PENDING**.

## Container OS audit follow-up — 2026-11-01

Commit `4d11dda` passed exact-SHA hosted CI `41313577210` and browser acceptance
`41313577177`; both produced no annotations or retained artifacts. A later OS
scan found 60 HIGH/CRITICAL package rows in the old Nginx/Alpine frontend image.
The frontend base is updated to official Nginx 1.30.6/Alpine by immutable digest;
CI now scans both runtime images with pinned Trivy and fails on high/critical
findings. Local Docker storage filled during follow-up; no destructive cleanup
was performed. Hosted validation must establish the final container status.
Phase 17 remains **IN PROGRESS**; Phases 18 and 19 remain **PENDING**.

## Portfolio and public-release checkpoint — 2026-11-01

Phase 17 remains **IN PROGRESS**; Phases 18 and 19 remain **PENDING**.
Original CSS SignalDesk branding replaces the unused hero image. Historical
artwork was byte-matched to official Vite v8.3.0 and its upstream notice retained
without licensing original SignalDesk code. Recruiter READMEs, contribution,
provenance, immutable Actions review, audit and publication checklist are added.

Full backend regression: **128 passed / 1 intentionally skipped**; Ruff 133
files clean; Alembic single head `2d4f8a71c930` and consistency check passed;
uv lock passed. Frontend lint/build and **7 Vitest tests** passed. Targeted
minimatch 11.0.1 override resolves the development advisory; full npm audit and
runtime Python audit found no vulnerabilities. Optional evaluation still reports
the two documented RAGAS/diskcache advisory IDs and is isolated from runtime.

Deterministic 40-case gate passed (Recall@3/MRR 0.7895, abstention 0.8333,
safety/schema 1.0). Genuine Deep Agents acceptance **1 passed in 8.46s**;
bounded genuine RAGAS **2 cases**, precision/recall/faithfulness 1.0, relevancy
0.4979. Runtime/evaluation/frontend images built. Real HTTP Compose acceptance
passed exactly-once/approval/RBAC/promotion checks. Final Chrome Playwright
**5 passed in 13.8s**, including the corrected knowledge screenshot. Six screenshots
were visually reviewed. Dedicated acceptance Compose uses only `telecom_test_db`
and separate project volumes; no development data or volumes were removed.

Strict Gitleaks passed all 25 fetched branch/PR commits and all available evidence
from 55 Actions runs / 48 retained artifacts. Personal email metadata remains
an explicit publication decision. Actions now use reviewed immutable Node 24
versions, no persisted checkout credentials, no global Gitleaks allowlist, and
no automatic build-record or authenticated browser trace uploads. actionlint
passed. Branch-protection API still returns plan-related HTTP 403. Final commit
and hosted CI evidence are recorded separately after push; local success alone
does not close Phase 17. See `docs/public-release-audit.md` and
`docs/publication-checklist.md` for coverage and owner-only decisions.

## Phase 17 implementation checkpoint — 2026-10-27

Phase 17 is **IN PROGRESS**. Least-privilege workflows now cover backend,
PostgreSQL/Qdrant integration, Alembic consistency, deterministic evaluation,
frontend quality/build, dependency and secret review, Docker image builds, and
real Compose Playwright acceptance. Paid Deep Agent/RAGAS evaluation is a
separate, confirmation-gated manual workflow using a protected environment and
GitHub secret.

Local configuration and regression validation is required in this batch.
Closure remains blocked until these newly created workflows are selectively
committed and pushed with owner approval, pass on clean GitHub-hosted runners,
and required-check/branch-protection settings are confirmed. No deployment is
part of Phase 17.

Local validation on 27 October 2026 passed: actionlint 1.7.7, YAML parsing,
redacted Gitleaks over 213 intended files, Ruff over 121 files, backend pytest
116 passed/1 paid test skipped, the 40-case deterministic threshold gate,
Alembic head/check at `c3e7a91d5f20`, frontend ESLint/Vitest 6/build/npm audit,
Playwright 5 passed in 15.3 seconds against the real Compose stack, both Docker
image builds, Compose configuration, `uv lock --check` (148
packages), and `git diff --check`. Phase 17 remains IN PROGRESS because no
GitHub-hosted run or branch-protection evidence exists yet.

The first GitHub-hosted backend run subsequently reported 114 passed, two
failed, and one skipped. The failures were isolated to CI environment handling:
an auth test inherited CI's configured JWT secret, and SQLAlchemy's printable
URL redacted the PostgreSQL password before it reached AsyncPostgresSaver.
Focused fixes explicitly isolate the no-secret test and preserve/escape real
credentials during checkpoint URL driver conversion. Local CI-style validation
after the fixes reported 7 focused tests passed and 117 full backend tests
passed with one paid test skipped; Ruff and `git diff --check` passed. Phase 17
remains IN PROGRESS pending a successful GitHub-hosted rerun.

The second hosted run fixed authentication and connected to PostgreSQL, then
failed only because the clean runner lacked official LangGraph checkpoint
tables. CI now provisions those tables explicitly after Alembic using the same
isolated `DATABASE_URL`; the integration test fixture reuses the same official,
idempotent setup function. A fresh ephemeral PostgreSQL 17 validation applied
all migrations, ran checkpoint setup twice, confirmed all four official tables,
and passed graph reconstruction. Full backend regression reported 117 passed
and one paid test skipped; Ruff, actionlint, and `git diff --check` passed.
Phase 17 remains IN PROGRESS pending a green hosted rerun.

The run for `016ef6d` subsequently showed that checkpoint provisioning,
Alembic checks, 117 backend tests, and deterministic evaluation all passed. The
only failure was the final lock check: global `UV_FROZEN=true` requested uv's
implicit lock-existence mode while the command also supplied `--check`, an
invalid option combination. The redundant global setting was removed;
`uv sync --frozen` remains explicit. Phase 17 remains IN PROGRESS pending the
next hosted run and branch-protection verification.

The subsequent exact-SHA hosted runs passed backend, frontend, security,
image-build, and real Compose Playwright jobs. Phase 17 remains **IN PROGRESS**
only because required branch protection cannot be enabled for this private
repository under the current GitHub plan.

## Public-release dependency and Docker remediation — 2026-11-01

Docker build contexts now exclude local environments, secret directories,
private key/certificate formats, caches and generated artifacts while retaining
public example configuration. RAGAS remains supported through an explicit
evaluation extra and dedicated image target; the production API target contains
neither RAGAS nor diskcache. CI separately audits the production dependency
export. During validation, the current audit identified newly published pyasn1
advisories, so the lock was updated from 0.6.4 to 0.6.5 before final image and
regression checks. Optional RAGAS/diskcache advisories remain documented and
isolated from the production service. Phase 17 remains **IN PROGRESS** and Phase
18 remains **PENDING**.

Final validation reported Ruff clean, backend **128 passed / 1 intentionally
skipped**, frontend Vitest **7 passed**, frontend lint/build clean, and the
deterministic 40-case gate passed at Recall@3/MRR 0.7895, abstention 0.8333 and
all safety metrics 1.0. Runtime, evaluation and frontend images built; package
inspection confirmed the intended boundary and production pip-audit found no
known vulnerabilities. The optional evaluation audit continues to report only
the two documented RAGAS/diskcache advisories.

## Microsoft Entra authentication enhancement — 2026-10-27

Before Phase 18, SignalDesk added single-tenant OIDC Authorization Code Flow
with PKCE, FastAPI-owned callback handling, hashed and revocable PostgreSQL
sessions, mutation CSRF checks, explicit external-identity mappings, and
database-controlled roles. Production rejects the fictional JWT mechanism and
requires secure cookies. React supports Microsoft sign-in while preserving the
fictional development path for isolated CI. Configuration and explicit
administrator bootstrap are documented in `docs/authentication-entra.md`.
Real interactive Entra browser sign-in is **NOT YET VERIFIED** and does not
change any frozen phase status.

On 28 October 2026, the authenticated-session response was extended with the
validated Microsoft `name` claim stored per revocable session, with a safe
`Microsoft user` fallback and no role derivation. Migration `2d4f8a71c930` and
backend/frontend regressions cover extraction, fallback, logout/expiry, account
switching, and sidebar rendering. A read-only RAG investigation also confirmed
the exact mobile-data question currently returns `guide-network-001` at 0.8409;
no persistent retrieval data or authorization policy was modified.

## Phase 15 final browser acceptance — 2026-10-27

Phase 15 is **DONE**. Playwright drove installed Google Chrome against the real
Compose React and FastAPI services: **5 passed in 14.5s**. It verified RBAC,
invalid/expired sessions, safe errors, deterministic SIM evidence/citations,
automatic feedback, result preservation, human-readable approval scope,
edit/replacement authorization, controlled execution, knowledge promotion,
restricted feedback history, responsive mobile layout, and empty local/session
storage. Sanitized screenshots are under `docs/screenshots/phase15-*.png`.

The user also completed separate manual browser acceptance: a 3/5 feedback item
persisted; approval #4 was edited from resolved to in-progress; replacement #5
required fresh authorization and executed; and a read-only PostgreSQL query
confirmed ticket 1 remained in-progress/high. These manual results are not
represented as automated Playwright evidence.

The business UX now shows current/proposed ticket fields, constrained edit
controls, collapsed technical scope, inline automatically linked feedback,
session-memory result preservation, readable evidence/timelines, and an
evidence-strength label. Development token paste remains non-production;
production OIDC/SSO and authorized customer/ticket lookup remain later work.

## Phase 15–16 acceptance checkpoint — 2026-10-26 (historical)

At this checkpoint Phase 15 remained **IN PROGRESS** only because native browser automation was
unavailable. Its implementation, component tests, build and real Compose HTTP
integration passed. Phase 16 is **DONE**: isolated Compose startup, health,
explicit initialization, real workflows, failure degradation and persistence
were exercised without deleting volumes.

- Frontend: ESLint passed; Vitest **6 passed**; Vite production build passed.
- Backend: Ruff passed for 119 files; pytest **116 passed, 1 intentionally
  skipped** in 6.15s. The existing RAGAS deprecation warning remains unchanged.
- Alembic: current/head `c3e7a91d5f20`; consistency check clean.
- Compose: configuration and builds passed; PostgreSQL, Qdrant, backend and
  frontend became healthy and migration/checkpoint jobs completed.
- `uv lock --check` and `git diff --check` passed.
- Real HTTP acceptance verified two SIM citations, 401 invalid/expired JWTs,
  403 unauthorized approval, material-edit reauthorization, exactly one ticket
  event, feedback history and one active promoted Qdrant point.
- Qdrant outage degraded to insufficient evidence; restart preserved two
  tickets, one feedback row and nine Qdrant points.
- Browser automation was attempted, but no controlled browser was available and
  macOS Computer Use permissions were not granted. Phase 15 is not marked DONE.

## Phase 0 current validation snapshot — 2026-10-21

**Overall status: DONE (acceptance recorded 2026-10-21).** React/Vite, FastAPI, local integration, automated testing and scoped security checks satisfy the frozen Phase 0 foundation gate. The Phase 0 closure and final command-reference commits were pushed successfully; the working tree was confirmed clean after commit `3a23b89`.

| Checkpoint | Evidence | Status |
|---|---|---|
| Backend | `uv run pytest backend/tests -q`: **21 passed in 0.22s** | PASSED |
| Backend code quality | `uv run ruff check backend`: all checks passed; `uv run ruff format --check backend`: 14 formatted | PASSED |
| Frontend | ESLint clean; `vitest run`: **5 passed**; Vite build: **18 modules transformed**, 106ms | PASSED |
| Browser integration | Ready, manual Refresh, Unavailable after stopping FastAPI, Ready after restart | PASSED (user-confirmed) |
| Python dependencies | `uv lock --check`: resolved 36 packages | PASSED |
| Frontend dependencies | `npm --prefix frontend ls --depth=0`: dependency tree valid, includes Vitest/Testing Library/jsdom | PASSED |
| Git exclusion rules | `.env`, `frontend/.env`, `frontend/node_modules`, `frontend/dist` verified with `git check-ignore -v` | PASSED |
| Security acceptance | Safe `.env.example` values reviewed; ignore rules, staged contents, and limited credential-pattern scan passed; not a complete secret audit | PASSED (scoped review) |
| Repository checkpoint | Private GitHub repository user-confirmed; clean synced `main`; commits `6533a2d`, `1787344`, `2c90b55`, and `3a23b89` verified | PASSED |

## Phase 0 gate

Do not mark Phase 0 DONE until its implementation, automated tests, relevant validation/security checks, configuration/API documentation, integrated local boot, known limitations, and tracker updates are complete. Details: `docs/phases/phase-0-foundation.md`.

## Phase 0 GitHub milestone — 2026-10-21

- GitHub repository: `https://github.com/ujoy100/telecom-agentic-ai-support` (visibility **Private**, user-confirmed).
- Initial implementation commit: `6533a2d` — `chore: initialize telecom agentic AI support foundation`.
- Git/GitHub documentation commit: `1787344` — `docs: document private GitHub setup and push workflow`.
- Phase 0 closure commit: `2c90b55` — `docs: finalize phase 0 acceptance and closure`.
- Final command-reference commit: `3a23b89` — `docs: record verified phase 0 closure commands`.
- After second push, `git status` reported `main` up to date with `origin/main` and a clean working tree.
- The README contains 157 lines; local `.env`, `frontend/.env`, `.venv`, frontend build outputs and dependencies were excluded from the initial staged snapshot.
- `git diff --cached --check` passed after normalizing CSS and development-requirements whitespace; `.gitattributes` permits intentional Markdown end-of-line spaces.
- Limited staged secret-pattern scan showed no matches. This is not proof of absence of all secrets.

**Phase 0 acceptance decision (2026-10-21): DONE.** Implementation, tests, configuration/API documentation, local boot, scoped security checks and known limitations were reviewed. The user copied the closure docs into Cursor and `git diff --check` returned no errors. **Publication verified:** both closure-documentation commits were pushed; after `3a23b89`, `git status` confirmed `main` up to date with `origin/main` and a clean working tree. **Historical note:** Phase 1 was PENDING at Phase 0 closure and was completed on 2026-10-25.


## Phase 1 implementation checkpoint — 2026-10-25

**Overall status: DONE.** Phase 1 acceptance was completed on 2026-10-25 after isolated PostgreSQL tests, a guarded disposable migration lifecycle, security configuration documentation, and final validation.

### Verified implementation and evidence

| Checkpoint | Evidence shared in conversation | Status |
|---|---|---|
| PostgreSQL 17.9 and local `telecom_db` | `pg_isready`: accepting connections; Psycopg and SQLAlchemy queries returned `telecom_db` | VERIFIED |
| Database connection configuration | `.env` ignored by Git (`git check-ignore .env` → `.env`); Pydantic Settings loads `DATABASE_URL`; SQLAlchemy engine connected | VERIFIED (local) |
| Database dependencies | `uv tree --depth 1`: SQLAlchemy 2.1.5, Alembic 1.20.0, Psycopg 3.3.6 | VERIFIED |
| ORM infrastructure | `backend/app/db/base.py`, `session.py`; shared `Base.metadata`, engine and session provider | IMPLEMENTED, basic verification |
| Sixteen application tables | All frozen Phase 1 domains are represented in SQLAlchemy models and Alembic metadata | IMPLEMENTED / CONSISTENT |
| Fifteen sequential Alembic migrations | Complete linear chain applied to `telecom_test_db`; autogenerate consistency found no pending operations | APPLIED / VERIFIED |
| Latest known revision | `926cf9047962`; both `alembic current` and `alembic heads` reported this single head | VERIFIED |
| Human approval reviewer integrity | Named FK `fk_human_approvals_reviewer_id_users` references `users(id)`; verified via `psql -d telecom_db -c '\d human_approvals'` | VERIFIED |
| Backend regression and integration tests | isolated PostgreSQL command → **29 passed** (final run 0.53s) | PASSED |
| Ruff | no-fix lint and format check passed across 55 backend Python files | PASSED |
| Phase 1 command/technical docs | Command reference, foundation notes, and tracker updated with implementation and actual results | UPDATED |

### Applied migration history

| Order | Revision | Change |
|---|---|---|
| 1 | `d3c0dd1b1ef8` | Create `customers` |
| 2 | `5e95fe8a3b9f` | Create `plans` |
| 3 | `5bc9c3472a11` | Create `subscriptions` |
| 4 | `3e82659e5801` | Create `tickets` |
| 5 | `61730074f548` | Create `ticket_events` |
| 6 | `ffc9b72b6f3e` | Create `human_approvals` |
| 7 | `947e5dccc67c` | Create `roles`, `users`, and reviewer foreign key |
| 8 | `d30eabd9f17a` | Create `conversations` |
| 9 | `b7bebfdfd40a` | Create `audit_events` |
| 10 | `42a7b9d9608c` | Create `feedback` |
| 11 | `132787509120` | Create `evaluation_runs` |
| 12 | `0fb4cf502b33` | Create `evaluation_scores` |
| 13 | `407281676bcc` | Create `prompt_versions` |
| 14 | `fffa3775b366` | Create `model_versions` |
| 15 | `926cf9047962` | Create `retriever_versions` |

**Migration issue and correction:** Alembic autogenerated a `drop_constraint(None, ...)` rollback instruction for the new reviewer foreign key and emitted a warning. The user edited the seventh migration so `create_foreign_key` and `drop_constraint` both use `fk_human_approvals_reviewer_id_users`; Python syntax validation passed, the upgrade executed, and PostgreSQL showed the named constraint. The database foreign key verifies existence of a reviewer, **not authorization**. No claim of complete HITL enforcement is made.

### Phase 1 acceptance closure

- Added `docs/db/postgresql-runtime-role.sql`, an idempotent administrator-run
  template that creates or hardens a non-superuser runtime role, grants only
  data access and sequence use, and keeps schema migration authority separate.
  Credentials remain external and the role was not created automatically.
- Added a migration-cycle runner that refuses every database except
  `telecom_migration_test_db` and requires `ALLOW_DISPOSABLE_DB_TEST=yes`.
- With explicit approval, created that disposable database, upgraded all 15
  migrations, downgraded to base, upgraded to head, and ran `alembic check`.
  The cycle passed and the disposable database was deleted. Development and
  test data were untouched.
- Reviewed seed concurrency and documented that normal serial reruns are safe;
  simultaneous subscription/event loaders are not claimed to be race-proof.
- Final combined validation later in the same batch passed 42 backend tests.

### Batch validation update — 2026-10-25

- Added deterministic fictional seed data for 3 customers, 2 plans, 3 subscriptions, 2 tickets, and 3 ticket events. The loader is atomic and repeatable and never deletes existing records.
- Added an explicit command: `uv run python -m backend.app.db.seed`.
- Hardened isolated testing: `TEST_DATABASE_URL` is mandatory, must name PostgreSQL `telecom_test_db`, and the connected database name is verified. Each write test rolls back reliably; expected integrity errors use savepoints.
- Added tests for rollback, uniqueness, foreign keys, subscription/ticket check constraints, seed contents, fictional identity convention, and repeat loading.
- `TEST_DATABASE_URL=postgresql+psycopg:///telecom_test_db uv run pytest backend/tests -q`: **29 passed in 0.38s**.
- Ruff: lint passed; formatting check passed for **55 backend Python files**.
- Alembic against `telecom_test_db`: current and only head are `926cf9047962`; `alembic check` reported no new upgrade operations.
- Documentation updated in this tracker, `phase-1-database-foundation.md`, and the new `phase-1-command-reference.md`.
- Known limitation: seed existence checks for subscriptions/events are safe for normal serial runs but are not claimed to prevent duplicates from simultaneous loader processes.

## Phase 2 acceptance — 2026-10-25

**Status: DONE.** Implemented validated LangChain document loading and
splitting, deterministic LangChain embeddings, structured Pydantic metadata,
stable Qdrant IDs, repeatable ingestion, environment-based configuration, and
fictional telecom knowledge. In-memory tests and temporary real-server Qdrant
validation both passed. Details and limitations are in
`docs/phases/phase-2-knowledge-ingestion.md`.

## Phase 3 acceptance — 2026-10-25

**Status: DONE.** Dense, BM25, reciprocal-rank hybrid retrieval, deterministic
cross-signal equivalent reranking, metadata/access filters, cited evidence,
and explicit no-answer behavior are implemented. The 14-case expanded
benchmark covers paraphrases, distractors, inactive versions, restricted
knowledge, and unsupported questions. Recall@3 and no-answer accuracy are 1.0
for all modes; vector MRR is 0.9 and the other MRR values are 1.0. The prior
Mars false positive now returns no-answer in all four modes.

## Phase 4 acceptance — 2026-10-25

**Status: DONE.** Added two lifecycle tables and migration `61f42e7c9a10`,
checksums, stable lineage IDs, duplicate skipping, draft/active/inactive state,
incremental versions, Qdrant deactivation, audit events, strict FastAPI schemas,
and JWT authentication. Promotion is deliberately disabled at the public
boundary until Phase 9 approval execution is trustworthy.

## Phase 5 acceptance — 2026-10-25

**Status: DONE.** Three official-SDK MCP servers expose all frozen knowledge,
customer, and ticket tools. Protocol discovery/invocation, typed outputs,
invalid arguments, missing records, and server-side ticket-write denial are
tested through MCP clients.

## Phase 6 acceptance — 2026-10-25

**Status: DONE.** The Gateway performs authenticated, namespaced MCP routing,
role policy, discovery, structured denial/error handling, UUID request IDs,
timeouts, bounded safe retries, and audit callbacks/database persistence.
Controlled writes remain unavailable even when approval is claimed.

### Final Phase 3–6 validation snapshot

- Ruff lint: all checks passed.
- Ruff format check: 87 Python files formatted.
- Backend suite with isolated PostgreSQL: **66 passed in 1.71s** on the final run.
- Alembic current/head: `61f42e7c9a10`; autogenerate consistency found no new
  operations.
- Guarded disposable lifecycle: all 16 migrations upgraded, downgraded to
  base, upgraded again, checked, and the disposable database was removed.
- Expanded 14-case benchmark: recall@3 and no-answer accuracy 1.0 for all four
  strategies; MRR 0.9 vector-only and 1.0 for keyword/hybrid/reranked.
- Dependency lock and `git diff --check`: passed.

## Phase 7 acceptance — 2026-10-25

**Status: DONE.** The frozen workflow is a genuine asynchronous LangGraph
`StateGraph` with conditional routing, strict state boundaries, Gateway-only
operational access, and official PostgreSQL checkpointing. A real integration
test interrupts at approval, disposes the original runtime, reconstructs fresh
graph/checkpointer instances, resumes the same thread, and proves a repeated
resume does not duplicate execution. Missing checkpoints recover safely.
Checkpoint DDL is an explicit provisioning command, not request-time behavior.

## Phase 8 acceptance — 2026-10-25

**Status: DONE.** The complete `SupportResolution` and related API/evidence/tool
contracts are strict Pydantic models. Confidence is derived from evidence/tool
signals, insufficient evidence is explicit, citations retain document/version
metadata, and malformed or instruction-like MCP output is rejected before graph
state updates. The current generator is explicitly deterministic; no LLM run is
claimed.

## Phase 9 acceptance — 2026-10-25

**Status: DONE.** PostgreSQL approvals, JWT-to-database identity binding,
approve/edit/reject, exact action digests, expiry, row locking, concurrent
decision control, transaction rollback, dual Gateway/tool verification,
single-use execution, ticket update/creation, audit, and resumable workflow
execution are implemented and tested. Authoritative knowledge promotion uses
exact version/document/checksum scope, Gateway and MCP enforcement, and a
recoverable PostgreSQL-coordinated Qdrant publication state machine. Failure
injection covers Qdrant staging/publication, PostgreSQL authority commit,
restart/retry, replay, mismatch, and concurrent ownership.

Final review on 2026-10-26 confirmed recovery through a newly constructed
database session and lifecycle service after simulated runtime loss. No
unapproved point becomes active during the interruption; the reconstructed
runtime completes the persisted `committed → published` transition exactly once.

### Final Phase 7–9 validation snapshot

- Ruff format: **100 files already formatted**; lint passed.
- Isolated PostgreSQL backend suite: **93 passed in 2.61s**.
- Alembic current and only head: `c3e7a91d5f20`; consistency check found no
  upgrade operations even with separately provisioned checkpoint tables.
- `uv lock --check`: resolved 91 packages in 13ms.
- `git diff --check`: passed.

## Phase 10 implementation checkpoint — 2026-10-26

**Status: DONE.** Official Deep Agents integration, conditional
LangGraph routing, MCP-only read tools, strict `InvestigationResult`, execution
budgets, timeouts, PII redaction, authoritative evidence reconstruction and
offline deterministic tests are implemented. Simple SIM activation remains on
the deterministic route. Genuine OpenAI acceptance with
`openai:gpt-4.1-mini` passed through LangGraph, official Deep Agents, authorized
MCP Gateway tools, validated evidence/citations, and structured resolution.

## Phase 11 acceptance — 2026-10-26

**Status: DONE.** Active PostgreSQL identity/role binding now also occurs
independently in the production MCP Gateway. Retrieval uses the verified role;
model-bound content is PII-redacted and isolated as untrusted data; strict MCP
and investigation contracts, read-only capability controls, safe audit fields,
approval replay protection and fail-closed dependency behavior are tested.
Prompt-injection risk is documented as defense in depth rather than solved by a
heuristic filter.

### Phase 10–11 validation snapshot

- Ruff format check: **104 files already formatted**; lint passed.
- Focused investigation/security/workflow/Gateway suite: **21 passed in 1.47s**.
- Full isolated PostgreSQL backend suite: **103 passed in 2.81s**.
- Alembic current and only head: `c3e7a91d5f20`; consistency check found no
  new upgrade operations.
- `uv lock --check`: resolved 104 packages in 12ms.
- `git diff --check`: passed.

### Phase 10 genuine model acceptance — 2026-10-26

- Presence-only Pydantic settings checks confirmed `OPENAI_API_KEY` and
  `DEEP_AGENT_MODEL`; no secret value was printed.
- Opt-in real-model test: **1 passed in 8.77s**.
- Verified required Customer plan and Ticket history calls, authoritative
  evidence, citation binding, six-call maximum, timeout/recursion bounds, and
  no controlled ticket/knowledge/approval tool access.
- Final offline regression: **103 passed, 1 opt-in test skipped in 3.19s**.
- Final Ruff checks passed for **105 files**; Alembic remained at single head
  `c3e7a91d5f20`; schema check, lock check (108 packages), and diff check passed.

## Phase 12–14 acceptance — 2026-10-26

**Phase 12 DONE.** Added the versioned 40-case fictional dataset, reproducible
deterministic/system metrics, PostgreSQL report persistence, documented gates,
and a two-case opt-in genuine RAGAS/OpenAI runner. Offline scores: Recall@3
0.7895, MRR 0.7895, abstention 0.8333, authorization/approval/schema safety
1.0. Real RAGAS: context precision 1.0, context recall 1.0, faithfulness 1.0,
answer relevancy 0.498.

**Phase 13 DONE.** Correlation IDs and privacy-safe structured telemetry cover
HTTP, LangGraph nodes, retrieval, MCP and Deep Agents, including latency,
errors, evidence/tool/model counts, token usage and versioned cost estimates.

**Phase 14 DONE.** Bounded idempotent retry, fail-closed degradation and
Admin-authorized promotion reconciliation extend the existing timeout,
checkpoint, approval and exactly-once controls. Reconciliation recovery after
Qdrant publication failure is tested through reconstructed runtime state.

### Phase 12–14 final validation

- Focused evaluation/observability/reliability/fault suite: **32 passed in
  4.11s**.
- Full backend suite: **112 passed, 1 intentionally skipped in 4.24s**.
- Genuine bounded RAGAS: **2 cases**, context precision 1.0, context recall
  1.0, faithfulness 1.0, answer relevancy 0.498.
- Ruff: **114 files formatted**, lint passed.
- Alembic current/only head: `c3e7a91d5f20`; consistency found no new upgrade
  operations.
- `uv lock --check`: **148 packages resolved**; `git diff --check`: passed.
- Known warning: RAGAS 0.3.9 imports sunset `langchain-community` VertexAI
  compatibility code even for OpenAI evaluation. The isolated shim and warning
  are documented; future dependency upgrades should remove it.

**Historical status at the Phase 12–14 checkpoint:** Phases 0–14 **DONE**; Phases 15–19 **PENDING**.
No commit, push, or deployment was performed.
