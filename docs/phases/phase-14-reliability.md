# Phase 14 — Reliability and failure recovery

**Status: DONE (2026-10-26).**

Model/Deep Agent, MCP and existing database/Qdrant boundaries use explicit
timeouts. Transient read/idempotent work can use capped exponential retry
(maximum five attempts); controlled writes are never blindly retried. Existing
approval consumption, execution request IDs, row locks and checkpoint tests
preserve exactly-once ticket behavior across replay and restart.

Knowledge promotion reconciliation scans only persisted `staging`, `staged` or
`committed` rows that already contain approval and execution-request scope. It
requires an active PostgreSQL-backed Admin identity and re-enters the existing
`promote` state machine. It cannot create approval, change scope, or activate a
point before PostgreSQL authority is committed. Tests inject Qdrant staging and
publication failures, PostgreSQL commit failure, concurrent ownership,
checkpoint interruption, unavailable MCP services, timeouts and retry
exhaustion.

## Recovery runbook

1. Confirm PostgreSQL and Qdrant readiness without modifying data.
2. Inspect promotion state and safe error type; never reset either store.
3. Invoke `reconcile_pending` as an authenticated active Admin with the normal
   service configuration.
4. Verify `published`, one active Qdrant version, consumed approval and audit
   events. A failure remains inactive/retryable and is counted, not hidden.
5. Escalate repeated failures; do not broaden scope or manufacture approval.

Dependency degradation returns explicit insufficient-evidence or service
unavailable states. Error surfaces contain classifications, not secrets or raw
customer data.
