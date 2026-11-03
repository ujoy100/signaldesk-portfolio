# SignalDesk: four-minute working demonstration

This is a local fictional-data demonstration, not a production deployment.
Earlier Debian backend images reported **46 HIGH findings / 10 CVEs** and
later **45 HIGH findings / 9 CVEs**. These findings remain documented as
historical evidence in [demo evidence](demo-evidence.md).

On November 3, 2026, the public Alpine backend and patched frontend passed
the unchanged strict Trivy HIGH/CRITICAL gate. Post-merge CI and browser
acceptance also passed on public `main`.

This remains a fictional-data portfolio demonstration, not a production-
approved deployment. Phase 17 is IN PROGRESS; Phases 18–19 are PENDING.

## Fresh local setup

Requirements: Git, Python 3.13 and Docker Desktop/Compose. Host Node/uv are needed
only for source development or running tests, not for viewing the Compose UI.
Run from the public `signaldesk-portfolio` checkout:

```bash
python3 -m backend.scripts.prepare_local_demo
docker compose config --quiet
docker compose build backend frontend
docker compose up -d --no-build --pull never --wait
docker compose --profile tools run --rm --pull never seed
docker compose ps --all
```

Preparation creates only missing example configuration and two random secret
files with mode 0600. It never overwrites or prints existing credentials. If an
existing volume’s password file is missing, restore the original file before
running preparation. Never remove/reset a volume to fix a password mismatch.
Seeding is an explicit setup step: it upserts the fictional catalog and
knowledge. Do not run it repeatedly to reset an established demonstration.

The public project name is `signaldesk-portfolio`. It uses its own Compose-named
volumes and a project-scoped backend image tag. API, migration, checkpoint and
seed services share that image, preventing an older migration image from falling
behind the API schema. Rebuild the backend once after code/migration changes,
then run `up` so Compose recreates services from that image. Do not use `start`
to apply changed images/configuration. A pre-existing public stack created under
the old `telecom-agentic-ai-support` project name is not automatically migrated;
leave it untouched and explicitly select the new project.

Open http://localhost:5173 and http://localhost:8000/ready. PostgreSQL and Qdrant
are private to the Compose network. Both the original and public UI/API defaults
use ports 5173/8000: do not run conflicting UI/API pairs on those ports. Do not
stop or alter the private development stack without its owner’s authorization.

For an already-built checkout, omit `build`. Stop only this public stack with:

```bash
docker compose down
```

This preserves volumes. Never add `-v`, prune resources or reset a database.

## Before recording

Use fictional development access only, with a fresh browser session. Obtain a
short-lived token privately for each role using:

```bash
docker compose exec -T backend python -m backend.scripts.issue_development_token support_agent
docker compose exec -T backend python -m backend.scripts.issue_development_token supervisor
docker compose exec -T backend python -m backend.scripts.issue_development_token admin
docker compose exec -T backend python -m backend.scripts.issue_development_token ticket_id
```

Tokens expire after ten minutes. Paste only into the local login form. Do not
record the terminal, token entry, browser storage, network headers or traces.
Start recording after successful login; the UI clears the token input.
The final command returns the fictional `FIC-TKT-001` internal ID. Approval
steps below modify that fictional ticket and append audit records; do not run
them against customer data. Use a freshly prepared public demo stack when possible.

## Recording script: 3–5 minutes

