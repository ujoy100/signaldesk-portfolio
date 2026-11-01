# Phase 8 — Structured outputs

**Status: DONE (2026-10-25).**

`backend/app/schemas/support.py` defines strict, extra-forbidden Pydantic
contracts for requests, responses, evidence, ticket drafts, decisions, and the
frozen `SupportResolution`. Cross-field validators reject contradictory action
flags and non-zero confidence for insufficient evidence.

Confidence is deterministic: the mean of available retrieval scores and
validated successful tool signals, or zero without evidence. Knowledge evidence
preserves source ID, document ID, version, score, and signals. No production LLM
is claimed; the current generator is explicitly deterministic.

Tests cover valid insufficient evidence, confidence bounds, contradictory
actions, unexpected fields, cited graph output, malformed customer/ticket
outputs, unavailable tools, and instruction-like extra fields. External MCP
results are validated against strict tool-specific contracts before state
updates; rejected output cannot affect routing or authorization.
