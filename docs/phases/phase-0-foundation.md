# Phase 0 — Project Foundation

**Status:** DONE  
**Project:** `telecom-agentic-ai-support`  
**Architecture authority:** *Telecom Agentic AI Support Platform — Frozen Project Documentation*, v1.0 (2026-10-20), especially Sections 15, 20, and 21.

## Exact frozen Phase 0 scope

> Repository structure, environment, React/Vite, FastAPI skeleton, configuration.

**Frozen completion evidence:** project boots locally; health endpoint and React shell work.

The global Definition of DONE additionally requires implementation, automated tests, applicable evaluations/safety checks, documented configuration and contracts, integrated application behavior, recorded limitations, and updated project/phase documentation.

## Locked decisions

- New repository; do not alter the prior Telecom RAG chatbot.
- Frontend: **React + Vite**.
- Backend: **FastAPI + Pydantic**.
- Keep later frozen components (LangGraph, LangChain, Deep Agents, MCP servers/Gateway, PostgreSQL, Qdrant, RAGAS) in their assigned phases.
- Manage Python using the user's existing `uv` project/virtual environment.
- Do not commit secrets; use ignored `.env` and tracked `.env.example` templates.



## Completed work / evidence to date

- [x] Reviewed the frozen project documentation and proposed the Phase 0 design.
- [x] Inspected the prior Telecom RAG archive as a read-only source of reference ideas/data, without modifying it.
- [x] Confirmed `uv 0.9.26` and uv's `.venv/bin/python3` interpreter from shared terminal output.
- [x] Confirmed initial `uv tree` had no third-party dependencies; subsequently verified 32 resolved packages with runtime and development dependencies.
- [x] Confirmed initial Git `main` was empty; subsequently verified commits `6533a2d` and `1787344` pushed to private GitHub.
- [x] Confirmed expected Phase 0 backend/frontend/docs directories exist from shared `find` output.
- [x] Reviewed user-pasted `pyproject.toml` (`requires-python = ">=3.13"`) and `.gitignore` contents.
- [x] Confirmed Phase 0 documentation files exist; final closure edits appear as three modified docs in `git status --short` and pass `git diff --check`.
- [x] Created and locally started the FastAPI application; `/docs` and `/openapi.json` returned HTTP 200.
- [x] Implemented `/health` and `/ready`; both returned HTTP 200 with expected response bodies.
- [x] Ran four automated API tests successfully after fixing the Python import path.
- [x] Frontend React + Vite shell and frontend-to-backend integration manually verified (Ready → Unavailable → Ready).
- [x] Backend lint/format passed (14 Python files); combined regression suite passed: 21 tests (11 configuration, 4 CORS, 6 health/readiness).
- [x] Readiness HTTP 503 failure-path and health/readiness separation verified with automated tests.
- [x] Step 7.5.5: Starlette/HTTPX warning investigated and resolved in the verified development environment; 21 tests pass with zero warnings.
- [x] Scoped repository security checks, README review, documentation synchronization in Cursor, initial Git commits, and Phase 0 acceptance review completed.
- [x] Phase 0 accepted as DONE on 2026-10-21; closure commits `2c90b55` and `3a23b89` pushed; clean working tree verified.



## Implemented Phase 0 API contracts

- `GET /health` — process liveness. Verified `200 {"status":"healthy"}`.
- `GET /ready` — application-level readiness for the Phase 0 workload. Verified `200` ready and `503` not ready. Do not invent checks for databases/tools not yet implemented.
- All future public application APIs are under `/api/v1` according to the frozen document; health endpoints are explicit exceptions.



## Proposed implementation sequence

1. Document repo setup and command history.
2. Install backend dependencies via `uv` after reviewing package choices.
3. Create FastAPI app factory, settings, health/readiness routes, typed schemas.
4. Test FastAPI endpoints and settings.
5. Scaffold React + Vite frontend, create lightweight status shell, test/build.
6. Verify frontend ↔ backend communication and OpenAPI docs.
7. Run lint/tests/build/security checks; document findings and limitations.
8. Mark DONE only after acceptance criteria are met.



## Current limitations

- Git history is maintained locally and on the user-confirmed private GitHub remote: verified commits `6533a2d` and `1787344`. Closure documentation was published in commits `2c90b55` and `3a23b89`; the working tree was clean after the final push.
- Backend has 21 passing automated tests; frontend has 5 passing component tests, clean ESLint, and a passing production build. Local React ↔ FastAPI Ready/Unavailable/Recovery scenarios have been manually validated. These component tests mock the API utility, so they do not replace a full end-to-end test suite.
- Configuration loading/override was verified in the initial steps; Git ignore rules for both local `.env` files, frontend dependencies and build output were later verified with `git check-ignore -v`.
- Readiness HTTP 503 is covered by tests; the `app.state.is_ready` flag is initialized to `True` and does not detect unavailable dependencies automatically. The former Starlette/HTTPX test-client warning was resolved in Step 7.5.5 by installing HTTPX2 2.15.1 as a development dependency; compatibility beyond the 21 current tests is not yet established.
- No PostgreSQL, Qdrant, MCP, LangGraph, or LLM service is configured in Phase 0.



## Learning notes

Refer to `docs/command-reference.md` for exact commands, purpose, and observed outputs. Update that reference after each implementation step.

## Phase 0 — File Creation and Implementation Log



### Step 1 — Initial project files


| File                        | Purpose                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------- |
| `pyproject.toml`            | Python project metadata and dependency declarations                                |
| `uv.lock`                   | Locked Python dependency versions                                                  |
| `.python-version`           | Preferred Python version for the project                                           |
| `.gitignore`                | Excludes secrets, virtual environments, generated files, and other local artifacts |
| `README.md`                 | Main project overview and setup instructions                                       |
| `main.py` (repository root) | Initial file generated by `uv init`; not our FastAPI entry point                   |


These files existed before our Phase 0 implementation steps.

### Step 2 — Project directories and documentation


| Path                      | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| `backend/app/`            | Backend application source code                     |
| `backend/app/api/routes/` | FastAPI route definitions                           |
| `backend/app/core/`       | Application configuration and shared infrastructure |
| `backend/app/schemas/`    | Pydantic request and response schemas               |
| `backend/tests/`          | Automated backend tests                             |
| `frontend/`               | React and Vite application                          |
| `docs/architecture/`      | Architecture decisions and technical design         |
| `docs/phases/`            | Phase-specific implementation documentation         |


