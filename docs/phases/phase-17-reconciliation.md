# Phase 17 reconciliation — 2 November 2026

**Phase 17 IN PROGRESS. Phases 18–19 PENDING. Production deployment BLOCKED.**
This document records evidence and unresolved acceptance requirements; it does
not change the frozen architecture, completion criteria or security policy.

## Reconciliation update — 3 November 2026

**Public portfolio container remediation: VALIDATED.**
**Phase 17: IN PROGRESS. Phases 18–19: PENDING.**
**Production deployment: NOT APPROVED.**

This update supersedes the November 2 statements about the current
public backend vulnerability gate. Earlier Debian findings and failed
workflow results remain preserved as historical evidence.

### Remediation and validation

The public backend migrated from Python 3.13 Debian Trixie to
Python 3.13 Alpine. The frontend Alpine runtime was updated to
require a patched `libexpat` package.

The strict Trivy HIGH/CRITICAL gate remained unchanged. No
vulnerability suppression or ignorxed exception was introduced.

| Check | Verified result |
|---|---|
| Backend Alpine runtime | Built and validated |
| Backend regression | 131 passed, 1 skipped in earlier Alpine testing |
| Backend health endpoint | HTTP 200 |
| Backend and frontend Trivy | Strict gate passed |
| Post-merge GitHub Actions CI | SUCCESS |
| Post-merge browser acceptance | SUCCESS |

Public PR #11 merged into `main` as
`f952f55caf4a1f4090134c0fd016ce5d4e978110`.

Evidence:

- [Post-merge CI](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839313)
- [Post-merge browser acceptance](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839342)

### Remaining acceptance boundaries

The public portfolio's validated container images are no longer
blocked by the historical Debian Trivy findings at that commit.

This does not change the separate original private repository.
Private branch-protection acceptance remains blocked by the
previously observed GitHub plan-related HTTP 403.

The public `paid-evaluation` environment still requires
configuration and protection before optional paid evaluation.

Public branch protection and required-check configuration must
remain accurately described. Passing the image-security job does
not itself establish that GitHub branch protection requires it.

The frozen architecture and technology choices remain unchanged.
Cloud deployment, live identity-provider validation and final
production acceptance have not been completed.

---

## Authority and repository scope

The repository Phase 17 specification, Phase 17–19 handoff and master phase
tracker govern this reconciliation. They reference *Telecom Agentic AI Support
Platform — Frozen Project Documentation*, v1.0. The standalone original document
is not present in this checkout; no new quotation or interpretation of its
unavailable text is asserted here.

`ujoy100/telecom-agentic-ai-support` is the original private development repository.
`ujoy100/signaldesk-portfolio` is an independent public portfolio repository.
Public validation does not automatically satisfy private-repository acceptance,
transfer its branch protection, or amend the original handoff’s repository scope.
Only the public documentation is changed by this reconciliation.

## Confirmed public-main evidence

