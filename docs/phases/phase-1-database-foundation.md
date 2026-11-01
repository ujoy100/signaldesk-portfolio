# Phase 1 — PostgreSQL, Alembic and Mock Telecom Operational Data

**Project:** `telecom-agentic-ai-support`  
**Date opened:** 2026-10-21  
**Last evidence update:** 2026-10-25  
**Status:** **DONE**  
**Prior phase:** Phase 0 **DONE**, latest previously verified Git commit `7358213`  
**Frozen authority:** *Telecom Agentic AI Support Platform — Frozen Project Documentation*, v1.0, Sections 6, 16, 20 and the global Definition of DONE.

## 1. Frozen scope and acceptance gate

**Phase 1:** PostgreSQL schema, Alembic migrations, mock telecom operational data.

**Frozen completion evidence:** Database created; migrations and tests pass. As with all phases, mark DONE only after code, applicable tests/validation, security and technical documentation are complete. Neither a local database nor an installed dependency alone completes this phase.

## 2. Architecture and design decisions

- **PostgreSQL** is the frozen structured/transactional source of truth, separate from **Qdrant**, which will later store unstructured telecom knowledge.
- **Alembic** is required for version-controlled schema changes. Do not manually create application tables through ad hoc SQL in the local database.
- **SQLAlchemy 2.1.5** is the implemented ORM toolkit; **Alembic 1.20.0** manages schema changes and **Psycopg 3.3.6** connects to PostgreSQL (all verified by `uv tree`).
- The user chose the local development database name **`telecom_db`**, replacing an initial empty practice database called `telecom_agentic_support`.
- Local configuration uses Pydantic Settings reading the Git-ignored `.env`; `DATABASE_URL=postgresql+psycopg:///telecom_db` was user-confirmed. Psycopg and SQLAlchemy both connected successfully. The administrator-run least-privilege runtime-role template is documented in `docs/db/postgresql-runtime-role.sql`; credentials and provisioning remain external. Never commit credentials or `.env` files.
- Preserve the existing React + Vite frontend and FastAPI + Pydantic backend. Do not modify the previous Telecom RAG chatbot project.

### Frozen PostgreSQL data domains

The frozen document identifies:

1. Users and roles.
2. Customers and plans.
3. Tickets and ticket events.
4. Human approvals.
5. Conversation/session metadata.
6. Audit events.
7. Feedback records.
8. Evaluation runs and scores.
9. Prompt/model/retriever version records.

Sixteen application tables now cover the frozen Phase 1 domains: operational customer/support records, roles/users and approvals, conversation and feedback metadata, audit records, evaluations, and prompt/model/retriever versions. Additional service-status, balance, and roaming records remain subject to later frozen MCP contract design. Approval execution authorization remains a later-phase control; storing approvals is not equivalent to enforcing them.

## 3. Progress and evidence (through 2026-10-25)

**Evidence meanings:** **VERIFIED** = actual command output observed; **DOCUMENTED** = a deployment-time configuration is supplied without storing credentials. Phase 1 acceptance was recorded after the final checks below.

| Checkpoint | Status | Evidence / notes |
|---|---|---|
| PostgreSQL 17.9 and `telecom_db` | **VERIFIED** | `pg_isready` accepting connections; Psycopg `Connected to: telecom_db`; psql inspections and migrations executed against the database |
| Dependencies | **VERIFIED** | SQLAlchemy 2.1.5, Alembic 1.20.0, `psycopg[binary]` 3.3.6; 43 resolved packages |
| `.env` Git ignore | **VERIFIED** | `git check-ignore .env` printed `.env`; database URL in `.env` user-confirmed; credential-free local URL observed |
| Pydantic database setting | **VERIFIED** | `get_settings().database_url` yielded `postgresql+psycopg:///telecom_db` |
| SQLAlchemy ORM base and session | **VERIFIED** | Base imported; `engine.connect()` returned `telecom_db` |
| Alembic connection/metadata | **VERIFIED** | `uv run alembic current`; models imported for `Base.metadata`; migrations generated and applied |
| Customers, plans, subscriptions | **VERIFIED** | Models imported; migrations applied; `psql \d` output checked |
| Tickets and ticket events | **VERIFIED** | Models imported; migrations applied; PostgreSQL table/index/FK output checked |
| Human approvals | **VERIFIED (schema)** | Pending default, allowed statuses and reviewer FK inspected in PostgreSQL; approval workflow security not implemented |
| Users and roles | **VERIFIED (schema)** | `psql -d telecom_db -c '\d users'` and `\d roles` confirmed columns, unique constraints, user-role FK, and reverse reviewer reference |
| Seventh migration | **VERIFIED** | Applied revision `947e5dccc67c`; reviewer FK `fk_human_approvals_reviewer_id_users` directly verified |
| Existing backend regression | **VERIFIED** | `uv run pytest backend/tests -v` → 22 passed in 0.49s after Ruff automatic fixes |
| Existing DB connection test | **VERIFIED** | `backend/tests/test_database.py::test_database_connection` passed (local development PostgreSQL) |
| Ruff fixes | **VERIFIED** | `uv run ruff check . --fix` → 40 fixed, 0 remaining; fresh no-fix lint run not separately reported |
| Runtime role and isolated test DB | **VERIFIED / DOCUMENTED** | Write tests accept only `telecom_test_db`; credential-free least-privilege role template supplied for administrator provisioning |
| Frozen data-domain tables | **IMPLEMENTED / CONSISTENT** | 16 model tables registered; test database at migration head; Alembic found no model/schema drift |
| Deterministic fictional data seeds | **VERIFIED IN TESTS** | Atomic, non-destructive loader covers customers, plans, subscriptions, tickets, and events; repeat run tested |
| Comprehensive DB/migration tests | **PASSED** | Constraints, rollback, seeds, migration upgrade/downgrade/re-upgrade, head, and autogenerate consistency verified |
| Full Phase 1 docs and tracker | **COMPLETE** | Foundation notes, command reference, architecture/security decisions, limitations, and tracker updated; no commit/push requested |

