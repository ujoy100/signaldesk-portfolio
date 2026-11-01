# Phase 9 — Human approval

**Status: DONE (2026-10-25).**

Migration `a6d9c8421b7e` additively extends `human_approvals`; it does not delete
or reset data. Requests store a UUID, workflow thread, canonical action payload
SHA-256 digest, expiry, decision, reviewer, consumed flag, execution request ID,
and timestamps. Legacy approvals are preserved but cannot pass exact-scope
verification.

`ApprovalService` uses row locks and checks state, expiry, active database-backed
supervisor/admin membership, exact action digest, and single-use execution
identity. Approve, edit, and reject are supported. Editing replaces the payload
and digest, invalidating the former scope. Audit records contain identifiers and
digests, not action payloads or PII.

The Gateway verifies approval before routing. The ticket MCP tool verifies again
inside the transaction that mutates a ticket, adds its event, and consumes the
approval. Ticket update and creation are enabled only when explicitly configured
with this chain; default server construction remains fail-closed. Replays and
mismatches are denied.

Approval APIs bind verified JWT actor/role claims to active PostgreSQL users and
roles. Caller-provided identity headers have no effect. Tests cover ticket
update and creation, rejection, material edits requiring a separate approval,
concurrent approve/reject decisions, transactional rollback, expiry, mismatch,
replay, exactly-once execution, authenticated HTTP roles, and checkpoint
reconstruction.

Authoritative promotion uses a recoverable state machine:

1. Lock and verify the exact database version ID, stable document ID, version
   label, checksum, approval, actor, and request ID.
2. Persist `staging`; upsert the new Qdrant point with `active=false`; persist
   `staged`.
3. Hide the superseded Qdrant version.
4. Atomically change PostgreSQL authority, consume approval, audit, and persist
   `committed`.
5. Publish the new point and persist `published`.

No new content is visible before PostgreSQL commits. Pre-commit failures leave
inactive staged content; post-commit failures leave a recoverable `committed`
version. Same-request retries are idempotent, other request IDs are rejected,
and concurrent requests have one owner. Public execution routes through the MCP
Gateway and genuine Knowledge MCP tool, followed by lifecycle re-verification.

Tests cover successful supersession, authorization, mismatch, replay, Qdrant
staging/publication failures, PostgreSQL commit failure, recovery, concurrency,
auditing, and active-only Qdrant visibility.

Final acceptance on 2026-10-26 additionally reconstructs a fresh SQLAlchemy
session and `KnowledgeLifecycleService` after an injected post-commit Qdrant
publication failure. The fresh runtime reads `committed` from PostgreSQL,
publishes the still-inactive deterministic Qdrant point, records `published`,
and proves subsequent same-request retry is idempotent while a different request
ID is rejected.
