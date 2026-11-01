# Phase 2 — Qdrant Knowledge Ingestion

**Status:** DONE  
**Completed:** 2026-10-25  
**Scope:** Qdrant, embeddings, metadata, and deterministic ingestion.

## Implementation

The Phase 2 knowledge store is separate from PostgreSQL. PostgreSQL remains the
transactional system of record; Qdrant stores embedded fictional support
knowledge and retrieval metadata.

- `backend/data/knowledge/fictional_telecom.json` contains six fictional source
  documents covering FAQs, SIM activation, roaming, billing, network
  troubleshooting, and an access-restricted internal runbook.
- `TelecomKnowledgeLoader` implements LangChain's loader contract and validates
  each record with Pydantic before producing LangChain `Document` objects.
- `RecursiveCharacterTextSplitter` performs deterministic document chunking.
- `DeterministicTelecomEmbeddings` implements LangChain's `Embeddings` contract
  with credential-free feature hashing and telecom aliases. It is an offline
  baseline, not a production semantic model claim.
- Qdrant point IDs are UUID5 values derived from document ID, version, chunk
  index, and content hash. Reingestion upserts stable IDs.
- Existing collections are never recreated. A vector-dimension mismatch fails
  safely and requires an explicit migration decision.

## Metadata contract

Each point stores document ID, source, service, category, version, active flag,
access roles, page, section, title, chunk index, and content. Metadata supports
auditable evidence and Qdrant-side filtering.

## Configuration

Environment variables are documented in `.env.example`:

- `QDRANT_URL` (default `http://127.0.0.1:6333`)
- optional `QDRANT_API_KEY` supplied only through the environment
- `QDRANT_COLLECTION`
- `EMBEDDING_DIMENSIONS`

Dependencies: LangChain 1.4.7, LangChain Core 1.7.0, LangChain Text Splitters
1.1.3, and Qdrant Client 1.20.0.

## Validation

- Isolated in-memory Qdrant tests verify metadata and stable repeat ingestion.
- A temporary official Qdrant Docker server accepted two consecutive ingestion
  runs, both reporting 6 documents and 6 chunks.
- A server-backed query returned `policy-roaming-001`; the temporary container
  was then stopped and automatically removed.
- No external embedding service or credential was required.

## Limitations

- The compact corpus produces one chunk per current document. The splitter is
  ready for longer documents, but production chunk tuning is future work.
- The deterministic embedding baseline prioritizes reproducibility and offline
  development. Selecting and evaluating a production embedding model belongs
  in a later model/evaluation decision.
- Docker Compose remains Phase 16; Phase 2 does not introduce stack
  orchestration.
