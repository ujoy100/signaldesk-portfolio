# Phase 3 — Hybrid RAG Retrieval

**Status:** DONE  
**Last validated:** 2026-10-25

## Implemented retrieval pipeline

`TelecomRetriever` implements four comparable strategies:

1. Qdrant dense vector retrieval.
2. BM25 keyword retrieval over the Qdrant-filtered eligible corpus.
3. Hybrid reciprocal-rank fusion of dense and keyword rankings.
4. Hybrid retrieval followed by a deterministic cross-signal reranker combining
   fused rank, meaningful query/document coverage, phrase evidence, and exact
   policy identifier preservation. This is the offline equivalent-reranking
   baseline permitted by the frozen cross-encoder-or-equivalent requirement.

Qdrant filters enforce active/version/service/category constraints and access
role intersection before results are eligible. Public callers cannot retrieve
the internal credit runbook; a support-agent scope can.

Every evidence result includes document ID, stable chunk ID, fictional source,
title, section, optional page, version, service, category, content, retrieval
signals, and the measured retrieval score. No LLM-generated confidence score is
used.

No-answer behavior requires the configured score threshold, at least 40%
meaningful query-term coverage, and exact presence of any queried policy/code
identifier. This corrects the earlier permissive any-token overlap defect and
prevents normalized BM25/RRF scores from manufacturing evidence.

## Benchmark

The expanded benchmark contains 10 positive and 4 unsupported queries,
including paraphrases, distractors, an inactive legacy version, restricted
knowledge, unknown policy identifiers, Mars service, and Neptune network
questions. It reports recall@3, MRR, and no-answer accuracy.

Observed baseline on 2026-10-25:

| Strategy | Recall@3 | MRR | No-answer accuracy |
|---|---:|---:|---:|
| Vector | 1.0000 | 0.9000 | 1.0000 |
| Keyword | 1.0000 | 1.0000 | 1.0000 |
| Hybrid | 1.0000 | 1.0000 | 1.0000 |
| Hybrid + reranking | 1.0000 | 1.0000 | 1.0000 |

The previous live defect returned mobile troubleshooting for the unsupported
Mars question in keyword, hybrid, and reranked modes (reranked score 0.8000).
After the evidence-gating correction, all four modes return explicit no-answer.
Both SIM activation paraphrases rank the activation guide first after reranking.

These values describe only a 14-case fictional baseline. They must not be
interpreted as production quality or statistical generalization. Deterministic
embeddings remain test-only; production embedding/cross-encoder selection still
requires later evaluation.

## Acceptance

Phase 3 is DONE for the frozen scope stated by the user: dense, BM25, hybrid,
equivalent reranking, filters, citations, no-answer behavior, and four-strategy
benchmark are implemented and validated. Production model selection and a
larger statistical evaluation remain later-phase work, not hidden blockers.

## Runtime retrieval investigation — 28 October 2026

The reported mobile-data no-evidence response could not be reproduced after the
Compose restart. Read-only inspection found the green `telecom_knowledge`
collection at 384 dimensions with 15 persisted points, 14 active points, 15
document IDs, and the expected public/support-agent scopes. PostgreSQL held nine
knowledge documents and nine versions: seven active/published and two
draft/unpromoted. Qdrant had no explicit payload indexes; this is acceptable for
the current 15-point development corpus and did not prevent authorization
filtering, but should be revisited for production scale.

The exact reported question returned `guide-network-001` at 0.840909 through a
direct retriever call. A full FastAPI → LangGraph → Qdrant request returned one
citation, 0.8409 confidence, and `insufficient_evidence=false`. Public plus
`support_agent` filtering retained the evidence, and LangGraph preserved it.
Because the failed request had no retained correlation diagnostics, its exact
historical cause is unconfirmed; current evidence rules out a persistent vector,
threshold, role-filter, version, or downstream-processing defect. No collection,
threshold, authorization, or persistent data was changed. An exact-query
regression test now protects this behavior.
