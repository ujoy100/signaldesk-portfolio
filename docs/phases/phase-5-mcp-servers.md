# Phase 5 — Telecom MCP Servers

**Status:** DONE  
**Validated:** 2026-10-25

Three genuine official-SDK `MCPServer` instances expose the frozen tools:

- Knowledge: `search_knowledge_base`, `get_policy`, `get_source_details`.
- Customer: `get_customer_profile`, `get_customer_plan`,
  `check_roaming_status`, `check_data_service_status`, `get_active_services`.
- Ticket: `get_ticket`, `get_ticket_history`, `draft_ticket_update`,
  `update_ticket`, `create_ticket`.

Tests use the official MCP `Client`, negotiate a real in-memory MCP connection,
discover tools, invoke them through `tools/call`, and validate structured
Pydantic output. Customer and ticket data comes from PostgreSQL fictional seed
records. Invalid arguments and missing records return MCP errors.

Ticket create/update are server-side fail-closed even when an approval ID is
supplied. Drafting is non-executable. Phase 9 must provide verified resumable
approval execution before these tools can mutate data.

The servers are intended to be registered behind the Gateway. Direct network
exposure is not configured in this phase.
