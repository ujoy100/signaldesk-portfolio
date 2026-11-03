# Phases 17–19 handoff

The original handoff below governs the private development repository
`ujoy100/telecom-agentic-ai-support`. This copy is maintained in the independent
public `ujoy100/signaldesk-portfolio` repository. Public validation/protection do
not automatically close private-repository acceptance. The historical private
baseline was `7358213`; public PR #10 merged as `3124016`. See
[the dated Phase 17 reconciliation](phase-17-reconciliation.md) and the master
tracker for current public evidence and unresolved requirements.

Do not initialize another repository, change remotes or rewrite history. Preserve
existing uncommitted owner changes and exclude all local secrets/configuration.
The owner’s local Compose port changes (8001/5174) remain outside this
public documentation-only PR.

## Public portfolio update — 3 November 2026

**Public CI and container security: VALIDATED at the recorded commit.**
**Phase 17: IN PROGRESS. Phases 18–19: PENDING.**
**Production deployment: NOT APPROVED.**

Public PR #11 merged into `main` as
`f952f55caf4a1f4090134c0fd016ce5d4e978110`.

The public FastAPI runtime migrated from Python 3.13 Debian Trixie
to Python 3.13 Alpine. The frontend Alpine runtime received a patched
`libexpat` package.

The unchanged strict Trivy HIGH/CRITICAL image gate passed.
Post-merge CI and real Compose browser acceptance also passed.

- [Post-merge CI](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839313)
- [Post-merge browstance](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839342)

The November 2 references below to 45 HIGH Debian findings are
historical. They are not the current public Alpine image result.

Public branch protection currently requires four checks. Passing
the image-security job does not establish that branch protection
requires that fifth check.

The original private project remains separate. Its branch-protection
acceptance and other outstanding requirements are not satisfied by
the public portfolio validation.

The public paid-evaluation environment still requires setup and
appropriate protection before optional paid evaluations.

This update does not authorize cloud deployment or changes to the
original private repository.

---

## Phase 17 — GitHub Actions

Keep Phase 17 IN PROGRESS. Any future implementation must use a reviewed PR in
the explicitly authorized repository; no historical commit/push instruction in
this handoff grants new authorization. This reconciliation permits only public
documentation on a separate branch/draft PR. It does not authorize application,
workflow, image, dependency, setting, deployment or private-repository changes.

Public application/browser/evaluation/secret checks pass on `3124016`; backend
Trivy remains 45 HIGH / 9 CVEs, zero CRITICAL. Public protection requires four
checks but not the enabled image-security job. Private protection is blocked by
the plan-related HTTP 403. The public `paid-evaluation` environment is not
configured. These are separate evidence/acceptance items, not a green release.
Production deployment remains blocked.

Required workflows: backend Ruff/pytest with disposable PostgreSQL and Qdrant
services; frontend npm ci/lint/test/build; deterministic evaluation gates; Alembic
head/check; Compose image builds. Use least-privilege read permissions, protected
`main`, required checks and reviewed pull requests. Paid OpenAI/real RAGAS jobs
must be manual opt-in and use GitHub secrets; they must not run by default.

## Phase 18 — cloud deployment

Keep Phase 18 PENDING. Frozen targets are Vercel for React/Vite; Render for
FastAPI, LangGraph and embedded official MCP services/Gateway; managed PostgreSQL;
Qdrant Cloud; and OpenAI API. Prerequisites include production JWT/OpenAI/Qdrant/
database secrets, HTTPS, exact Vercel CORS origin, restricted database roles,
managed backups, explicit Alembic migration and checkpoint jobs, health checks,
audit retention and post-deployment authorization/persistence validation. Do not
run migrations from ordinary requests and do not deploy from this handoff.

## Phase 19 — release

Keep Phase 19 PENDING. Complete final real-browser workflows, architecture and
trust-boundary diagrams, sanitized screenshots, full README/command reference,
known limitations, release notes, portfolio demonstration, security review and
end-to-end evidence across authentication, deterministic/Deep-Agent routing,
MCP, approvals, knowledge promotion, feedback, observability and recovery.
