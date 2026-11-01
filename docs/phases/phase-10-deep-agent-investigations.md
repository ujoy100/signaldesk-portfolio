# Phase 10 — Bounded Deep Agents investigations

**Status: DONE.** Deterministic acceptance and a genuine OpenAI-backed complex
investigation passed on 2026-10-26 using `openai:gpt-4.1-mini`.

## Architecture

`SupportWorkflow.classify_issue` assigns an issue type and a `simple` or
`investigation` complexity. Normal SIM activation and other simple cases retain
the deterministic LangGraph route. Repeated roaming, billing, or network cases
that require multiple records or policy/history review branch to
`investigate_complex_issue`, then return a strict `InvestigationResult` to the
existing structured-resolution and controlled-action path.

`DeepAgentInvestigator` calls the official `deepagents.create_deep_agent` API.
It exposes only seven read-only Knowledge, Customer, and Ticket MCP operations,
all routed through the MCP Gateway. Deep Agents filesystem, shell, task, todo,
and editing tools are excluded by a harness profile; no controlled ticket or
knowledge operation is offered. Model-call, tool-call, recursion, timeout, and
input-size budgets bound execution.

Every MCP result is validated against its Pydantic contract. User and tool text
is PII-redacted and enclosed in explicit untrusted-data boundaries before model
use. The returned evidence is reconstructed from validated Gateway responses;
model-authored evidence is never promoted to authoritative workflow state.
Citations are intersected with collected evidence IDs. No validated evidence
forces `insufficient_evidence`.

## Test mode and acceptance evidence

Offline CI injects a clearly separate deterministic `InvestigationRunner`. It
tests routing, strict contracts, tool restrictions, unavailable dependencies,
timeouts/budget exhaustion, invalid structured output, and safe fallback. This
mode is not represented as a model run.

Focused validation: **21 passed in 1.47s** (Phase 10/11 workflow, security and
Gateway group). Final full backend validation: **103 passed in 2.81s**.

## Genuine model acceptance

The opt-in test loads `OPENAI_API_KEY` as `SecretStr` and
`DEEP_AGENT_MODEL` through Pydantic settings. It uses repeatable fictional
PostgreSQL seed records and an isolated in-memory Qdrant collection. The test
ran LangGraph → official Deep Agent → genuine OpenAI model → authorized MCP
Gateway → real Knowledge/Customer/Ticket MCP servers → validated authoritative
evidence → `InvestigationResult` → LangGraph resolution.

The final model run passed in **8.77s**. Runtime assertions confirmed customer
plan and ticket-history evidence collection, non-empty authoritative evidence,
citations bound only to collected evidence IDs, at most six tool calls, no
controlled operation, and completion without a ticket draft. A normal SIM
activation question remained on the deterministic route and made no additional
Gateway/Deep Agent calls.

Two compatibility findings were fixed during acceptance: concurrent MCP reads
now use independent database sessions in the integration test, and model
narrative output is separated from authoritative evidence/tool-call records.
UUID evidence IDs are preserved during PII redaction. Model-authored evidence or
tool names can therefore never become operational authority.

The real test is intentionally gated by `RUN_PHASE10_MODEL_TEST=yes`; ordinary
offline CI skips it to avoid external calls and cost. Credentials are never
printed, logged, committed, or included in test output.