[PR #10](https://github.com/ujoy100/signaldesk-portfolio/pull/10) merged as
`3124016c2bed6af97565888e3ae863f587a3fa17` (short `3124016`). The results below
belong to that merged public-main SHA, not an uncommitted local configuration or
the later documentation PR.

| Requirement / check | Confirmed result | Evidence |
|---|---|---|
| Backend, migrations and checkpoints | 131 passed, 1 intentional paid-model skip; backend job passed | [Merged-main CI](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41412969331) |
| Frontend lint, tests and build | Passed; 7 tests passed | Same CI run |
| Deterministic evaluation | 40 cases passed the configured thresholds | Same backend job |
| Secret/dependency checks | Passed | Same CI run |
| Real Chrome / Compose acceptance | 5 tests passed | [Merged-main browser run](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41412969300) |
| Container builds | Completed; the subsequent security scan failed | Same CI run |
| Backend Trivy | 45 HIGH package/advisory rows across 9 CVEs, zero CRITICAL | Same CI run |
| Frontend Trivy | Zero HIGH/CRITICAL findings | Same CI run |

The public application has also been demonstrated locally with Docker and
fictional telecom data. A working local demonstration and passing application
tests are evidence of functionality, not production readiness. The
[demo runbook](../recruiter-demo.md) and [demo evidence](../demo-evidence.md)
distinguish real UI/API operations, automated tests and optional provider flows.
Default hosted checks do not establish fresh interactive Entra sign-in or a
paid Deep Agents/RAGAS run. The intentional paid-test skip remains visible.

## Current governance and remaining requirements

| Item | Confirmed state | Acceptance consequence |
|---|---|---|
| Public `main` protection | Four passing checks required; branch must be up to date; PRs required; force pushes and deletion prohibited | Public protection exists; it is not protection for the private repository |
| Required public check names | Backend, PostgreSQL, Qdrant, migrations and evaluation; Frontend lint, tests and production build; Secret and dependency review; Playwright with real Compose stack | These four checks pass on merged `3124016` |
| Image/security job | Reproducible backend and frontend images is enabled and visible, fails on the strict Trivy scan, and is **not required by public branch protection** | This differs from the Phase 17 specification’s required image-check acceptance; no setting is changed here |
| Sole-maintainer review | Zero mandatory approving reviews; no mandatory external/code-owner approval | Owner review remains a process responsibility; this record does not introduce a self-locking review requirement |
| Private `main` protection | Last verified read returned GitHub plan-related HTTP 403 | Original private-repository protection acceptance remains BLOCKED; no visibility/plan/settings change is authorized here |
| `paid-evaluation` environment | Not configured in the public repository, although the manual workflow references that name | Required-reviewer protection and the appropriate secret must be established before any optional paid run; a YAML environment name alone is not a protected environment |
| Phase 17 closure | Not all requirements are satisfied | Keep IN PROGRESS; public portfolio publication does not grant Phase 17 completion |

The remaining owner decisions are which repository is the subject of Phase 17
acceptance and how to satisfy its documented protection/check requirements.
Neither a scope change nor a security exception is approved by this document.
The paid workflow must remain manual and explicitly confirmed; configuring a
protected environment is separate work requiring owner authorization. No paid
run is initiated by this reconciliation.

## Historical versus latest vulnerability evidence

The 1 November report recorded **46 HIGH rows across 10 CVEs** against the private
development baseline. Preserve that dated evidence in
[backend-container-findings.md](../backend-container-findings.md) and SECURITY.md.
The newer merged-public-main scan above reports **45 HIGH rows across 9 CVEs**.

The newer report omits CVE-2026-119586 while retaining the recorded SQLite package
version; that is not proof of an application fix, a patched image or removal of
all risk. The nine reported IDs are CVE-2025-69720, CVE-2026-119373,
CVE-2026-16742, CVE-2026-54369, CVE-2026-76642, CVE-2026-78408,
CVE-2026-78409, CVE-2026-78410 and CVE-2026-9538. The observed scan has no fixed
versions listed for those findings. This is dated scan evidence, not a promise
about future advisory feeds or upstream fixes.

The Trivy implementation is working as a fail-closed gate. Satisfying that gate
is still blocked. The current tracker explicitly retains the failing container
gate as a Phase 17 blocker, and the specification requires successful acceptance
checks including image-build. Therefore the findings block **Phase 17 acceptance
under the recorded criteria as well as production deployment**. No claim is made
that the unavailable original frozen text explicitly specified a zero-HIGH
threshold. No scanner suppression, threshold reduction or runtime change is made.

## Phase boundaries and next action

- **Phase 17:** hosted CI/evaluation, documented checks, least-privilege workflows,
  repository protection/review requirements and optional paid-workflow safeguards.
- **Phase 18 PENDING:** Vercel/Render deployment, production secrets/configuration,
  HTTPS/CORS, managed PostgreSQL/Qdrant, backups, restricted roles, health/audit
  operations and post-deployment authorization/persistence validation.
- **Phase 19 PENDING:** complete release documentation/diagrams, sanitized demo
  assets, release notes and full end-to-end acceptance across the specified flows.
  Existing screenshots and a working demo are partial evidence, not completion.

Next: owner review of repository scope and the protection/paid-environment gaps.
Resume container remediation only when a supported, evidenced fix is available;
do not continue speculative runtime changes or weaken existing gates. Production
release remains blocked.

The owner’s uncommitted `compose.yaml` port changes (8001/5174) are local-only,
not staged or included in this documentation reconciliation, and are not covered
by the merged-main validation above.