### 3.1 Implemented application schema

| Table | Purpose | Important integrity features |
|---|---|---|
| `customers` | Customer record | Unique customer number; optional unique email; timestamp |
| `plans` | Telecom package | Unique plan code; decimal monthly price `NUMERIC(10,3)` |
| `subscriptions` | Customer ↔ plan service | FKs to customers/plans; indexed IDs; `active/suspended/cancelled` check |
| `tickets` | Support issue/current state | FK to customer and optional subscription; unique ticket number; status and priority checks |
| `ticket_events` | Support history | FK to tickets; ticket/time indexes; actor type (not yet authenticated) |
| `human_approvals` | Proposed sensitive AI actions | FK to optional ticket and reviewer user; pending/approved/rejected/expired check; indexes |
| `roles` | Access-control role catalog | Unique role name |
| `users` | Application user metadata | Unique email; role FK; `is_active`; role index |

**Relationship summary:** `roles.id → users.role_id → human_approvals.reviewer_id`; `customers.id → subscriptions.customer_id`; `plans.id → subscriptions.plan_id`; `customers.id → tickets.customer_id`; `subscriptions.id → tickets.subscription_id` (optional); `tickets.id → ticket_events.ticket_id` and `human_approvals.ticket_id` (optional).

**Security and behavior boundaries:** Foreign keys show *existence*, not *authorization*. Login, permissions, signed-off reviewer actions, approval state-machine enforcement, and immutable audit records are not implemented yet. `tickets.updated_at` has a database insert default and SQLAlchemy `onupdate`; it is not maintained by a general PostgreSQL trigger. `actor_type` in ticket events is not authenticated identity. The one-role-per-user design may need revision if frozen permission requirements demand multi-role memberships; do not silently change it.

### 3.2 Verified migration chain

| Revision | Change | Evidence |
|---|---|---|
| `d3c0dd1b1ef8` | Create `customers` | Applied; `\d customers` checked |
| `5e95fe8a3b9f` | Create `plans` | Applied; `\d plans` checked |
| `5bc9c3472a11` | Create `subscriptions` | Applied; FKs, check and indexes checked |
| `3e82659e5801` | Create `tickets` | Applied; constraints/FKs inspected |
| `61730074f548` | Create `ticket_events` | Applied; FK/indexes inspected |
| `ffc9b72b6f3e` | Create `human_approvals` | Applied; status check and ticket FK inspected |
| `947e5dccc67c` | Create roles/users and add reviewer FK | Applied; named reviewer FK and role FK inspected |
| `d30eabd9f17a` | Create `conversations` | Applied to isolated test database |
| `b7bebfdfd40a` | Create `audit_events` | Applied to isolated test database |
| `42a7b9d9608c` | Create `feedback` | Applied to isolated test database |
| `132787509120` | Create `evaluation_runs` | Applied to isolated test database |
| `0fb4cf502b33` | Create `evaluation_scores` | Applied to isolated test database |
| `407281676bcc` | Create `prompt_versions` | Applied to isolated test database |
| `fffa3775b366` | Create `model_versions` | Applied to isolated test database |
| `926cf9047962` | Create `retriever_versions` | Verified current and only head; no schema drift |