Documentation files:

- `docs/command-reference.md`
- `docs/phase-tracker.md`
- `docs/phases/phase-0-foundation.md`



### Step 3 — Dependency files


| File                   | Purpose                                                 |
| ---------------------- | ------------------------------------------------------- |
| `requirements.txt`     | Initial runtime dependency list                         |
| `requirements-dev.txt` | Initial development dependency list                     |
| `pyproject.toml`       | Updated automatically by uv to register dependencies    |
| `uv.lock`              | Updated automatically by uv to lock dependency versions |


**Decision:** `pyproject.toml` and `uv.lock` remain the authoritative dependency files. Requirements files should be kept synchronized or generated from uv when needed.

### Step 4 — FastAPI application

**File:** `backend/app/main.py`

**Responsibility:**

- Create the FastAPI application.
- Configure API metadata.
- Register API routers.
- Expose the ASGI application to Uvicorn.

**Important concepts:**

- FastAPI
- ASGI
- Application factory pattern
- OpenAPI documentation
- Router registration

**Validation observed:**

- Uvicorn application startup successful.
- Swagger UI returned HTTP 200.
- OpenAPI schema returned HTTP 200.



### Step 5 — Health and readiness endpoints

**Files:**


| File                               | Responsibility                                  |
| ---------------------------------- | ----------------------------------------------- |
| `backend/app/schemas/health.py`    | Pydantic health and readiness response models   |
| `backend/app/api/routes/health.py` | `/health` and `/ready` endpoint implementations |
| `backend/app/main.py`              | Updated to register the health router           |


**Important concepts:**

- `BaseModel` — typed response schema
- `Literal` — restricts allowed values
- `APIRouter` — groups related API routes
- `response_model` — validates and documents API responses
- Liveness — application process responsiveness
- Readiness — ability to handle supported requests

**Validation:**

- Health response: PASS — HTTP 200 and expected JSON confirmed with `curl`.
- Readiness response: PASS — HTTP 200 and expected JSON confirmed with `curl`.
- Swagger/OpenAPI route registration: PASS — confirmed by automated test; current browser view not separately rechecked.
- Historical initial endpoint test count: 4 PASSED; Step 7.5.4 later added 2 negative-state tests, bringing this file to 6 PASSED.



### File documentation rule for future steps

For every important file created or modified, record:

1. File path and name.
2. Why the file is needed.
3. Important functions, classes, and components.
4. How it connects to other files.
5. Relevant architecture decisions.
6. Commands used to create or test it.
7. Actual validation results.
8. Known limitations or pending improvements.

Update results only after they have been verified.

### Step 5 — Health and Readiness Validation Results

**Validation date:** 20 October 2026

**Files implemented:**

- `backend/app/main.py`
- `backend/app/api/routes/health.py`
- `backend/app/schemas/health.py`

**Commands executed:**

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

**Observed results:**


| Endpoint      | HTTP status | Response                                           | Result |
| ------------- | ----------- | -------------------------------------------------- | ------ |
| `GET /health` | 200         | `{"status":"healthy"}`                             | PASS   |
| `GET /ready`  | 200         | `{"status":"ready","checks":{"application":"ok"}}` | PASS   |


**Technical notes:**

- Liveness confirms the application can respond to requests.
- Readiness currently reports application-level status only.
- Pydantic models define the response contracts.
- The FastAPI router separates endpoint implementation from application initialization.

**Remaining validation:**

- Four original success/schema/OpenAPI tests passed; Step 7.5.4 subsequently verified the controlled not-ready HTTP 503 response with two new tests.
- Verify current Swagger UI displays both routes.

**Status:** Initial manual and four automated tests PASSED. Readiness failure-path validation was subsequently completed in Step 7.5.4; remaining Phase 0 validation PENDING.

### Step 6 — Automated tests and import-path troubleshooting

**Validation date:** 20 October 2026

**File created:** `backend/tests/test_health.py`, containing four tests for liveness, readiness, JSON content type, and OpenAPI route presence.

**First attempt:**

```bash
uv run pytest backend/tests/test_health.py -v
```

**Observed:** Test collection failed with `ModuleNotFoundError: No module named 'backend'`; zero tests were executed.

