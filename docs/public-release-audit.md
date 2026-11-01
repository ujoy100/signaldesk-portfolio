# SignalDesk public-release audit — 1 November 2026

Decision: suitable for a reviewed private Git commit after the recorded gates;
**not cleared for public release**. Phase 17 remains IN PROGRESS; Phases 18/19
remain PENDING. No visibility/security settings, secrets, development databases,
history or retained artifacts were changed or deleted.

## Scope and findings

- Fetched every remote branch and all 13 pull-request heads into audit refs.
  Gitleaks 8.24.3 scanned all 25 reachable commits, about 1.75 MB, with default
  rules and **no allowlist**: no findings. Local repository is not shallow.
  Ignored `.env`, frontend `.env`, secret files, caches and builds are excluded;
  tracked configuration consists of example files and the secret README.
- Historical `hero.png` was unused by the current UI and is removed. Exact bytes
  match official Vite v8.3.0 commit `434e8e9495436a60789f2b588a04a6a24a3d1661`.
  [Provenance](provenance.md) records SHA-256 and upstream source. Its notice is
  retained in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), limited to
  third-party material. No SignalDesk MIT/Apache license was added. No artwork
  history rewrite is recommended on this evidence; old snapshots require the
  applicable upstream notice if distributed independently.
- Personal author/committer email exists in history. Its exact value is omitted
  here to avoid further duplication. Actions logs/build records also contain
  personal email metadata (20 archive objects matched personal email patterns).
  Owner must explicitly decide whether this metadata may become public.
- Enumerated **55 Actions runs and 48 retained artifacts**. Downloaded every
  available run log and non-expired artifact; three initial timeouts passed on
  retry. Recursively inspected ZIP/gzip content: 397 archive/payload objects,
  about 9.7 MB extracted, then strict redacted Gitleaks passed. Additional private
  key/provider-key/email/hero-name and exact hero-byte checks found email metadata
  and signed Docker registry CDN URLs; the apparent provider-key match was a
  substring of a signed CDN URL, not an application OpenAI key. No hero bytes or
  hero filename were detected in extracted evidence. Binary formats, external
  caches and already expired/deleted evidence remain coverage limits.
- Seed identities use reserved `example.test` addresses; seed and knowledge data
  are explicitly fictional. Evaluation data is repository-authored synthetic
  material. No real subscriber export was found. Phone-like fixtures are not
  asserted to be reserved/unreachable numbers.
- Visually reviewed six current screenshots: original CSS login, support,
  approval, knowledge lifecycle, feedback and mobile. No visible credentials or
  real customer identities. Corrected the knowledge screenshot test to capture
  the lifecycle screen after promotion, rather than the approvals screen.
- Runtime pip-audit: no known vulnerabilities. Optional evaluation audit fails
  for the existing RAGAS 0.3.9 and diskcache 5.6.3 advisories (duplicate advisory
  rows share the same two IDs); these remain isolated and documented in SECURITY.md.
- Full npm audit initially found minimatch development-only glob amplification.
  Added a targeted `minimatch: 11.0.1` override; locked installation, lint, tests,
  build and full npm audit then passed with zero vulnerabilities. This overrides
  ESLint's transitive major constraint; revisit when upstream supports the fix.
- Reviewed official action release notes/tag commits/manifests and pinned Node 24
  actions; Gitleaks container pinned by registry digest. Disabled checkout token
  persistence, automatic Docker build-record uploads, and Playwright diagnostic
  uploads that could expose authenticated traces. Existing artifacts are retained.
- GitHub confirmed repository remains private. Branch-protection read returned
  HTTP 403 requiring a plan upgrade or public visibility. No setting was changed.

## Validation evidence

| Gate | Result |
|---|---|
| Backend Ruff / formatting | Clean; 133 files |
| Isolated PostgreSQL regression | 128 passed, 1 intentional paid-test skip |
| Alembic current/head/check | `2d4f8a71c930`, single head, no pending operations |
| uv lock | 148 packages, clean |
| Deterministic evaluation | 40 cases, passed; Recall@3/MRR 0.7895, abstention 0.8333, safety/schema 1.0 |
| Genuine Deep Agents acceptance | 1 passed in 8.46s |
| Genuine bounded RAGAS | 2 cases; precision/recall/faithfulness 1.0, relevancy 0.4979 |
| Frontend lint / Vitest / build | Clean / 7 passed / passed |
| Real Chrome Playwright | 5 passed; final screenshot/data-ready rerun recorded in tracker |
| Docker | Runtime, evaluation and frontend image targets built; runtime asserts no RAGAS/diskcache |
| Compose | Separate `signaldesk-release-audit` project; only `telecom_test_db`; fresh audit-only PostgreSQL/Qdrant volumes |
| Actions syntax | actionlint 1.7.7 passed |
| Secrets | All-ref history and downloaded Actions evidence passed strict Gitleaks |
| Dependency audits | Runtime Python and full npm pass; optional evaluation has two retained advisories |

