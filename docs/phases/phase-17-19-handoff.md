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