**Resolution:** Added explicit `__init__.py` package marker files and configured pytest in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["."]
```

**Retest command:**

```bash
uv run pytest backend/tests/test_health.py -v
```

**Observed:** Four tests collected, four PASSED, zero failed. A `StarletteDeprecationWarning` about `httpx` versus `httpx2` remained. Investigate compatibility before declaring Phase 0 DONE; do not change packages without confirming the compatible approach.

**Remaining checks:** A negative HTTP 503 readiness test and dependency compatibility review. Ruff lint and format checks subsequently PASSED.

**Learning notes:** Python import paths, package initialization, pytest collection versus test failures, FastAPI `TestClient`, assertions, and OpenAPI contract checks.

### Step 6 — Code Quality and Regression Testing

**Files checked:**
- `backend/app/main.py`
- `backend/app/api/routes/health.py`
- `backend/app/schemas/health.py`
- `backend/tests/test_health.py`
- Python package initialization files

**Commands:**
```bash
uv run ruff check backend
uv run ruff format --check backend
uv run ruff format backend
uv run pytest backend/tests/test_health.py -v
```

**Verified results:**
- Initial lint check: PASSED
- Initial formatting check: 4 files required formatting
- Automated test rerun: 4 PASSED, 1 warning

**Pending confirmation:**
- Readiness HTTP 503 test.
- Starlette/HTTPX compatibility warning review.

**Technical concepts learned:**
- Python linting
- Code formatting
- Automated regression testing
- pytest test discovery and execution
- Third-party dependency warnings

**Phase status:** IN PROGRESS
- Final Ruff lint check: PASSED
- Final Ruff formatting check at Step 6: PASSED (11 files formatted); Step 7.3: PASSED (12 files formatted)
- Backend automated tests: PASSED (4 tests)
- Documentation files: Verified
- Readiness failure-path testing: subsequently PASSED in Step 7.5.4
- Starlette/HTTPX warning review: PENDING

### Step 7.1 — Centralized Application Configuration

**Date:** 20 October 2026

**File created:** `backend/app/core/config.py`

**Purpose:** Centralize application configuration using Pydantic Settings instead of hardcoding environment-specific settings throughout the application.

#### Important components

| Component | Responsibility |
|---|---|
| `Settings(BaseSettings)` | Loads and validates application settings |
| `SettingsConfigDict` | Configures environment-file loading |
| `Literal` | Restricts values to permitted options |
| `Field` | Defines validation constraints and defaults |
| `default_factory` | Creates a default value when a model is instantiated |
| `get_settings()` | Provides a reusable configuration accessor |
| `@lru_cache` | Caches the Settings instance |

#### Configuration fields

| Field | Default |
|---|---|
| `app_name` | Telecom Agentic AI Support Platform |
| `app_env` | development |
| `app_debug` | false |
| `api_v1_prefix` | /api/v1 |
| `backend_host` | 127.0.0.1 |
| `backend_port` | 8000 |
| `cors_origins` | http://localhost:5173 |

#### Architecture decision

Application configuration is centralized, typed, and environment-driven.

Secrets must not be hardcoded, printed in logs, or committed to Git.

#### Validation results

- Configuration import: PASSED
- Configuration JSON output: PASSED
- Initial Ruff lint check: PASSED
- Initial Ruff formatting check: 1 file required formatting
- Final formatting verification: PASSED

#### Remaining work

- Final Ruff formatting verified: 12 files already formatted at Step 7.3.
- `.env.example` and local `.env` created (user-reported); environment loading, overrides, and Git-ignore checks passed according to user confirmation (exact terminal output not shared).
- Invalid configuration tests completed in Step 7.5.3: eight invalid cases rejected.
- Settings integrated with FastAPI in Step 7.3 (user-reported, regression tested).

### Step 7.2 — Environment Configuration Files

**Files created:**

| File | Responsibility |
|---|---|
| `.env.example` | Version-controlled template containing safe example settings |
| `.env` | Local, Git-ignored runtime configuration |

**Architecture decision:** Separate environment configuration from application code. Use Pydantic Settings for type validation and environment overrides.

**Security:** The `.env` file must not be committed to Git. Secrets must not be exposed in browser-side configuration.

**Validation commands:**

```bash
cp .env.example .env
uv run python -c "from backend.app.core.config import get_settings; s = get_settings(); print(s.app_env, s.backend_port, s.cors_origins)"
BACKEND_PORT=9000 uv run python -c "from backend.app.core.config import get_settings; print(get_settings().backend_port)"
git check-ignore .env
git check-ignore .env.example
git status --short --untracked-files=all
```

**Actual validation results (user-confirmed):**
- Settings loading returned the expected development environment, port 8000, and local frontend origin — PASS (user-reported).
- `BACKEND_PORT=9000` returned 9000 — PASS (user-reported).
- `git check-ignore .env` identified `.env` — PASS (user-reported).
- `git check-ignore .env.example` produced no output — PASS (user-reported).
- Exact terminal transcripts and the latest `git status` were not supplied; no commit has been verified.

**Security interpretation:** Ignore rules reduce accidental Git tracking but are not proof that a secret has never been committed. Do not publish `.env`.

**Next:** Complete invalid-settings tests and verify CORS integration in later Phase 0 substeps.

## Step 7.3 — Integrating Pydantic Settings with FastAPI

**Validation date:** 20 October 2026  
**Modified file:** `backend/app/main.py`

### Implementation and design

- `create_app(settings: Settings | None = None)` supports an explicit settings instance for isolated tests.
- In the absence of an argument, `get_settings()` supplies cached validated settings.
- FastAPI receives `title=settings.app_name` and `debug=settings.app_debug`.
- `app.state.settings = settings` makes application configuration available to backend components.
- Health and readiness router registration is preserved.

**Architecture decision:** Use dependency-injectable application configuration rather than hardcoded environment-specific settings. Do not expose secrets from application state to clients.

### Commands executed / verification

```bash
uv run python -c "from backend.app.main import create_app; print(create_app().title)"
uv run python -c "from backend.app.main import create_app; from backend.app.core.config import Settings; app = create_app(Settings(app_name='Telecom Test Application', app_env='testing')); print(app.title, app.state.settings.app_env)"
uv run pytest backend/tests/test_health.py -v
uv run ruff check backend
uv run ruff format --check backend
```

| Check | Actual or reported result | Evidence status |
|---|---|---|
| Default application title | User reported completing the verification | Completed (user-reported; output not supplied) |
| Custom Settings injection | User reported completing the verification | Completed (user-reported; output not supplied) |
| API regression tests | 4 passed, 1 warning in 0.21s | Verified from supplied terminal output |
| Ruff lint | `All checks passed!` | Verified from supplied terminal output |
| Ruff formatting | `12 files already formatted` | Verified from supplied terminal output |
| Starlette/HTTPX compatibility | `StarletteDeprecationWarning` concerning `httpx`/`httpx2` | Review pending |

### Technical revision notes

- An **application factory** constructs and configures the FastAPI instance.
- **Dependency injection** lets tests provide custom settings without altering shared environment files.
- `app.state.settings` holds application-level configuration; it is not a public API response.
- **Regression tests** show the previously tested endpoints continue to behave as expected after the change.
- A passing test suite does not establish readiness failure-path correctness or complete configuration validation.

**Step 7.3 status:** Implementation reported complete; regression, lint, and formatting checks verified.

**Step 7.4 — CORS Configuration:** COMPLETED (manual validation user-reported; final Ruff checks verified).

- CORS middleware integrated with FastAPI using configured React/Vite development origins.
- Allowed and disallowed origins, plus OPTIONS preflight, manually validated (user-reported).
- Ruff lint: PASSED (`All checks passed!`).
- Ruff formatting: PASSED (`12 files already formatted`); one file was reformatted.
- Automated CORS tests: PASSED — four tests passed before and after formatting (post-format: 0.16s, one compatibility warning).

**Current next step:** React/Vite frontend setup and validation under Phase 0. Readiness HTTP 503 was verified in Step 7.5.4 and the test-client warning was resolved in Step 7.5.5; React + Vite, integration, security and final validation remain before Phase 0 DONE.

**Overall Phase 0 status: IN PROGRESS. Phase 1: PENDING.**

### Step 7.4 — CORS Configuration for React + Vite

**Date:** 20 October 2026

**Modified file:** `backend/app/main.py`

**Purpose:** Configure FastAPI to allow cross-origin browser requests from approved React frontend origins.

#### Implementation details

- Imported `CORSMiddleware` from FastAPI.
- Registered CORS middleware using `app.add_middleware()`.
- Loaded allowed origins from `Settings.cors_origins`.
- Configured `allow_credentials=False`.
- Restricted cross-origin methods to `GET` for the current Phase 0 endpoints.
- Configured `allow_headers=["Content-Type"]`.

#### Architecture decision

CORS configuration is environment-driven through Pydantic Settings.

The approved development origin is `http://localhost:5173`.