| Time | Show and do | Explain |
|---|---|---|
| 0:00–0:30 | Show the support workspace signed in as the fictional Support Agent | React calls FastAPI; the database owns the role. Development token access is not Microsoft sign-in. |
| 0:30–1:15 | Submit “How do I recover the PUK for my locked fictional SIM?”; open one evidence card’s Technical details | A real LangGraph route calls the MCP Gateway; hybrid keyword/vector retrieval returns versioned fictional knowledge. Explain the evidence-strength indicator is not measured real-world accuracy. |
| 1:15–1:40 | Submit a feedback rating/comment; show “Feedback recorded.” | Feedback is persisted against the workflow thread. |
| 1:40–2:15 | Enter the fictional ticket ID, select “Propose a controlled ticket action”, then submit “Apply the cited SIM activation guidance and resolve this fictional ticket” | The workflow pauses for human approval rather than immediately writing to PostgreSQL. Support Agents cannot approve the action. |
| 2:15–3:15 | Pause recording for role switching. Sign in as fictional Supervisor, open Approvals, edit the proposed priority/status and submit for reauthorization. Approve the new replacement record | A material edit invalidates the old approval. The authorized resume executes through the Gateway. Show the final Executed status. |
| 3:15–3:45 | Switch to fictional Admin off-camera; show Knowledge lifecycle and Feedback history | Role-aware operational views reflect real API/database records. This segment demonstrates listing, not a new knowledge promotion. |
| 3:45–4:00 | Return to README security/limitations | Local functionality and public container CI validation are demonstrated; cloud deployment and production approval remain pending. |

These are real application operations. Do not replace responses with browser
routes/mocks, edit DOM content or add invented model output for the recording.
No recording is supplied by this PR; this is the production plan for one.

## Optional genuine Deep Agents segment

Deep Agents remains implemented and is not removed or replaced. It is optional
for the default demo because it requires paid provider access and nondeterministic
latency. Configure ignored `OPENAI_API_KEY` and `DEEP_AGENT_MODEL` as documented;
never put them in frontend variables. After changing container environment, use
`docker compose up -d --no-build --pull never --wait` to apply configuration.

With fictional customer and ticket IDs, submit:
“Investigate repeated fictional roaming failures using customer plan eligibility,
ticket history, and roaming policy.” Show the Bounded Deep Agent badge and
customer/ticket/knowledge evidence. An insufficient-evidence result is a valid
safety outcome; do not advertise a confirmed root cause when data does not prove it.
Without provider configuration the complex route fails closed. The deterministic
four-minute demo does not require provider credentials or the evaluation extra.

## Optional Microsoft Entra segment

Follow [Entra setup](authentication-entra.md), retain the ignored client secret,
and use the existing `compose.entra.yaml` overlay. Entra identity must already
be explicitly mapped to an active application user; roles are not self-assigned.
Do not weaken RBAC to obtain a demonstration. Record only the application after
successful sign-in; keep personal account details, MFA and provider pages off-camera.
Interactive sign-in/logout must be personally verified before claiming this segment.
The default fictional-token walkthrough does not demonstrate an Entra session.

## Validation and evidence

The PR’s backend job runs the full regression suite with disposable PostgreSQL/
Qdrant, Alembic and checkpoint provisioning, deterministic evaluation and audits.
The browser job builds the real stack, verifies the shared runtime image IDs,
runs `backend.scripts.verify_compose_acceptance` (real HTTP, role denial,
material-edit authorization, knowledge publication and exactly-once ticket events),
and runs Chrome Playwright. The positive demo flows use live services; one
existing negative browser test deliberately aborts a request to test outage UX.

Only these six screenshot paths are retained from a successful hosted browser run:
login, support, approval, knowledge, feedback and mobile under `docs/screenshots/`.
The isolated browser stack disables provider credentials and uses synthetic data.
The artifact contains no traces, HAR, video, environment files or logs; retention
is seven days. Review the artifact before promoting screenshots into the README.
Checked-in screenshots are reviewed captures with their source SHA recorded in
the evidence document; they are not automatically replaced by a new workflow run. See [demo evidence](demo-evidence.md).

Docker-free source checks (after `uv sync --frozen` / frontend `npm ci`):

```bash
uv run ruff check backend
uv run ruff format --check backend
uv run pytest backend/tests/test_prepare_local_demo.py -q
npm --prefix frontend test
```

Other backend integration tests require only the explicitly isolated
`telecom_test_db`; never point write tests at the demonstration database. The
optional RAGAS extra is for evaluation tooling, not application startup.
