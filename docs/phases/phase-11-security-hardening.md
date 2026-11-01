# Phase 11 — Security hardening

**Status: DONE.** The Phase 11 controls were reviewed and validated on
2026-10-26. Prompt injection remains a residual model-system risk; protection
is defense in depth, not a claim that heuristic filtering solves it.

## Enforced trust boundaries

- JWT signature, audience, expiry and required claims are verified. Support API
  claims must match one active PostgreSQL user and role.
- Support Agent, Supervisor and Admin permissions are enforced at API,
  approval-service and MCP Gateway boundaries. The production Gateway performs
  its own active database identity/role check.
- Normal retrieval and Deep Agent knowledge tools force active-only retrieval
  with `public` plus the verified database role. Callers and model output cannot
  expand the access role.
- Customer-role callers cannot use support/customer/ticket namespaces. Forged
  roles and inactive identities fail before MCP routing.
- Controlled ticket writes and knowledge promotion retain exact-scope,
  single-use, audited human approval at both Gateway and server/service layers.
- User messages and tool output are untrusted data, PII-redacted before model
  calls, strictly validated, and separated from trusted system instructions.
- A Deep Agent has no write, approval, shell, filesystem or subagent tool.
  Therefore injected content cannot add a tool or bypass the deterministic
  LangGraph approval route.
- Gateway audit events record identifiers, role, tool, outcome and safe error
  codes—not arguments, JWTs, credentials or customer payloads. Public failures
  use bounded error codes rather than leaking dependency details.
- Secrets remain environment/deployment configuration. `.env.example` contains
  only non-secret settings and an optional model-name example.

## Validation and residual risk

Tests cover forged/inactive roles, invalid/expired JWTs, namespace denial,
retrieval role filters, PII redaction, instruction-like malformed MCP output,
read-only tool allowlists, invalid structured model output, approval mismatch
and replay, and dependency failure. Existing Phase 9 tests continue to cover
approval concurrency and exactly-once execution.

Untrusted-content tags and redaction are not the sole prompt-injection defense.
The primary controls are capability restriction, independent authorization,
strict contracts, authoritative evidence reconstruction, deterministic routing,
and approval-gated writes. A sufficiently capable model may still summarize
malicious evidence poorly; its narrative is advisory and cannot directly mutate
operational state. Phase 12 evaluations should add an adversarial corpus, while
Phase 13 should monitor denial and injection signals without recording PII.
