# SignalDesk frontend

React 19 + Vite 8, JavaScript/JSX operations workspace for the SignalDesk FastAPI
backend. Includes support investigations and citations, exact-scope approvals,
knowledge lifecycle, evaluation history and linked feedback with role-aware
navigation. Microsoft sign-in uses the backend's Entra OIDC flow and revocable
cookie sessions; local fictional token login stays in memory. Interactive Entra
acceptance remains outstanding.

The SignalDesk mark and login/workspace backgrounds are original HTML/CSS.
No third-party hero image, font service or image request is needed. Historical
artwork remains subject to [provenance review](../docs/provenance.md).

```bash
# From repository root
npm --prefix frontend ci
cp frontend/.env.example frontend/.env
npm --prefix frontend run dev
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Configure `VITE_API_BASE_URL` for local FastAPI. All `VITE_` values are public:
never put secrets there. Production builds keep development login off unless
explicitly enabled; the backend independently rejects development JWTs in
production. See [Entra configuration](../docs/authentication-entra.md).

Vitest/Testing Library mock HTTP transport. Playwright uses installed Chrome
against the real fictional Compose backend and performs business writes; use
isolated acceptance services/data, never development or production databases.
The responsive layout supports mobile; screenshot evidence is in
[docs/screenshots](../docs/screenshots). The UI is not cloud-deployed.

See the [root README](../README.md) for architecture, Docker setup, CI status,
security, evaluation limitations and rights. Preserve the frozen React/Vite
stack; do not regenerate this application from a starter template.
