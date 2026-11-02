# Demonstration evidence and limits — 2 November 2026

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
