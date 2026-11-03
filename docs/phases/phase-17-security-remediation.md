# SignalDesk Portfolio — Phase 17 Security Remediation, CI/CD and Merge Evidence

**Record date:** 2026-11-03  
**Scope:** Public repository `ujoy100/signaldesk-portfolio` only  
**Original private development repository:** `ujoy100/telecom-agentic-ai-support` — deliberately not changed  
**Public merge commit:** `f952f55caf4a1f4090134c0fd016ce5d4e978110`  
**Phase status:** Phase 17 **IN PROGRESS**; Phases 18–19 **PENDING**  
**Production deployment:** **BLOCKED / not approved**

> **Scope distinction:** A passing public portfolio build and branch protection do not establish acceptance of the separate private project, deployment readiness, or production security certification. This is a documented engineering and security validation milestone, not a production approval.

## 1. Executive summary

The public SignalDesk portfolio initially failed the strict Trivy HIGH/CRITICAL image vulnerability gate due to numerous operating-system findings in its Debian-based Python backend. Alternative bases were investigated. An explicitly approved, isolated Alpine Python 3.13 migration passed a local full-runtime Trivy scan and 131 backend tests (one skipped). A subsequent GitHub Actions failure exposed missing native build dependencies in the RAGAS evaluation image; adding `build-base` and `linux-headers` to the **evaluation stage only** addressed that build error. A later CI scan identified two HIGH `libexpat` vulnerabilities in the Nginx frontend image; a Dockerfile minimum patched-version requirement addressed the frontend gate failure.

The unchanged strict CI security gate subsequently passed; all five PR checks succeeded. PR #11 was merged to public `main`, and **both post-merge CI and Browser Acceptance passed on the same merge commit**.

## 2. Frozen architecture and change boundaries

The project architecture remains React + Vite, FastAPI + Pydantic, LangGraph, LangChain, bounded Deep Agents, MCP and MCP Gateway, PostgreSQL + Alembic, Qdrant, RAGAS and custom safety/evaluation tests, structured outputs, HITL controls, Docker/Compose and GitHub Actions. The approved migration changed the **public backend container base OS**, not these architectural decisions or the locked Python dependencies.

- No replacement of PostgreSQL with Pinecone or of any other frozen service.
- No modification of the original private project or previous telecom RAG project.
- No relaxation, suppression or exclusion of the Trivy HIGH/CRITICAL vulnerability gate.
- No use or publication of real credentials. Secrets must stay out of Git.
- Locally modified `compose.yaml` ports (`8001`/`5174`) were **not staged or committed** in PR #11.
- Local experimental `backend/Dockerfile.alpine-test` and `backend/Dockerfile.debian-backup` were not included in PR #11.
- No deletion of Docker database volumes or production deployment.

## 3. Chronological investigation and remediation

### 3.1 Initial backend security blocker

Original backend `base` stage used `python:3.13-slim-trixie` and Debian's `apt-get`. The unchanged raw Trivy gate flagged approximately **45 HIGH / 0 CRITICAL** OS-related findings in the public Debian backend. The counts are scan-specific; do not conflate with separate private-project scan records. Investigated Debian Bookworm, distroless and Docker Hardened Images; none met the same strict gate in these local tests. This was not evidence of application exploitation, but it prevented meeting the configured vulnerability acceptance criterion.

**Gate (unchanged):**
```sh
trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 1 <image>
```

### 3.2 Approved Alpine base migration

The owner explicitly approved switching **only the SignalDesk portfolio backend** to Alpine Python 3.13.

```diff
-FROM python:3.13-slim-trixie AS base
+FROM python:3.13-alpine AS base
 ...
-RUN apt-get update && apt-get upgrade --yes ...
+RUN apk upgrade --no-cache ...
```

