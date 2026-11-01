# Phase 6 — MCP Gateway

**Status:** DONE  
**Validated:** 2026-10-25

`MCPGateway` registers the three namespaces and routes every invocation through
the official MCP `Client`; it does not call tool functions directly.

Controls include environment-keyed JWT authentication, role/namespace policy,
tool discovery before invocation, request UUIDs, bounded timeout, one safe
read retry, structured errors, and audit callbacks. A database audit writer
persists decisions without tool arguments or tokens. Unsupported tools,
unavailable namespaces, invalid arguments, unauthorized roles, and ticket-write
approval bypass attempts are explicitly denied.

Controlled writes are never retried and are denied even if a caller claims an
approval was verified. Phase 9 must supply the trusted verification/resumption
interface before that policy can change.
