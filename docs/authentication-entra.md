# Microsoft Entra authentication

**Enhancement status: DONE (28 October 2026).** Real Entra login, database role
mapping, an authenticated LangGraph investigation, logout, and the isolated
session/RBAC security suite have been verified. Frozen phase statuses are
unchanged.

SignalDesk uses single-tenant OIDC Authorization Code Flow with PKCE. FastAPI owns the redirect and callback; the browser receives only a random `HttpOnly` session cookie, never an Entra access or ID token. PostgreSQL remains authoritative for active status and the `support_agent`, `supervisor`, or `admin` application role.

## Local configuration

Keep the existing client secret in `secrets/entra_client_secret.txt` (ignored by Git). Do not paste it into a command, `.env`, frontend variable, image, or Compose file. Put only these non-secret identifiers in the ignored root `.env`:

```dotenv
ENTRA_TENANT_ID=<tenant UUID>
ENTRA_CLIENT_ID=<application/client UUID>
ENTRA_CLIENT_SECRET_FILE=secrets/entra_client_secret.txt
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:5173
COOKIE_SECURE=false
```

The opt-in `compose.entra.yaml` overlay mounts the same secret as `/run/secrets/entra_client_secret`; committed Compose files contain no secret value, and ordinary fictional CI does not require the Entra secret. Start Entra-enabled local services with `docker compose -f compose.yaml -f compose.entra.yaml up -d`. Apply the migration with `DATABASE_URL=<safe target> uv run alembic upgrade head`, then provision checkpoint tables separately as before.

## Explicit identity and role bootstrap

Entra users receive no automatic role. First create or select an active application user with a reviewed role, obtain that user's Entra **Object ID** from the tenant administration UI, and explicitly link it:

```bash
uv run python -m backend.scripts.link_entra_identity --user-id <application-user-id> --entra-subject <entra-object-id>
```

The command does not accept a role, email-derived privilege, password, or client secret. It refuses missing/inactive users and duplicate mappings. Use the same reviewed process for the first administrator; the application does not map Entra Global Administrator or email domains to SignalDesk Admin.

## Request security

- Login transactions are ten-minute, single-use PostgreSQL records binding random state, nonce, and an S256 PKCE verifier.
- Callback validation pins the tenant issuer, application audience, signature/JWKS, expiration, nonce, and tenant ID.
- Session and CSRF secrets are random; only SHA-256 hashes are stored. Mutating API calls require the session plus `X-CSRF-Token`.
- Sessions are checked against expiry, revocation, active user, and current database role on every request. Logout revokes server state and clears both cookies.
- Development JWTs remain available for fictional local/CI acceptance but are rejected when `APP_ENV=production`.
- Production startup requires `COOKIE_SECURE=true`. Deploy frontend and API behind one HTTPS site (for example, a Vercel rewrite/proxy to Render under the frontend origin) so the host-only `SameSite=Lax` cookie remains first-party. Do not change it to a cross-site JavaScript token design.

## Authentication routes and authorization boundaries

`create_app()` mounts five `APIRouter` instances. Authentication routes are
`GET /auth/login`, `GET /auth/callback`, and `POST /auth/logout`; authenticated
application identity is exposed by `GET /api/v1/session`. Support, approval,
knowledge, feedback, and operational routes remain under `/api/v1`.

FastAPI 0.151 stores included routers as lazy internal `_IncludedRouter`
objects. Their direct `.path` is `None`, so scripts that iterate `app.routes`
and filter on `route.path` omit every included endpoint. The route-specific
`APIRouter.routes` collections and `app.openapi()["paths"]` contain the actual
endpoints. This is inspection behavior, not a routing defect.

On successful callback, FastAPI stores only SHA-256 hashes of the random
session and CSRF values in PostgreSQL. `POST /auth/logout` authenticates the
session and CSRF header, sets `revoked_at`, and deletes both browser cookies.
The old cookie cannot authenticate again because every request filters out
revoked and expired session records.

The validated ID token's optional `name` claim is normalized to 150 characters
and copied into that browser-session record. `GET /api/v1/session` returns this
verified session display name together with `actor_id` and the PostgreSQL role.
If Entra omits or empties `name`, the API returns `Microsoft user`; it never
falls back to email, Object ID, token content, or an unverified browser value.
React keeps the returned profile only in component memory, clears it on logout,
and replaces it on account changes. Existing sessions created before migration
`2d4f8a71c930` use the safe fallback until the user signs in again.

Role authority is independent of Entra identity mapping: `external_identities`
maps tenant/Object ID to a user, while `users.role_id` supplies the current
application role. Support Agents can submit support work and feedback but
cannot list or decide approvals or administer knowledge. Supervisors can
review controlled approvals but do not gain Admin knowledge-list privileges.
Admins receive the explicitly assigned administrative capabilities. FastAPI,
LangGraph, the MCP Gateway, and approval services retain their independent
checks.

## Live verification

After migrations and an explicit identity link:

1. Start the backend and frontend with the ignored local configuration.
2. Open `http://localhost:5173` and choose **Sign in with Microsoft**.
3. Confirm Entra shows `SignalDesk-Telecom-Dev` in the expected tenant.
4. After redirect, verify the role-aware navigation matches the database role.
5. Perform a harmless support query, sign out, and confirm refresh cannot restore the revoked session.
6. Confirm an unlinked tenant user is denied and a support agent cannot access approval or knowledge-administration routes.

Real interactive Entra login was verified manually on 28 October 2026 with a
database-linked Support Agent. The investigation completed with grounded
evidence and citations, logout returned to the login page, and an unauthenticated
session request returned HTTP 401. No real credential values are recorded.

## Security validation evidence

The isolated PostgreSQL API suite proves that logout persists revocation,
cookie replay returns 401, missing CSRF returns 401, expired sessions return
401, and production development-JWT authentication is rejected. It also proves
that a valid Support Agent session receives 403 for approval access and
knowledge promotion, decision, upload, and deactivation attempts, with approval
and knowledge-version counts unchanged. Production callback cookie tests require
`Secure`, `HttpOnly`, and `SameSite=Lax` on the session cookie.

Final display-name and retrieval validation on 29 October 2026: the focused
Entra/session/auth/RBAC/retrieval suite **33 passed**; the full backend suite
**128 passed, 1 intentionally skipped**, Ruff formatting and lint passed, the
Entra Compose overlay validated, and `git diff --check` passed.

Display-name extension validation: verified-name extraction and missing-name
fallback, authenticated session output, expiry/revocation, account switching,
and RBAC were added to the existing suites. Roles remain exclusively controlled
by `users.role_id`; the Microsoft name claim is presentation data only.

## Safe callback diagnostics

Callback failures remain generic in the browser. Backend warnings expose only
an allowlisted stage, exception category, HTTP status, provider error category,
and AADSTS code. They never include authorization codes, tokens, cookies,
client secrets, PKCE verifiers, nonce values, or raw provider responses.

`invalid_client` / `AADSTS7000215` occurs during the authorization-code
exchange, before ID-token signature or claim validation. Replace the ignored
secret file with the Entra client-secret **Value** for this application (not
the Secret ID), then recreate only the backend with the Entra Compose overlay.
An expired secret must be rotated in Entra first. Never paste the value into a
shell command or committed environment file.

## Operational limitations

Session cleanup is opportunistic for login transactions; a scheduled retention job should remove expired/revoked sessions before production scale. Microsoft JWKS retrieval depends on provider availability and fails closed. Client-secret rotation is an external Entra/deployment operation; restart instances after rotating the mounted secret.