CORS is not a substitute for authentication or authorization. Future API methods and browser authentication requirements will be reviewed when their corresponding features are implemented.

#### Manual validation

| Validation | Expected behavior | Result |
|---|---|---|
| Allowed origin | HTTP 200 and matching Access-Control-Allow-Origin header | PASS — user-reported |
| Disallowed origin | No Access-Control-Allow-Origin header authorizing the origin | PASS — user-reported |
| OPTIONS preflight | HTTP 200 and GET permitted for approved origin | PASS — user-reported |
| Existing API regression tests | Four existing tests pass | PASS — user-reported |
| Ruff lint | No configured lint violations | PASS — user-reported |
| Initial Ruff format check | Identify formatting differences | One file requires formatting |

#### Formatting issue

Ruff identified an extra blank line at the beginning of `backend/app/main.py`.

**Correction command:**

```bash
uv run ruff format backend/app/main.py
```

**Final verification commands:**

```bash
uv run ruff check backend
uv run ruff format --check backend
```

**Final formatting verification:** PASSED

- Formatting correction: `1 file reformatted`
- Ruff lint: `All checks passed!`
- Ruff formatting: `12 files already formatted`
- Step 7.4 manual CORS validation: PASSED (user-reported)
- Automated CORS tests: PASSED — four tests passed before and after formatting (post-format: 0.16s, one compatibility warning)

#### Technical concepts learned

- CORS (Cross-Origin Resource Sharing)
- Same-origin policy
- FastAPI middleware
- Allowed and disallowed origins
- OPTIONS preflight requests
- Environment-driven security configuration
- Least-privilege configuration

#### Remaining work

- Post-format automated CORS regression verified: 4 tests passed in 0.16s (one existing compatibility warning).
- Automated Pydantic Settings positive-case tests completed in Step 7.5.2.
- Invalid configuration tests passed in Step 7.5.3; readiness failure behavior was verified in Step 7.5.4.

**Historical next:** Step 7.5.5 — Starlette/HTTPX Dependency Warning Review (completed).

**Overall Phase 0 status:** IN PROGRESS.


### Step 7.5.1 — Automated CORS Tests and Formatting

**Date:** 20 October 2026  
**New file:** `backend/tests/test_cors.py`

**Purpose:** Automatically verify the existing Phase 0 CORS policy for allowed origins, disallowed origins, permitted GET preflight, and rejected POST preflight. The tests use FastAPI `TestClient` and application-factory-injected test settings. These tests verify browser CORS response policy, not authentication or authorization.

**Commands and observed outcomes:**

```bash
uv run pytest backend/tests/test_cors.py -v
# 4 passed, 1 warning in 0.17s

uv run ruff check backend
# All checks passed!

uv run ruff format --check backend
# 1 file would be reformatted, 12 files already formatted

uv run ruff format --diff backend/tests/test_cors.py
# Proposed removal of a leading blank line and simplification of two assert statements

uv run ruff format backend/tests/test_cors.py
# 1 file reformatted

uv run ruff check backend
# All checks passed!

uv run ruff format --check backend
# 13 files already formatted
```

**Test results (before formatting; all four also passed after formatting):**

| Test | Result |
|---|---|
| `test_allowed_origin` | PASSED |
| `test_disallowed_origin` | PASSED |
| `test_allowed_get_preflight` | PASSED |
| `test_disallowed_post_preflight` | PASSED |

**Compatibility warning:** `StarletteDeprecationWarning` states that using `httpx` with `starlette.testclient` is deprecated and recommends `httpx2`. The warning did not fail these tests. Package compatibility review remains pending; no dependency change has been approved or made for this warning.

**Formatting resolution:** Ruff reformatted `test_cors.py` by removing a leading blank line and simplifying two multi-line assertions. Both final lint and formatting checks PASSED. The test file was retested successfully after formatting.

**New concepts studied:** CORS testing with `TestClient`, positive/negative assertions, test-specific configuration injection, OPTIONS preflight, linting versus formatting, regression-test sequencing.

**Post-format regression verification — PASSED:** `uv run pytest backend/tests/test_cors.py -v` collected 4 tests; all 4 PASSED, 0 failed, with 1 existing `StarletteDeprecationWarning`, in 0.16s. This confirms the formatting change did not break the CORS tests.

**Historical next:** Step 7.5.3 — Invalid Configuration Validation Tests; both invalid configuration and readiness HTTP 503 testing have now passed. Dependency warning review remains pending. React/Vite and integrated checks remain part of Phase 0.

**Overall Phase 0 status: IN PROGRESS. Phase 1: PENDING.**


### Step 7.5.2 — Automated Pydantic Settings Tests and Formatting

**Date:** 20 October 2026  
**New file:** `backend/tests/test_config.py`  
**Status:** DONE — implementation, validation, and documentation recorded.

**Purpose:** Verify Pydantic Settings defaults, environment-variable overrides, and the FastAPI application factory's use of explicitly injected settings. Positive-case coverage was extended by the negative input cases in Step 7.5.3.

**Automated tests:**

| Test | Purpose | Result |
|---|---|---|
| `test_default_settings` | Confirm expected development defaults, port 8000, API prefix, and Vite CORS origin | PASSED |
| `test_environment_variable_overrides` | Confirm environment overrides for app environment, debug flag, port, and CORS origins | PASSED |
| `test_custom_settings_injected_into_app` | Confirm custom title/debug settings and object identity in `app.state.settings` | PASSED |

**Commands and actual results (terminal output shared):**

```bash
uv run pytest backend/tests/test_config.py -v
# Initial run: 3 passed in 0.20s, no warnings

uv run ruff check backend
# All checks passed!

uv run ruff format --check backend
# 1 file would be reformatted, 13 files already formatted

uv run ruff format --diff backend/tests/test_config.py
# Extra leading blank line before 'import pytest' identified

uv run ruff format backend/tests/test_config.py
# 1 file reformatted

uv run ruff check backend
# All checks passed!

uv run ruff format --check backend
# 14 files already formatted

uv run pytest backend/tests/test_config.py -v
# Post-format regression: 3 passed in 0.20s, no warnings
```

