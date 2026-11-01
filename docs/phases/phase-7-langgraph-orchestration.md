# Phase 7 — LangGraph orchestration

**Status: DONE (2026-10-25).**

`backend/app/workflow/graph.py` implements the frozen deterministic sequence as a
genuine `StateGraph`: classification, hybrid retrieval, tool determination,
customer lookup, ticket history, evidence aggregation, strict resolution,
conditional approval, execution, audit, and final response. Operational reads
use `MCPGateway`; graph nodes never query customer or ticket tables directly.

The graph accepts an injected retriever, Gateway, session factory, and
checkpointer. Production API construction uses the official
`langgraph-checkpoint-postgres` `PostgresSaver`; its returned `thread_id` is the
checkpoint key. Conversation state remains separate from authoritative telecom
tables. Empty retrieval and unavailable dependencies produce explicit safe
outcomes. Controlled actions interrupt before Gateway-only execution.

Important files are `backend/app/workflow/graph.py`,
`backend/app/api/routes/support.py`, and
`backend/tests/test_support_workflow.py`.

Acceptance evidence includes real `AsyncPostgresSaver` interruption, disposal,
fresh graph/checkpointer reconstruction, same-thread approval resumption, missing
checkpoint recovery, and a repeated-resume assertion proving the graph does not
execute the controlled action twice. Authenticated submission/resume is covered
through FastAPI. Checkpoint DDL is provisioned explicitly with
`python -m backend.scripts.setup_checkpoints`, never during ordinary requests.