**Seventh migration lesson:** Alembic autogenerate warned that an unnamed `drop_constraint(None, ...)` would fail on downgrade. The migration was edited to use **`fk_human_approvals_reviewer_id_users`** in both `create_foreign_key` and `drop_constraint`. Ruff fixed generated typing/import style; Python `py_compile` passed; migration applied with `uv run alembic upgrade head` and the constraint name was observed in `psql`. **A real downgrade/upgrade cycle has not been tested.**

## 4. Existing reference data: prior Telecom RAG project

Earlier project documentation reports `tickets.db` (SQLite) with **19 resolved support-ticket examples**, `faq.csv` with 25 FAQs and a telecom guide PDF. These are reference sources only. Before adapting historical tickets into the new PostgreSQL mock dataset:

- Inspect the **actual** read-only SQLite schema and records.
- Check that all imported records are fictional or anonymized, with no real customer identifiers or sensitive information.
- Preserve useful ticket categories/descriptions/resolutions, mapping them to the new model and adding realistic fictional customers, plans, services and open ticket histories.
- Do not copy Chroma, the previous application architecture or its code into the new project. FAQs/PDF knowledge will be more relevant to Phase 2 Qdrant ingestion.

## 5. Accelerated implementation batches

**Batch A — Database environment and core design (DONE):** PostgreSQL, dependency configuration, `.env` protection, schema foundations, isolated test database, and runtime-role policy verified or documented.

**Batch B — ORM and migrations (DONE):** `backend/app/db/base.py`, `session.py`, 16 model files, and the Alembic environment are implemented. All 15 sequential migrations passed current/head/autogenerate consistency and a guarded upgrade/downgrade/re-upgrade lifecycle.

**Batch C — Seed data and tests (IMPLEMENTED / VERIFIED):** Repeatable fictional data seeds and isolated PostgreSQL tests are implemented. The suite verifies rollback, uniqueness, foreign keys, check constraints, seed relationships, and repeat execution against `telecom_test_db`.

**Batch D — Acceptance and documentation (DONE):** Final combined validation passed 42 backend tests, Ruff lint/format, Alembic current/head/consistency, and the disposable migration lifecycle on 2026-10-25. The runtime-role template and security boundaries are documented. No commit or push was performed.

## 6. Learning notes

- `createdb telecom_db` creates a database **inside the PostgreSQL server**, not a folder in the project.
- `psql -d telecom_db` opens the SQL command-line session for a chosen database.
- `psql -l` (Mac terminal) and `\l` (inside psql) list databases.
- `\dt` lists relations in the current search path; no application tables are expected before migrations.
- `\pset pager off` changes display behavior only; it does not modify stored data.
- `\q` exits the client but does not stop PostgreSQL.
- `dropdb` is destructive and should only be used with an explicitly checked target.
- `uv tree --depth 1` displays direct project dependencies; `uv add` changes dependency declarations and lock files.
- **Alembic** versions database schema changes; **SQLAlchemy** maps Python code to tables and queries. Neither substitutes for PostgreSQL itself.
- `\d table_name` inspects a PostgreSQL table and its FKs, constraints and indexes; `alembic current` displays the applied revision.
- `ruff check . --fix` edits source files: rerun tests afterward (22 passed after this run).

**Detailed learning commands and evidence:** `docs/phases/phase-1-command-reference.md`.

## 7. Project files (observed in Git status and user-provided code/output)

- `backend/app/core/config.py` — existing Pydantic settings extended with database URL.
- `backend/app/db/base.py` — declarative SQLAlchemy base.
- `backend/app/db/session.py` — engine, sessionmaker and session dependency.
- `backend/app/models/` — 16 frozen-domain SQLAlchemy models registered with Alembic metadata.
- `alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/` — Alembic configuration and 15 sequential migration files through `926cf9047962`.
- `backend/app/db/seed.py` — deterministic, atomic fictional operational seed loader.
- `backend/tests/test_database.py`, `test_database_constraints.py`, `test_transaction_rollback.py`, and `test_seed_data.py` — isolated PostgreSQL validation.
- `docs/phases/phase-1-command-reference.md` — separate beginner-oriented commands and observed output.
- `docs/phases/phase-1-database-foundation.md` — this technical and progress document.

User's `git status --short` showed application/config/dependency files modified and the above Phase 1 additions untracked. Do not assume changes are committed or pushed. Verify `.env` and other secrets remain excluded at staging time.

## 8. Architecture revision notes and next actions

### 8.1 Batch implementation completed 2026-10-25

