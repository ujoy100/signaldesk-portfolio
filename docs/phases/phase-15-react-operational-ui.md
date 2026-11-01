# Phase 15 — React operational UI

**Status: DONE (27 October 2026).** Implementation, component tests, production build, manual browser acceptance, real Compose HTTP acceptance, and automated Playwright acceptance with installed Google Chrome all pass.

## Architecture and security

`frontend/src/api/client.js` is the single typed-by-contract request boundary. It applies a 30-second timeout, bearer authentication, consistent safe errors, and correlation-ID display. The browser receives only the public `VITE_API_BASE_URL`; provider credentials never enter the bundle.

The backend has no credential-exchange or secure-cookie endpoint. The compatible design therefore accepts an already issued short-lived JWT and keeps it only in React memory. It is never written to local or session storage and disappears on refresh/logout. `/api/v1/session` verifies the signature and binds identity and role to the active PostgreSQL user before rendering role-aware navigation.

The UI provides support issue entry, optional authorized customer/ticket IDs, structured resolutions, an evidence-strength indicator, readable evidence/citations and ticket timelines, next steps, server-derived deterministic/Deep-Agent mode, approval-pending state, approval/rejection, material edits with reauthorization, knowledge promotion request/decision/execution, persisted evaluation runs, and authenticated feedback. React never calls a ticket or knowledge datastore directly. Controlled execution remains behind FastAPI, the approval service, LangGraph, and MCP Gateway.

Approval cards use authoritative read-only ticket state from PostgreSQL to show ticket number, current/proposed status and priority, unchanged fields, expiry, and context. Constrained status/priority selectors replace JSON editing; raw scope remains under collapsed technical details. Editing still rejects the original exact-scope approval and creates a fresh pending approval. It does not execute a mutation.

The latest resolution lives in React session memory across navigation. Completed resolutions expose inline feedback whose real thread ID is supplied internally, so operators do not copy checkpoint identifiers. Logout clears the token, session, and recent result. Customer/ticket lookup remains numeric because no suitably scoped list API exists; adding one is a documented production UX limitation rather than a frontend-only data source.

## Routes and API mapping

The responsive console has Support, Approvals, Knowledge, Evaluations, and Feedback views. New narrow contracts include `/api/v1/feedback`, knowledge promotion endpoints, and a `workflow_mode` value produced by LangGraph state rather than inferred by React.

Read-only operational list endpoints were added with strict Pydantic response models. They repeat server-side authorization; hiding navigation is convenience, not the security boundary.

## Acceptance evidence

- Vitest: 6 component/integration tests passed (mocked request boundary).
- Playwright: 5 browser tests passed in installed Google Chrome against the real Compose frontend and backend. Coverage includes invalid/expired authentication, safe transport errors, RBAC navigation, SIM citations, automatic feedback, approval edit/replacement/execution, knowledge promotion, supervisor/admin feedback history, mobile layout, and empty browser storage.
- Manual browser acceptance supplied by the user remains separately recorded: SIM activation, 3/5 feedback persistence, approval #4 edited from resolved to in-progress, replacement approval #5 explicitly authorized and executed, and a read-only PostgreSQL check showing ticket 1 in-progress/high.
- Prior real HTTP acceptance separately covers FastAPI, PostgreSQL, Qdrant, LangGraph, MCP Gateway, authorization denial, approvals, promotion, failure degradation, feedback, and persistence.

Sanitized browser screenshots are in `docs/screenshots/phase15-*.png`. They contain fictional development data and were captured only after login; no access token input or secret is visible.

## Limitations

Token-paste login is development-only. Production requires an approved OIDC/SSO design with a secure server-managed session. The development issuer refuses production and only resolves allowlisted active fictional seeded identities; it is a CLI inside the backend container, not a public endpoint. Customer/ticket selection still accepts authorized internal numeric IDs pending a scoped lookup API. Confidence is explicitly presented as evidence strength, not a calibrated probability.