The isolated acceptance stack does not use the development database. No Docker
volume was removed. Host integration tests also explicitly selected only
`telecom_test_db`. The RAGAS runner uses in-memory Qdrant and has a hard two-case
selection in the CLI. Paid credentials were never printed or added to artifacts.

## Remaining limits and manual work

Follow [publication-checklist.md](publication-checklist.md): decide about email
metadata and retained artifacts, verify branch protection/required CI, complete
interactive Entra acceptance, review optional evaluation advisories and complete
Phase 19's separate release requirements. The original full frozen source document
is not present locally; repository phase specifications/tracker governed this work.
RAGAS's deprecated community import and Qdrant client 1.20/server 1.15.5 warning
remain visible and documented, without warning suppression or a frozen-stack swap.
A passing scanner is evidence, not proof of absence of every possible secret.

Full HTTP acceptance also passed: invalid/expired authentication 401, unauthorized
approval 403, edited-action reauthorization, feedback visibility, one promoted
Qdrant point and exactly one ticket event. Staged snapshot credential scanning
and whitespace review passed before commit. Final SHA and hosted run results
are reported after push; they cannot be inferred from earlier green baselines.

## Container OS follow-up

The initial commit `4d11dda` passed hosted CI run `41313577210` and real Compose
browser run `41313577177` with no annotations or retained artifacts. A subsequent
Trivy 0.76.1 scan of the old frontend image found **60 HIGH/CRITICAL OS-package
rows** on Alpine 3.21.3. Language dependency audits did not cover these packages.
The frontend now uses official stable Nginx 1.30.6/Alpine, pinned by manifest digest.
See [upstream release/security notes](https://nginx.org/news.html).

Local follow-up image pulling/backend scanning hit full host storage (about
249 MiB available) and Docker I/O errors. No cleanup/prune/volume removal was
performed. Validation continues on GitHub-hosted runners. CI now loads the built
runtime images and scans both OS/application packages with immutable Trivy
0.76.1, failing on HIGH/CRITICAL findings without ignoring unfixed advisories.
Final scan results and any retained upstream blockers must be reviewed before
claiming container clearance. Local Docker recovery remains an owner task unless
narrowly scoped cleanup is explicitly authorized.

Hosted follow-up `86b8c53` passed browser/backend/frontend/secret gates, but the
new strict image gate correctly failed: backend Debian 12.15 had 55 OS rows and
six Python/tooling rows; updated frontend Alpine still had three fixable OS rows.
The Python inventory findings included pip-vendored packages and the old global
uv executable; the application lock already contains urllib3 2.8.0 and no msgpack
or setuptools package. A selective lock refresh confirmed no changes were needed.

Further remediation upgrades the Python 3.13 base from Debian Bookworm to stable
Trixie with available OS security updates, upgrades uv CLI to 0.13.6 (including
its compromised-root-store fix), and removes pip/uv and build input manifests
from the runtime image after installation. The evaluation target retains uv for
its explicit tooling use. Alpine receives available package security updates.
No advisory suppression or ignore-unfixed switch was introduced.

The owner approved removal only of audit-created images/cache. The Docker daemon
stalled on the exact image-removal request; its client was terminated rather than
leaving an unattended operation pending. No successful cleanup is claimed and no
volume/development-image/cache pruning was attempted. Docker recovery/free disk
space remains manual. GitHub-hosted validation is authoritative for this follow-up.

## Final retained findings and evidence

For runtime remediation commit `558ddfb`, hosted browser run `41314181754`
passed. CI `41314181794` passed backend/migrations/evaluation, frontend and secret
checks and built both images; the strict image scan failed as intended on
**46 HIGH Debian package/advisory rows across 10 CVEs**. There are **0 CRITICAL
and 0 Python-package findings** in the updated backend, and **0 HIGH/CRITICAL**
findings in the patched frontend. See SECURITY.md for IDs and independently
checked Debian tracker references. This is not a claim that each OS advisory is
reachable through an application endpoint. No stable fixed version was reported
for these remaining installed packages after available OS updates.

Final documentation/branding work also enforces the full npm audit in CI and
builds the isolated evaluation target. Local lint/7 Vitest tests/build and SVG/
workflow syntax checks passed; final exact-SHA Actions results are reported to the
owner after push. No public-release clearance is granted. The audit is complete
as a review with documented findings; remediation is incomplete while the strict
OS gate remains red. The repository remains private, with Phases 17–19 open.

To revalidate after upstream security packages land, rebuild runtime images with
`--pull --no-cache` and rerun the immutable Trivy command from CI. Do not reuse a
cached apt/apk security-update layer as evidence of receiving new patches. A
reviewed runtime reduction is an alternative engineering task requiring full
regression and browser acceptance; this audit does not authorize changing the
frozen application technologies or suppressing advisories.