**Technical revision notes:** `@pytest.fixture` centralizes per-test setup; `monkeypatch.delenv()` removes relevant environment overrides temporarily, and `monkeypatch.setenv()` supplies test overrides. `_env_file=None` disables reading `.env` for that Settings instance. `get_settings.cache_clear()` prevents cached settings from leaking between tests; a teardown cache clear restores isolation. Application-factory injection makes configuration independently testable without changing production configuration.

**Validation boundary:** This run does not test malformed configuration, all possible external environment variables, readiness HTTP 503, or the full backend test suite. The previously observed Starlette/HTTPX warning remains open for separate review, even though it did not appear in these three configuration tests.

**Historical next:** Step 7.5.4 — Readiness HTTP 503 Failure-Path Testing (now completed). React/Vite and frontend/backend integration remain pending Phase 0 deliverables.

**Overall Phase 0 status: IN PROGRESS. Phase 1: PENDING.**


### Step 7.5.3 — Invalid Configuration Validation Tests

**Date:** 20 October 2026  
**Status:** DONE — implementation, focused and full-file tests, code quality, and documentation recorded.  
**Modified file:** `backend/tests/test_config.py` (existing Step 7.5.2 test file; not replaced).

**Purpose:** Verify Pydantic Settings rejects invalid backend ports and unsupported environment names with `pydantic.ValidationError`. These are *negative tests* complementing the three existing successful-configuration tests.

#### Added automated coverage

| Parameterized test | Tested invalid values | Verified result |
|---|---|---|
| `test_invalid_backend_port_is_rejected` | `0`, `-1`, `65536`, `70000` | 4 PASSED |
| `test_invalid_app_environment_is_rejected` | `"invalid"`, `"staging"`, `"Development"`, `""` | 4 PASSED |
| Existing defaults/override/injection cases | 3 existing tests | 3 PASSED |

Each negative test uses `pytest.mark.parametrize`, `pytest.raises(ValidationError)`, and asserts that the error location (`error["loc"]`) matches the intended field (`backend_port` or `app_env`). Tests instantiate `Settings(_env_file=None)` using the existing environment-cleanup fixture.

#### Commands and verified results

```bash
uv run pytest backend/tests/test_config.py::test_invalid_backend_port_is_rejected -v
# 4 passed in 0.18s; no warnings

uv run pytest backend/tests/test_config.py::test_invalid_app_environment_is_rejected -v
# 4 passed in 0.17s; no warnings

uv run pytest backend/tests/test_config.py -v
# Before Ruff fixes: 11 passed in 0.18s; no warnings

uv run ruff check backend
# I001 in backend/tests/test_config.py: import block unsorted

uv run ruff format --check backend
# 1 file would be reformatted; 13 files already formatted

uv run ruff check --fix backend/tests/test_config.py
# Found 1 error (1 fixed, 0 remaining)

uv run ruff format backend/tests/test_config.py
# 1 file reformatted

uv run ruff check backend
# All checks passed!

uv run ruff format --check backend
# 14 files already formatted

uv run pytest backend/tests/test_config.py -v
# Post-correction regression: 11 passed in 0.18s; no warnings
```

#### Architecture and learning notes

- **Fail-fast validation:** Pydantic rejects invalid configuration when Settings is constructed rather than allowing invalid values to propagate.
- `Field(ge=1, le=65535)` enforces the allowed backend port range.
- `Literal["development", "testing", "production"]` restricts application environments; case differences are not accepted.
- `pytest.mark.parametrize` generates four test cases per function without duplicated test code.
- `pytest.raises(ValidationError)` verifies rejection; inspecting error locations checks that rejection is caused by the expected field.
- Ruff rule `I001` identified third-party imports separated incorrectly; `ruff check --fix` organized imports, then `ruff format` fixed the remaining blank line.
- The full configuration test file was rerun after edits; all 11 cases PASSED.

**Validation boundary (at Step 7.5.3):** Not every possible invalid field or external environment condition was tested. Subsequently, Step 7.5.4 verified the combined backend suite and readiness HTTP 503 behavior. Starlette/HTTPX compatibility warning, React/Vite frontend and end-to-end validation remain pending. No changes were made to Pydantic production constraints, dependencies, or the frozen architecture.

**Historical next:** Step 7.5.4 — Readiness HTTP 503 Failure-Path Testing (now completed). **Current next:** Phase 0 React/Vite frontend work (when requested).

**Overall Phase 0 status: IN PROGRESS. Phase 1: PENDING.**


### Step 7.5.4 — Readiness HTTP 503 Failure-Path Testing

**Date:** 20 October 2026  
**Status:** DONE — implementation, targeted tests, full regression, linting/formatting, and documentation recorded.

#### Files modified and responsibilities

| File | Change | Why |
|---|---|---|
| `backend/app/main.py` | Initialize `app.state.is_ready = True` in `create_app()` | Preserve the initial ready state and permit controlled application-level readiness changes |
| `backend/app/api/routes/health.py` | Inject `Request`, read `request.app.state.is_ready`, emit readiness check/status | Support structured HTTP 503 when application is marked not ready |
| `backend/tests/test_health.py` | Add 2 tests for HTTP 503 readiness and independent HTTP 200 liveness | Verify both failure-path contract and liveness/readiness distinction |

**API contracts verified:** With the flag `True`, `GET /ready` returns HTTP 200 and `{"status":"ready","checks":{"application":"ok"}}`. When explicitly set to `False` in an isolated application, `GET /ready` returns HTTP 503 and `{"status":"not_ready","checks":{"application":"not_ready"}}`; `GET /health` continues returning HTTP 200 with `{"status":"healthy"}`.

#### Commands and observed results

```bash
uv run pytest backend/tests/test_health.py::test_readiness_returns_503_when_application_not_ready backend/tests/test_health.py::test_health_remains_healthy_when_application_not_ready -v
# 2 passed, 1 StarletteDeprecationWarning, in 0.24s

uv run pytest backend/tests -v
# Before formatting: 21 passed, 1 warning in 0.25s

uv run ruff check backend
# All checks passed!
uv run ruff format --check backend
# 1 file would be reformatted, 13 files already formatted

uv run ruff format --diff backend/app/api/routes/health.py
uv run ruff format backend/app/api/routes/health.py
# Formatting correction performed, followed by successful checks

uv run ruff check backend
# All checks passed!
uv run ruff format --check backend
# 14 files already formatted

uv run pytest backend/tests -v
# Post-format regression: 21 passed, 1 warning in 0.25s
```