The official backend Dockerfile retained `base`, `evaluation`, and `runtime` stages and continued to install the same frozen `uv.lock` production dependencies. The production runtime omitted optional evaluation packages. A local ARM64 build of `backend/Dockerfile --target runtime` succeeded as `signaldesk-backend-alpine:verification` (Docker build: 12/12 steps, ~37.6 seconds). Trivy 0.76.1 reported **zero HIGH and zero CRITICAL** for Alpine 3.24.3 and installed Python metadata. Trivy printed a third-party SBOM accuracy warning; note this as a scanner caveat, not a detected vulnerability.

### 3.3 Alpine backend regression and integration evidence

The **experimental Alpine test-stage image** `signaldesk-alpine-test-runner:local` was built with `--extra evaluation`, native build dependencies and `git` to run pytest against the installed RAGAS package.

- Previously failing `test_installed_ragas_metrics_load_with_current_langchain`: **1 passed**, one deprecation warning about `langchain-community`.
- Full backend suite: **131 passed, 1 skipped, 1 warning**, ~10.26 seconds.
- PostgreSQL tests used only the dedicated `telecom_test_db`, with explicit URL/database safety assertions. Application database `telecom_db` was not used as the test target.
- PostgreSQL authentication/query, Qdrant get_collections and Alembic migration head were validated in isolated test/integration runs.
- Official production image: `from backend.app.main import app` FastAPI import passed.
- Official image temporary, network-isolated Uvicorn HTTP smoke test: `GET /health` returned **HTTP 200** and `{"status":"healthy"}`; clean shutdown.
- Native runtime import checks earlier passed for Psycopg, gRPC, NumPy, Cryptography, uvloop, httptools, pydantic_core and orjson.

**Evidence limitation:** The full 131-test regression suite was run on the experimental Alpine **test stage**, while the official production runtime separately passed import, HTTP and vulnerability checks; do not claim pytest ran in the stripped production runtime image.

### 3.4 GitHub Actions evaluation-image `g++` failure

On PR #11, CI #18 failed in `Build isolated evaluation image`. The RAGAS 0.3.9 dependency graph included `scikit-network==0.33.5`, whose source build required `g++`; Alpine evaluation stage initially installed only `git`.

Original failure:
```text
error: [Errno 2] No such file or directory: 'g++'
hint: scikit-network (v0.33.5) included because ragas (v0.3.9) depends on scikit-network
```

Fix:
```diff
 FROM base AS evaluation
-RUN apk add --no-cache git \
+RUN apk add --no-cache git build-base linux-headers \
     && uv sync --frozen --no-dev --extra evaluation --no-install-project
```

`build-base` provides the native C/C++ build toolchain; `linux-headers` provides build-time headers. These packages were **not added to the production runtime**. Later CI progressed beyond the evaluation build, confirming this error was cleared.

### 3.5 GitHub Actions frontend `libexpat` findings

CI #19 reached the strict image-scanning stage and reported **2 HIGH, 0 CRITICAL** in `signaldesk-frontend:ci` (Alpine 3.24.3), while the backend scan was clean:

| Vulnerability | Package | Installed | Fixed version indicated |
|---|---|---|---|
| CVE-2026-117610 | `libexpat` | `2.9.0-r0` | `2.10.0-r0` |
| CVE-2026-118370 | `libexpat` | `2.9.0-r0` | `2.10.0-r0` |

The pinned Nginx runtime already had `RUN apk upgrade --no-cache`, but the produced image still contained the vulnerable version at the time of CI #19.

Fix:
```diff
 FROM nginx:1.30.6-alpine@sha256:0e52bd054126cdc040b1276c0af347aeb02a41b9cfe305d6094767ac30e97949
-RUN apk upgrade --no-cache
+RUN apk upgrade --no-cache \
+    && apk add --no-cache 'libexpat>=2.10.0-r0'
```

The explicit minimum version means builds fail if the required version is unavailable, rather than silently accepting an older vulnerable package. The Docker base-image digest was preserved. Subsequent configured strict CI vulnerability checks succeeded without changing their threshold.

### 3.6 Successful PR validation and merge

