# Contributing to SignalDesk

This portfolio project follows the frozen project architecture and
[phase tracker](docs/phase-tracker.md). Discuss proposed contributions with the
owner before submitting work. No broad open-source reuse license is offered;
contributions require an explicit agreement about rights before acceptance.
Do not add an MIT or Apache license without the owner's decision.

Keep React/Vite, FastAPI, PostgreSQL, Qdrant, LangChain, LangGraph, Deep Agents,
MCP and RAGAS boundaries intact. Preserve completed workflows. Do not modify or
import private material from the previous Telecom RAG repository.

Use a focused branch and explain the problem, behavior change, limitations and
validation in a pull request. Review all changes before staging. Run backend
Ruff/pytest against only `telecom_test_db`, frontend lint/Vitest/build and affected
Playwright checks. Run migration checks, deterministic evaluation, image builds
and dependency/secret scans when relevant. Paid evaluations require explicit
opt-in. See the root README and phase command references.

Never commit credentials, `.env`, local data, identity-provider information,
node_modules, virtual environments, generated builds, traces or private logs.
Use only fictional fixtures and document the provenance of any asset or dataset.
`VITE_` configuration is public. Report security concerns privately as described
in [SECURITY.md](SECURITY.md); do not paste secrets into issues or pull requests.

Do not weaken authorization, approval binding, test database guards, audit
checks, or CI to obtain a passing result. Preserve Docker volumes and development
databases. History rewrites, artifact deletion, secret rotation, deployment,
publication and repository security-setting changes require explicit owner
approval. Phase 17 remains IN PROGRESS until required CI and branch protection
pass; Phases 18 and 19 need their own implementation and acceptance.