**Test breakdown:** 11 configuration tests, 4 CORS tests, 6 health/readiness tests; 0 failures. The single `StarletteDeprecationWarning` concerns using `httpx` with `starlette.testclient`; compatibility review is scheduled for Step 7.5.5, with no dependency change yet.

#### Architecture decisions and limitations

- `Request` exposes `request.app.state` so readiness evaluates the application that received the request.
- The application-factory pattern keeps not-ready test state isolated from the running server.
- Liveness (`/health`) and readiness (`/ready`) serve different operational purposes.
- **Important limitation:** `app.state.is_ready` defaults to `True`; it is a manually controlled flag, not automatic startup, dependency, or shutdown monitoring. Future dependency checks must be implemented when their associated frozen phases are reached.
- No new PostgreSQL, Qdrant, MCP or other later-phase dependencies were introduced.

**Historical next:** Step 7.5.5 — Starlette/HTTPX Dependency Warning Review (now DONE). React/Vite frontend, integration and final Phase 0 acceptance remain PENDING.

**Overall Phase 0:** IN PROGRESS. **Phase 1:** PENDING.


## Step 7.5.5 — Starlette/HTTPX Dependency Warning Review

**Date:** 20 October 2026  
**Status:** DONE — root cause documented, development dependency added, regression and formatting verified, documentation updated.

### Problem and evidence

The previously passing 21-test backend suite emitted one `StarletteDeprecationWarning` stating that using `httpx` with `starlette.testclient` was deprecated and recommending `httpx2`. The user inspected installed metadata and Starlette's installed `testclient.py`: the module first attempts `import httpx2 as httpx`, falls back to `import httpx`, and emits the warning on fallback. Thus the warning originated at test-client import, not from failing FastAPI endpoints.

Before changes: FastAPI 0.151.0; Starlette 1.9.0; HTTPX 0.28.1; HTTPX2 absent. FastAPI's optional `standard` extra and Starlette's optional `full` extra list HTTPX2, while existing HTTPX satisfies the listed optional bounds. PyPI metadata queried by the user reported HTTPX2 2.15.1 supporting Python >=3.11, compatible with the project's Python 3.13.11. This checks Python-version compatibility, not every behavioral interaction.

### Dependency update

The user chose the established requirements-input workflow, updating `requirements-dev.txt` and reporting use of `uv add --dev -r requirements-dev.txt`. The corresponding development dependency group in user-shared `pyproject.toml` now includes:

```toml
[dependency-groups]
dev = [
    "httpx>=0.28.1",
    "httpx2>=2.0.0,<3.0.0",
    "pytest>=9.1.1",
    "ruff>=0.17.1",
]
```

`uv pip show httpx httpx2 starlette fastapi` independently confirmed **HTTPX2 2.15.1**, **HTTPX 0.28.1**, **Starlette 1.9.0**, and **FastAPI 0.151.0** installed. `uv add --dev -r requirements-dev.txt` registers inputs in `pyproject.toml`/`uv.lock`; direct inspection of the updated lockfile was not separately supplied. Retaining HTTPX avoids an unnecessary removal before broader compatibility review. The frozen FastAPI/Pydantic stack was preserved.

### Verified commands and results

```bash
uv pip show fastapi starlette httpx httpx2
# Initially: httpx2 absent; fastapi 0.151.0, starlette 1.9.0, httpx 0.28.1

uv run python -c "from importlib.metadata import requires; print('\n'.join(requires('fastapi') or []))"
uv run python -c "from importlib.metadata import requires; print('\n'.join(requires('starlette') or []))"
# Printed dependency constraints, including optional HTTPX2 requirements

uv run python -c "import inspect; from starlette.testclient import TestClient; print(inspect.getfile(TestClient))"
# Triggered prior warning; located .venv/.../starlette/testclient.py

sed -n '1,90p' .venv/lib/python3.13/site-packages/starlette/testclient.py
# Confirmed HTTPX2-first import, HTTPX fallback and warning

uv pip index versions httpx2
# Unsupported: unrecognized subcommand 'index' (no environment change)

uv pip list --outdated
# Displayed installed packages with available updates, not HTTPX2 availability

uv run python -c "import json, urllib.request; data = json.load(urllib.request.urlopen('https://pypi.org/pypi/httpx2/json', timeout=10)); print('Latest HTTPX2 version:', data['info']['version']); print('Requires Python:', data['info']['requires_python'])"
# Reported version 2.15.1, requires Python >=3.11

uv pip show httpx httpx2 starlette fastapi
# Confirmed HTTPX2 2.15.1 installed alongside unchanged versions

uv run python -W error::DeprecationWarning -c "from fastapi.testclient import TestClient; print('TestClient imported successfully without deprecation warnings')"
# Passed without deprecation warnings

uv run pytest backend/tests -v
# 21 passed in 0.20s; no warnings

uv run ruff check backend
# All checks passed!
uv run ruff format --check backend
# 14 files already formatted
```

**Technical revision notes:** Test dependencies are distinct from production dependencies. A package can be a valid optional dependency and still emit a deprecation warning when the preferred integration is unavailable. Inspect installed package metadata and source before changing dependencies; verify the preferred import path, then perform full regression and quality checks. The failed `uv pip index` command illustrates CLI-version differences: record the actual failure and choose a supported read-only check.

**Boundary:** This confirms the warning is resolved and the **current 21 backend tests** pass in the updated environment. It does not prove complete dependency compatibility or readiness for production deployment. No new application features, MCP services, vector stores or LLM dependencies were introduced.

**Historical next at Step 7.5.5:** React + Vite frontend implementation, subsequently completed in Steps 8.x. Current remaining work: final repository security review and Phase 0 acceptance. **Phase 0: IN PROGRESS. Phase 1: PENDING.**


## React beginner reference — Interactive create-vite setup and file origins

**Scope:** Phase 0 React + Vite frontend setup. **Historical evidence:** The selected React/JavaScript starter, generated files, and running frontend were confirmed. We do not have a verbatim transcript of the original interactive scaffolding prompts, so the example below explains their meaning without claiming exact prompt wording.

