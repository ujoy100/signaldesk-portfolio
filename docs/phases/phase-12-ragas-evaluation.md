# Phase 12 — RAGAS and agent evaluation

**Status: DONE (2026-10-26).**

The versioned `fictional-telecom-eval:1.0.0` dataset contains 40 cases across
SIM, roaming, billing, plans, network, tickets, abstention, restricted content,
prompt injection, PII and approval safety. Deterministic retrieval metrics are
kept separate from genuine RAGAS LLM-as-judge metrics.

Offline metrics and gates are Recall@3 ≥ 0.75, MRR ≥ 0.75, unsupported-question
abstention ≥ 0.80, and authorization, approval and schema safety = 1.0. The
measured result was Recall@3 **0.7895**, MRR **0.7895**, abstention **0.8333**,
and all three safety metrics **1.0**. Runs can be persisted in the existing
`evaluation_runs` and `evaluation_scores` tables with model, prompt, retriever,
dataset and knowledge versions.

The explicitly opted-in genuine RAGAS 0.3.9 run was capped at two fictional
cases. With `openai:gpt-4.1-mini`, it measured context precision **1.0**,
context recall **1.0**, faithfulness **1.0**, and answer relevancy **0.498**.
This small paid smoke run proves real metric execution, not statistical coverage.
The provisional smoke thresholds are 0.90 for context precision/recall and
faithfulness and 0.45 for answer relevancy; Phase 17 should use a larger,
budget-reviewed sample before making these RAGAS scores a release gate.

RAGAS 0.3.9 has one legacy optional VertexAI import incompatible with
LangChain Community 0.4.2. The opt-in loader supplies an isolated unavailable
VertexAI placeholder; the OpenAI metrics themselves are genuine and unmodified.

## Production dependency boundary

RAGAS remains the frozen evaluation framework, but it is now installed through
the explicit `evaluation` dependency extra rather than the production API
dependency set. The backend Dockerfile's `evaluation` target includes RAGAS and
its `diskcache` transitive dependency; the production `runtime` target asserts
that neither package is installed. Ordinary CI installs the extra to preserve
all evaluation tests, while a separate production export is vulnerability
audited without optional evaluation packages.

This boundary contains, but does not conceal, two advisories in the optional
toolchain: RAGAS 0.3.9 `GHSA-95ww-475f-pr4f` (`PYSEC-2026-3046`) and
diskcache 5.6.3 `GHSA-w8v5-vhqr-4h9v` (`PYSEC-2026-2447`). Neither advisory
currently has an upstream fixed version
compatible with the frozen RAGAS requirement. The evaluation environment must
therefore remain opt-in, use fictional inputs, and never serve production API
traffic.
