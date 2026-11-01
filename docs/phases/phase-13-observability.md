# Phase 13 — Observability

**Status: DONE (2026-10-26).**

An exporter-neutral telemetry layer propagates correlation IDs with
`contextvars` and returns `X-Correlation-ID` from FastAPI. Structured events
cover HTTP requests, every LangGraph node, retrieval latency/evidence count,
MCP tool outcome/latency/error, and Deep Agent duration, model invocations,
tool calls, token use and estimated cost. Pricing is an explicitly versioned
estimate (`2026-10-26`), never a billing record.

Telemetry excludes fields containing token/credential names and redacts email,
phone and long numeric identifiers. Gateway arguments, JWTs, prompts, retrieved
content and customer payloads are not logged. Existing PostgreSQL audit events
remain the authority for approvals and controlled writes; telemetry is
operational evidence, not authorization.

Operational queries should group events by `correlation_id`, `name`, `outcome`,
`attributes.error_code`, and latency percentiles. Recommended dashboards show
HTTP error rate, retrieval no-answer rate, MCP timeout/error counts, approval
outcomes, Deep Agent tool/model budgets and estimated model cost.