1. **Create the initial location:** `mkdir -p frontend` creates a folder only; no React files exist as a result of `mkdir`.
2. **Use the create-vite scaffolder:** The setup used create-vite interactively for a frontend named `frontend`, with **React** as the framework and **JavaScript** as the variant. An *equivalent new-project example* is `npm create vite@latest frontend -- --template react`. **Do not run this again in our existing frontend directory.**
3. **Understand the choices:** React is the UI framework; JavaScript gives `.jsx` React components without TypeScript; the generated project includes ESLint tooling (`eslint.config.js`, `npm run lint`). Interactive options can vary by version; ESLint does not necessarily appear as an independent prompt in every release.
4. **Understand what was generated:** Vite's starter provided `index.html`, `src/main.jsx`, demo `src/App.jsx`, `src/App.css`, `src/index.css`, `package.json`, `vite.config.js`, `eslint.config.js`, and starter assets. `main.jsx` renders `<App />` into the HTML root element.
5. **Install packages:** `npm --prefix frontend install` installs dependencies defined by `frontend/package.json` and creates/updates the npm lockfile.
6. **Run the app:** `npm --prefix frontend run dev` launches Vite; visit `http://localhost:5173/`. Stop with Ctrl+C. Run FastAPI in a second terminal with `uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000` to test API connectivity.
7. **Customize the starter:** We replaced the demo `App.jsx` and CSS with the telecom status shell; created `src/api/health.js` and safe `frontend/.env.example`/ignored `.env`; later added `src/App.test.jsx` and Vitest configuration. Neither these application-specific files nor our tests were generated by the initial create-vite scaffold.

**Key distinction:** create-vite **generates starter files**; `npm install` **installs dependencies**; `npm run dev` **runs the development server**; `npm run build` **generates production assets**. For full explanations, commands, and the distinction between verified and equivalent examples, see `docs/command-reference.md` → **Step 8.0**.

## Steps 8.1–8.6 — React + Vite foundation and FastAPI integration

**Validation recorded:** 21 October 2026. **Implementation and observed browser behavior: PASSED.**

### Created/modified files

| File | Responsibility |
|---|---|
| `frontend/package.json`, `frontend/package-lock.json` | React/Vite package scripts and locked JavaScript dependencies; later Vitest/Testing Library dev dependencies |
| `frontend/index.html`, `frontend/src/main.jsx` | React mounting point and application entry |
| `frontend/src/App.jsx` | Responsive status shell; backend status state, asynchronous checks, and manual refresh |
| `frontend/src/App.css`, `frontend/src/index.css` | Component and global styling, responsive layout, and status variants |
| `frontend/src/api/health.js` | Configured fetch wrapper for `/health` and `/ready`, 5-second timeout and HTTP error status propagation |
| `frontend/.env.example` | Safe public API base URL template; `frontend/.env` remains local and ignored |
| `frontend/vite.config.js` | React Vite plugin; subsequently extended for Vitest jsdom environment |

### Architecture and behavior

- Frozen frontend remains **React + Vite**; backend remains **FastAPI + Pydantic**.
- `VITE_API_BASE_URL` is a browser-visible configuration value, not a place for credentials. Development example: `http://127.0.0.1:8000`.
- `fetchHealth()` requests `GET /health`; `fetchReadiness()` requests `GET /ready`. Failed HTTP responses generate errors with an HTTP `status` property; request timeout is 5 seconds.
- `App.jsx` checks both endpoints with `Promise.allSettled`, displays Ready if both succeed with expected structured payloads, Not ready if liveness succeeds and readiness rejects with HTTP 503, and Unavailable otherwise.
- Refresh triggers a new pair of requests. A cleanup guard prevents obsolete effect executions from writing component state.
- Current `/ready` depends on an application-level flag initialized as `True`; it does **not** automatically check PostgreSQL, Qdrant, network connectivity or other not-yet-implemented services.
- The browser was observed to show Ready while FastAPI was running, Unavailable after stopping FastAPI and refreshing, and Ready again after restart. Refresh behavior was separately user-verified.

## Steps 8.7.A–8.7.I — Validation, security hygiene, and frontend tests

### Automated testing and build evidence

| Command | User-observed result | Status |
|---|---|---|
| `uv run pytest backend/tests -q` | **21 passed in 0.22s**, no warnings reported | PASSED |
| `uv run ruff check backend` | `All checks passed!` | PASSED |
| `uv run ruff format --check backend` | `14 files already formatted` | PASSED |
| `npm --prefix frontend run lint` | No ESLint errors reported | PASSED |
| `npm --prefix frontend run test` | Vitest 4.1.12, **5 passed** in 1 test file | PASSED |
| `npm --prefix frontend run build` | Vite 8.3.4, **18 modules transformed**, build completed in 106ms | PASSED |
| `uv lock --check` | `Resolved 36 packages in 23ms` | PASSED |
| `npm --prefix frontend ls --depth=0` | Direct dependency listing completed without errors | PASSED |
| `git status --short --untracked-files=all` | New project source/docs and lockfiles listed as `??`, no commit established | REVIEWED |
| `git check-ignore -v .env frontend/.env frontend/node_modules frontend/dist` | All four matched expected ignore rules | PASSED |

**New frontend testing files/configuration:** `frontend/src/App.test.jsx`, updated `frontend/vite.config.js` (Vitest configured with `environment: 'jsdom'`, test discovery and mock cleanup), and `test` / `test:watch` scripts in `frontend/package.json`.

**Dev tooling versions observed:** React and React DOM 19.3.1; Vite 8.3.4; Vitest 4.1.12; `@testing-library/react` 16.3.3; `@testing-library/dom` 10.4.2; `@testing-library/user-event` 14.6.8; jsdom 29.1.1. Installation of five test-tooling packages succeeded: 77 added packages, 221 audited, 0 reported vulnerabilities.

**Automated React tests — all PASSED:**

1. Both health and readiness healthy/ready ⇒ Ready.
2. Both backend calls fail ⇒ Unavailable.
3. Health succeeds, readiness rejects HTTP 503 ⇒ Not ready.
4. Refresh click ⇒ new health and readiness calls.
5. Initial Unavailable followed by successful refresh ⇒ Ready recovery.

**Testing boundary:** The five component tests mock `src/api/health.js`; real HTTP `fetch`, timeout behavior, deployed CORS policy, and end-to-end browser automation are not independently covered by these tests. Manual local browser integration was performed. Dependency lock validation is not a vulnerability audit or complete supply-chain review.

### Security and repository notes

