# Phases 17–19 handoff

This handoff applies to the existing private repository
`ujoy100/telecom-agentic-ai-support`, branch `main`. The historical baseline
was `7358213`; current implementation and evidence are in the master tracker. Do not
initialize another repository, change the remote, rewrite history, or stage
without reviewing `git status`, `git diff`, and ignored files.

## Phase 17 — GitHub Actions

Keep Phase 17 IN PROGRESS. The owner should review and stage only source, migrations,
tests and documentation. Exclude `.env`, `frontend/.env`, `secrets/*.txt`, API
keys, local databases, `.venv`, caches, `node_modules` and build output. Before a
future commit: run all quality gates, `git diff --cached --check`, inspect
`git diff --cached`, scan staged content for credentials, then commit and push to
the existing `main` within explicit owner authorization. The current task authorizes a reviewed
normal commit/push after passing gates, but not publication or settings changes.

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
