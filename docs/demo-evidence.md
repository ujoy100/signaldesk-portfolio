# Demonstration evidence and limits — 2 November 2026

> **Evidence update — 3 November 2026:** The earlier Debian
> vulnerability findings are historical. The public Alpine backend
> and patched frontend subsequently passed the strict Trivy gate
> and post-merge CI.
>
> See the November 3 validation section below.


SignalDesk is a personal learning/portfolio project developed with Codex
assistance. Data and identities used for demonstration are fictional. No customer
or employer deployment, production clearance or fabricated benchmark is claimed.

## Directly observed local demonstration

The preceding local walkthrough started existing PostgreSQL, Qdrant, FastAPI and
React containers without rebuilding or deleting volumes. A stale one-shot
migration image was identified; selecting the existing API image for migration
and checkpoint services completed startup. This motivates the shared-image fix
in this PR. The database was already at Alembic head `2d4f8a71c930`.

A fresh automated Google Chrome context exercised real UI/API operations:

- Fictional-token login; unauthenticated session rejected (401).
- Support Agent navigation and approval API denial (403).
- Deterministic LangGraph response with evidence signals `keyword`, `vector`
  and `deterministic_cross_signal_reranker`.
- Feedback creation and later Admin review.
- One genuine Deep Agents/OpenAI request completed with customer, ticket and
  knowledge evidence. It returned insufficient evidence for a confirmed roaming
  cause; this is not evidence of successful root-cause diagnosis.
- A dedicated fictional demo ticket paused for approval. A material edit created
  a replacement approval; Supervisor approval executed it; replay returned 409.
- Admin knowledge listing, development UI logout and responsive mobile layout.

The recorder had locator/duplicate-feedback assertion errors; these were fixed
in the temporary harness and a continuation completed the remaining views. No
application defect was inferred from those harness errors. Positive responses
were not mocked. Temporary screenshots/results from that session are no longer
available; do not treat this prose as a downloadable recording or exact-PR proof.
Fresh hosted validation and screenshot artifacts are required for this PR.

Focused local regression results at that earlier working-tree baseline:
13 authentication/session tests, 22 workflow/approval/MCP/checkpoint tests,
and 7 frontend tests passed. These are not claimed as reruns on the PR SHA.

## Claims requiring separate evidence

| Feature | Evidence boundary |
|---|---|
| Current PR application and startup | Exact-SHA hosted checks must establish it; prior results alone are insufficient. |
| Genuine Deep Agents | Observed locally as above; default hosted/browser jobs deliberately have no paid provider key. |
| Entra | Configuration presence and authorization redirect with S256 PKCE/state/nonce observed. No new interactive Microsoft sign-in completed in that session because computer-control permission was unavailable. Earlier historical acceptance is documented separately. |
| Session revocation/CSRF, concurrent approvals and recovery | Automated regression coverage; development-token UI logout alone does not prove Entra cookie revocation. |
| Knowledge promotion | The earlier UI walkthrough showed listing. Hosted HTTP/browser acceptance exercises promotion separately. |
| Four-minute demo video | Runbook provided; no completed video is claimed. |
| Container security | Existing backend 46 HIGH rows / 10 CVEs remain documented; production release stays blocked. No suppression or gate weakening. |

## Runtime scope

No technology, dependency lock or application feature is removed. RAGAS remains
an isolated optional evaluation extra; provider/Entra credentials are optional
for the default fictional demo. Default startup needs only PostgreSQL, Qdrant,
API and UI plus explicit one-shot migration/checkpoint initialization. Seed is
already a tools-profile task. Further OS-image experiments stopped because no
supported verified fix was established; DHI migration is not included.

Project and image names are public-portfolio scoped to avoid reusing the private
project’s containers or volumes. This PR does not migrate/delete pre-existing
volumes, change GitHub protections or deploy. Phase 17 IN PROGRESS; 18–19 PENDING.

## Hosted evidence for source commit `53a21b7`

[CI run](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41410657422)
and [browser run](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41410657421)
ran the PR merge simulation `7f9e127e005c2fb8036169c24acd7e68d2789041`.

| Check | Observed result |
|---|---|
| Backend regression | 131 passed, 1 intentional paid-test skip; one known optional RAGAS import warning |
| Frontend | Lint/build and 7 tests passed |
| Chrome Playwright | 5 passed in 15.1 seconds |
| Migration/checkpoint startup | Completed; API/migrate/checkpoint containers share the same image ID |
| Live HTTP acceptance | Invalid/expired tokens 401; unauthorized approval 403; edit reauthorization true; feedback visible; 1 promoted Qdrant point; exactly-once event delta 1 |
| Secret/dependency checks | Passed |
| Strict Trivy image gate | Failed: backend 45 HIGH rows / 9 CVEs, 0 CRITICAL; frontend 0 HIGH/CRITICAL |

The historical 46 HIGH / 10-CVE baseline in SECURITY.md and the existing findings
report is preserved. This newer scan omits CVE-2026-119586 while reporting the
same SQLite package version; no application/runtime fix or remediation of that
CVE is inferred. Remaining IDs: CVE-2025-69720, CVE-2026-119373,
CVE-2026-16742, CVE-2026-54369, CVE-2026-76642, CVE-2026-78408,
CVE-2026-78409, CVE-2026-78410 and CVE-2026-9538. Their Fixed Version cells
are empty in this run. No further speculative runtime change was attempted.

The six checked-in screenshots were refreshed from that browser run’s allowlisted
artifact after visual privacy review: empty token input at login, fictional
Development User roles, fictional ticket/knowledge data, no real identities or
credentials. PNGs contain no text/EXIF metadata. The source SHA above is their
capture provenance; later documentation/asset commits do not retroactively make
these captures evidence from another SHA. New runs produce separate artifacts.

## Public Alpine remediation and post-merge validation — 3 November 2026

This section supersedes earlier statements about the **current public
portfolio container security status**, while preserving their original
historical evidence.

The public backend migrated from Python 3.13 Debian Trixie to
Python 3.13 Alpine. The frontend received a patched Alpine `libexpat`
dependency. The strict Trivy HIGH/CRITICAL gate was retained without
vulnerability suppressions or an ignore-unfixed exception.

### Verification results

| Check | Result |
|---|---|
| Backend Alpine runtime | Built and validated |
| Backend regression tests | 131 passed, 1 skipped in earlier Alpine testing |
| FastAPI health | HTTP 200 |
| Backend runtime Trivy gate | PASS |
| Frontend runtime Trivy gate | PASS |
| GitHub Actions CI after merge | SUCCESS |
| Playwright browser acceptance after merge | SUCCESS |

Public merge commit:
`f952f55caf4a1f4090134c0fd016ce5d4e978110`

- [Post-merge CI](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839313)
- [Post-merge browser acceptance](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839342)

### Evidence boundaries

These results establish automated validation for the public portfolio
at the stated commit. They do not constitute production security
certification or confirm cloud deployment.

The original private `telecom-agentic-ai-support` project is separate;
its unresolved findings and acceptance requirements are unaffected.

Phase 17 remains **IN PROGRESS**. Cloud deployment (Phase 18) and final
release acceptance (Phase 19) remain **PENDING**.