- `.env` and `frontend/.env` are ignored; `frontend/node_modules` and `frontend/dist` are also ignored, confirmed using Git's matching-rule output.
- `frontend/.env.example` is visible to Git and should contain only public configuration. All `VITE_` variables are shipped to the browser: never store secrets in them.
- Git `??` denotes untracked files, not committed files. No initial commit has been verified.
- The previous Telecom RAG chatbot repository was not modified.

### Historical Phase 0 acceptance checklist (as recorded before Steps 8.9–8.10)

- [ ] Inspect the repository's commit-eligible source, configuration templates and generated artifacts for accidentally embedded secrets or credentials (do not print secret values in logs).
- [ ] Verify README and environment startup instructions reflect the actual backend and frontend commands, API ports, tests, and current limitations.
- [ ] Copy these updated master documentation files back into `docs/` in the local Cursor repository; review the final Git status and changes.
- [ ] Create and verify the initial Git commit when the user approves; ensure `.env`, frontend build outputs and dependency folders remain excluded.
- [ ] Review the frozen Phase 0 acceptance checklist and only then change Phase 0 to DONE; keep Phase 1 PENDING until started.

**Historical checkpoint:** These items were pending at Step 8.7 and were subsequently reviewed in Steps 8.9–8.10. No later-phase LangGraph, MCP, databases, vector retrieval, authentication platform, Docker or deployment is represented as implemented.


## Step 8.9 — Repository security, README and GitHub publication (2026-10-21)

**Status: DONE for repository publication.** Phase 0 acceptance and subsequent closure-documentation publication were completed in Step 8.10.

**Observed commands and outcomes**

```bash
git status --short --untracked-files=all
git ls-files
git check-ignore -v .env frontend/.env frontend/node_modules frontend/dist
uv lock --check
npm --prefix frontend ls --depth=0
wc -l -c README.md
git add .
git diff --cached --name-only
git -c core.pager=cat diff --cached --check
git -c core.pager=cat diff --cached --stat
git grep --cached -n -I -E 'AIza[[:alnum:]_-]{20,}|sk-[[:alnum:]_-]{15,}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY'
git remote add origin https://github.com/ujoy100/telecom-agentic-ai-support.git
git remote -v
git commit -m "chore: initialize telecom agentic AI support foundation"
git push -u origin main
git status
git log -1 --oneline
```

- The initial review staged **46 project files**, excluding local `.env` files, `.venv`, dependency installations and `dist`.
- The initial trailing-whitespace reports included intentional Markdown hard line breaks and two correctable non-Markdown issues. Added root `.gitattributes` with `*.md whitespace=-blank-at-eol`; corrected final blank line in `frontend/src/App.css` and trailing whitespace in `requirements-dev.txt`. Final staged `git diff --cached --check` returned no errors.
- Root README initially had 0 bytes; it was replaced with documented project setup and startup instructions; verification reported **157 lines, 6735 bytes**.
- The staged credential-pattern grep produced no matching output. This limited scanner does not establish complete secret-free status.
- GitHub repository `ujoy100/telecom-agentic-ai-support` was created by the user, who confirmed **Private** visibility. Its privacy setting was not changed by our local Git commands.
- **Initial commit:** `6533a2d` — `chore: initialize telecom agentic AI support foundation`.
- **Documentation commit:** `1787344` — `docs: document private GitHub setup and push workflow`.
- After the documentation push, `main` tracked `origin/main`, was up to date, and `git status` reported `nothing to commit, working tree clean`.

**Known limitations:** Phase 0 readiness is a controlled application flag, not automatic health monitoring for PostgreSQL or Qdrant. Frontend component tests mock the API utility; manual browser verification covers real local backend connectivity, not deployed E2E automation. Secret-pattern checks are necessarily incomplete. No future-phase infrastructure has been implemented.

## Step 8.10 — Phase 0 closure acceptance (2026-10-21)

- [x] React/Vite frontend and FastAPI backend boot locally; integrated health and readiness UI manually verified.
- [x] Backend: 21 automated tests; Ruff lint and formatting passed.
- [x] Frontend: 5 automated component tests; ESLint and Vite build passed.
- [x] Configuration and CORS checks, `.env` ignore rules, safe example templates, dependency locks verified.
- [x] README, command reference and phase documents supplied and user-reported applied to local repository.
- [x] Private GitHub remote, initial commit and documentation commit verified; working tree clean after second push.
- [x] Closure documentation copied to local `docs/` by the user; `git status --short` listed three modified Markdown files and `git diff --check` returned no errors.
- [x] Reviewed frozen Phase 0 gate against verified implementation, 26 tests, local integration, documentation and scoped security checks.
- [x] Phase 0 marked DONE in tracker and foundation.
- [x] **Publication:** Phase 0 closure commit `2c90b55` and command-reference commit `3a23b89` pushed; clean synchronized `main` verified.

**Current status: Phase 0 DONE; Phase 1 PENDING.**

## Phase 0 — Final Acceptance and Closure

**Completion date:** 2026-10-21  
**Status:** DONE

### Verified results

- FastAPI application, Pydantic configuration, health/readiness endpoints, and CORS implemented.
- React + Vite application implemented and connected to FastAPI.
- Backend automated tests: 21 PASSED.
- Frontend automated tests: 5 PASSED.
- Backend Ruff lint and formatting: PASSED.
- Frontend ESLint and production build: PASSED.
- Manual connectivity, backend-unavailable, refresh, and recovery scenarios: PASSED.
- Environment-file Git exclusions and limited staged secret-pattern scans: PASSED.
- Root README and technical documentation completed.
- Private GitHub repository verified.
- Initial repository commit: `6533a2d`.
- Git workflow documentation commit: `1787344`.
- Phase 0 acceptance/closure commit: `2c90b55`.
- Final command-reference commit: `3a23b89`; remote synchronized and working tree clean.

### Known limitations

- Readiness is currently controlled by `app.state.is_ready`; external dependency checks are deferred.
- Automated frontend tests mock the API functions; real-browser integration was verified separately.
- Security checks are foundational rather than a complete production security audit.
- PostgreSQL, Qdrant, LangGraph, MCP, Deep Agents, RAGAS, and deployment remain future-phase work.

**Phase 0 acceptance decision:** DONE (2026-10-21). Closure commits `2c90b55` and `3a23b89` were verified pushed; `git status` confirmed a clean working tree synchronized with `origin/main`.

**Next:** Phase 1 — PostgreSQL, Alembic, and mock telecom data. Status: PENDING.