PR [#11](https://github.com/ujoy100/signaldesk-portfolio/pull/11) was initially Draft, later marked Ready for review, confirmed `MERGEABLE` and `CLEAN`, then merged into the **public** `main` branch on **2026-11-03 at 10:52:14 UTC**.

| Commit | Description |
|---|---|
| `c833b6b` | Documentation-only Phase 17 evidence reconciliation |
| `13c3d80` | Migrate public backend runtime to Alpine |
| `505886c` | Install native Alpine evaluation build dependencies |
| `5e32143` | Require patched `libexpat` in frontend |
| `f952f55caf4a1f4090134c0fd016ce5d4e978110` | PR #11 merge commit on public `main` |

The PR changed **exactly seven files**:

```text
EXPORT_MANIFEST.json
backend/Dockerfile
docs/phase-tracker.md
docs/phases/phase-17-19-handoff.md
docs/phases/phase-17-github-actions.md
docs/phases/phase-17-reconciliation.md
frontend/Dockerfile
```

`compose.yaml`, private repository source, GitHub workflow code and all database volumes were outside the PR changes.

## 4. Verification evidence

### 4.1 Successful pre-merge checks

All **five** checks completed successfully on `5e32143c07eadfb38d5069f529a660334ab40c74`:

1. Backend, PostgreSQL, Qdrant, migrations and evaluation
2. Frontend lint, tests and production build
3. Secret and dependency review
4. Playwright with real Compose stack
5. Reproducible backend and frontend images

Pre-merge workflow evidence:
- [CI run 41616194235](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41616194235) — **success**
- [Browser acceptance run 41616194233](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41616194233) — **success**

### 4.2 Successful post-merge checks on public `main`

Both GitHub Actions workflows completed with `"status":"completed", "conclusion":"success"` on the exact **merge SHA `f952f55caf4a1f4090134c0fd016ce5d4e978110`**.

| Workflow | GitHub Actions evidence | Conclusion |
|---|---|---|
| CI #21 | [Run 41622839313](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839313) | SUCCESS |
| Browser acceptance #21 | [Run 41622839342](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839342) | SUCCESS |

The CI workflow scans both backend and frontend runtime images with `--scanners vuln --severity HIGH,CRITICAL --exit-code 1`; the passing workflow is evidence that its configured strict scan gate completed successfully at that commit. Preserve scanner version/DB timestamp if making later audit comparisons. Re-scan periodically: a clean historic result is not a guarantee against future CVEs.

### 4.3 Public `main` branch protection

The public repository's GitHub API response confirmed:
- **Strict** required up-to-date status checks (`strict:true`).
- Required contexts: Backend/PostgreSQL/Qdrant/migrations/evaluation; frontend lint/tests/build; secret/dependency review; Playwright with real Compose.
- Admin enforcement **enabled**.
- Force pushes **not allowed**; branch deletion **not allowed**.
- Conversation resolution **required**.
- **Zero** required approving reviews; signed commits **not required**.

This protection evidence applies to `ujoy100/signaldesk-portfolio/main` **only**. An empty PR `reviewDecision` did not represent an approved review; none was required by the configured rules.

### 4.4 Verification commands (reference)

```sh
# Run from Mac Terminal; read-only GitHub queries can run outside the repo.
gh pr view 11 --repo ujoy100/signaldesk-portfolio \
  --json state,mergedAt,mergeCommit
gh run list --repo ujoy100/signaldesk-portfolio --branch main \
  --limit 2 --json workflowName,headSha,status,conclusion,url
gh api repos/ujoy100/signaldesk-portfolio/branches/main/protection

# Local git checks from portfolio-export (do not stage all files):
git status --short
git diff --check
git diff --cached --name-only

# CI's strict vulnerability threshold (run on intended image):
trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 1 IMAGE
```

## 5. Outstanding private-project and production acceptance boundaries

These are **not current failures of public SignalDesk post-merge CI**:

| Topic | Evidence/status | Required next action |
|---|---|---|
| Private repository branch protection | `gh api repos/ujoy100/telecom-agentic-ai-support/branches/main/protection` returned **HTTP 403**, message: `Upgrade to GitHub Pro or make this repository public to enable this feature.` | Keep private; consider eligible GitHub paid plan, or record as blocker. Procedural branch discipline is not equivalent to enforced protection. |
| Private-project vulnerability findings | Latest recorded scan: **45 HIGH across 9 CVEs**; older historical: **46 HIGH across 10 CVEs** | Retain dated raw reports; investigate/remediate private image separately; do not present public Alpine scan as private remediation. |
| Paid-environment evaluation | Not yet evidenced | Obtain actual paid-environment validation and document results; do not invent outcomes. |
| Production deployment | Not approved or verified | Meet frozen acceptance criteria, security sign-off and deployment-specific validation first. |
| Phase 17 | **IN PROGRESS** | Update master tracker with dated public evidence and explicit blockers; phase is DONE only after all applicable implementation, tests, evaluations, documentation and validations. |
| Phases 18–19 | **PENDING** | Do not advance based solely on portfolio CI. |

## 6. Practical engineering lessons

1. **Distinguish OS and Python package findings:** A Trivy report can fail on base-image packages even when FastAPI tests pass.
2. **Do not weaken a failing security gate:** Prefer changing vulnerable packages or images over exclusions or threshold changes.
3. **Build stages matter:** Native compilers can be necessary for RAGAS *evaluation* without belonging in the production runtime.
4. **Transitive dependencies matter:** `ragas → scikit-network → g++` explains a Python evaluation build failure.
5. **Scan both backend and frontend:** Fixing one image may expose a previously hidden gate failure in another image.
6. **Interpret GitHub workflow scope correctly:** Branch-PR successes and post-merge `main` successes should be recorded separately by exact SHA.
7. **Keep private and public acceptance separate:** Public portfolio validation is useful for recruiters but not a private production authorization.
8. **Keep local-only files safe:** Explicit `git add <path>` avoids committing local port overrides and experimental Dockerfiles.
9. **Limit Docker disk use:** Reuse cached builds, avoid unnecessary local evaluation rebuilds, preserve DB volumes and review image/cache cleanup before deletion.

## 7. Resume / interview technical explanation

> I resolved a strict container security gate failure in a telecom-focused agentic AI portfolio. The Debian Python runtime initially had 45 HIGH image findings, so I validated and migrated only the public backend runtime to Alpine Python 3.13 while retaining the frozen `uv.lock` dependencies. CI then exposed a RAGAS transitive native compilation requirement, which I fixed by adding build tools only to the evaluation stage. A later CI scan flagged two HIGH `libexpat` vulnerabilities in the Nginx frontend, which I addressed with a minimum patched-package requirement. The unchanged Trivy gate passed, five PR checks passed, the changes merged to `main`, and both post-merge CI and Playwright acceptance passed. I kept production approval and private-repository security requirements explicitly separate.

## 8. Documentation integration status

This engineering record is staged on the public
`docs/recruiter-readiness` documentation branch as
`docs/phases/phase-17-security-remediation.md`.

- [x] Add the engineering record to the public repository.
- [x] Update the Phase 17 tracker and reconciliation.
- [x] Preserve historical security findings.
- [x] Validate local Markdown file links.
- [x] Run staged Gitleaks scan: no leaks found.
- [ ] Complete final staged-content and provenance review.
- [ ] Verify any required export-manifest consistency.
- [ ] Commit the reviewed documentation changes.
- [ ] Open a documentation-only pull request.
- [ ] Verify exact-commit GitHub Actions checks.

The modified local `compose.yaml` and experimental Dockerfiles
remain excluded from the staged documentation changes.

Phase 17 remains IN PROGRESS; Phases 18–19 remain PENDING.
Production deployment is not approved.

**Record provenance:** Evidence comes from user-provided Mac Terminal logs, GitHub CLI responses, CI log excerpts, screenshots and the frozen project document. This record does not assert that a fresh checkout, new code change or new paid-environment test has been executed during its preparation.