`backend/app/db/seed.py` owns the Phase 1 operational seed fixture. Its fixed
UTC timestamp, stable natural keys, reserved `.test` email addresses, and
fictional names make the dataset reproducible and visibly non-production. The
loader uses PostgreSQL upserts where schema uniqueness exists and explicit
existence checks for subscriptions and ticket events. It never deletes,
truncates, or resets records, and the command runs in one transaction so a
failure cannot leave a partially loaded dataset.

The PostgreSQL test layer is split by responsibility:

- `backend/tests/db_safety.py` rejects missing URLs, non-PostgreSQL URLs, URL
  database names other than `telecom_test_db`, and connections whose actual
  database name differs.
- `backend/tests/conftest.py` supplies per-test transactions, unconditional
  rollback cleanup, engine disposal, and an Alembic-head precondition.
- `backend/tests/test_database_constraints.py` verifies unique, foreign-key,
  subscription-status, and ticket-priority constraints. Expected failures are
  isolated in nested transactions/savepoints.
- `backend/tests/test_transaction_rollback.py` writes an application row,
  rolls back, then verifies through a new connection that it did not persist.
- `backend/tests/test_seed_data.py` verifies the five seeded entity groups,
  fictional email convention, relationships, and unchanged counts after a
  second load.

The explicit seed command and all operational commands are recorded in
`docs/phases/phase-1-command-reference.md`. `.env.example` documents separate
development and test URLs without credentials.

### 8.2 Validation snapshot

| Command/check | Actual result on 2026-10-25 |
|---|---|
| Ruff lint | PASSED — all checks passed |
| Ruff format check | PASSED — 55 files already formatted |
| Backend suite with `TEST_DATABASE_URL` | PASSED — 29 tests in 0.38s |
| Alembic current | PASSED — `926cf9047962 (head)` |
| Alembic heads | PASSED — one head, `926cf9047962` |
| Alembic check | PASSED — no new upgrade operations detected |

An initial sandboxed PostgreSQL connection attempt failed with a local-socket
permission error. The same commands were then executed with approved local
database access and produced the results above. One first rollback-test run
found that its generated probe exceeded the schema's 30-character customer
number limit; the probe was corrected and the complete suite then passed.

### 8.3 Acceptance closure and limitations

- `docs/db/postgresql-runtime-role.sql` now documents and implements the
  administrator-run least-privilege runtime-role policy without embedded
  credentials. Runtime role provisioning remains a deployment/manual action.
- A guarded runner upgraded, downgraded, re-upgraded, and checked all migrations
  in `telecom_migration_test_db`; the disposable database was then removed.
- Seed idempotency is transactionally safe for normal serial command use. The
  subscription and event tables lack seed-specific natural-key constraints, so
  simultaneous seed processes are not claimed to be race-proof.
- Seed data is a compact operational fixture, not a production-sized dataset.
- Authentication, authorization, approval enforcement, Qdrant/RAG, MCP,
  LangGraph, Deep Agents, evaluation execution, Docker, and deployment remain
  assigned to later frozen phases.

Phase 1 acceptance is **DONE**. The schema, fictional seeds, isolated database
tests, migration lifecycle, security configuration, and documentation satisfy
the recorded frozen completion evidence. Production credential provisioning
remains environment/deployment work and does not place secrets in this phase.

1. **PostgreSQL** holds operational facts, identities, support tickets and approval records. **Qdrant** is reserved for later unstructured knowledge ingestion.
2. **Psycopg** is the driver; **SQLAlchemy** manages mapped classes and database sessions; `Base.metadata` describes models; **Alembic** produces reviewed schema migrations.
3. `backend/alembic/env.py` uses Pydantic database settings and `Base.metadata`, with imports registering all 16 tables. An example `.env` URL for local peer/default authentication is `postgresql+psycopg:///telecom_db`; do not copy credentials into tracked files.
4. **Revision vs upgrade:** `uv run alembic revision --autogenerate -m "..."` generates a file; inspect it before `uv run alembic upgrade head`, which changes the database. `uv run alembic current` checks applied revision.
5. **Naming convention:** Give new constraints stable names (or centrally configure SQLAlchemy naming conventions in a planned revision). Do not blindly re-autogenerate or edit past deployed revisions.
6. **Testing limitation:** The 29 passing tests cover current regressions, isolated connectivity, selected FK/check/unique constraints, rollback, and seed repeatability. They do not prove role-based authorization, migration reversibility, concurrent seed serialization, or secure production runtime behavior.

**Later work:** Provision the documented runtime role in each deployment environment, assess later MCP-owned telecom service facts, and commit/push only when the user chooses.

**Next phase boundary:** Continue Qdrant/RAG work without moving transactional operational data out of PostgreSQL.

**Overall:** Phase 0 **DONE**; Phase 1 **DONE**; later phase status is tracked in `docs/phase-tracker.md`.
