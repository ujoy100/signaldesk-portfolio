# Recruiter publication plan — 1 November 2026

## Recommendation and comparison

Recommend **B: a separate clean source-review portfolio**, proposed name
`signaldesk-portfolio`. Approval is still required before creating or publishing
any remote. This is a proposed exception to the existing full-release checklist,
not a declaration that the application release gates passed.

| Route | Public-review prerequisites | Tradeoff |
|---|---|---|
| A: publish existing repository | Owner decision on historical emails; retained Actions logs/artifacts review and any approved cleanup; existing publication checklist and release gates | Preserves development history, but carries inherited privacy exposure and unresolved release criteria |
| B: publish clean source snapshot | Review exact exported files and screenshots; confirm rights, synthetic metadata and privacy; approve remote creation/publication | No inherited commits, refs, logs or artifacts; loses development history and hosted verification continuity |

A recruiter needs inspectable source, architecture, screenshots, tests, reproducible
instructions, evaluation caveats and an honest status. Production hosting and
completion of Phases 18–19 are not prerequisites for this narrower source-review
purpose. The original frozen document is absent locally; repository phase
specifications and tracker remain the available architectural authority.

## Prepared contents and boundary

`portfolio-export/` is an ignored, independent local repository. It contains
all tracked source, migrations, synthetic data, frontend, backend tests, lockfiles,
example configuration, screenshots, phase documentation, rights/notices and
unchanged CI/Docker recipes, plus the existing untracked container findings report
and this plan. Only its README gains a source-review banner. It contains no
original `.git`, Actions downloads, ignored environment/secrets, installed
packages, build output or database files. `EXPORT_MANIFEST.json` inventories
SHA-256 hashes; `SNAPSHOT.md` explains origin and validation scope.

The initial commit uses the deliberately synthetic identity
`SignalDesk Portfolio <portfolio@example.test>`, not a claimed verified GitHub
account. Original authorship/provenance and notices remain in the files. Before
future commits the owner should use their actual verified GitHub noreply identity.
The snapshot has no remote. It retains all strict workflows and will still fail
the backend image gate on the recorded baseline; no passing badge is claimed.
Local Docker recipes are engineering reference/local reproduction material, not
approved deployable artifacts. No container registry release is prepared.

## Security disposition

Retain the dated findings, with production deployment/container release blocked.
The supplied report records 46 HIGH rows / 10 OS CVEs, zero CRITICAL/Python
findings and zero frontend HIGH/CRITICAL findings. These are historical scan
results, not a new scan or current upstream fix verification. No already verified
minimal fix is available in the reviewed evidence. No speculative rebuild,
base switch, suppression or gate reduction is justified. Optional RAGAS/diskcache
advisories remain documented and isolated. Source publication does not fix them.

## Exact owner actions before publication

1. Review the local export diff/manifest, six screenshots and fictional fixtures.
   Prior visual review is recorded in the audit; approve the exact snapshot.
   Phone-like fixtures are fictional but not guaranteed reserved; never contact them.
2. Owner has confirmed this is a personal learning/portfolio project developed
   with OpenAI Codex assistance, not an employer/client project. Retain
   THIRD_PARTY_NOTICES.md. No MIT/Apache license is proposed.
3. Approve the source-review exception explicitly, including public disclosure of
   the unresolved security findings and retention of strict failing image checks.
4. Approve creation/publication of `ujoy100/signaldesk-portfolio`. Use an empty
   GitHub repository without generated README/license, then attach that remote
   and push the reviewed local `main` only. No remote action is performed here.
5. Review exact-SHA hosted workflow results after push. Earlier private runs are
   historical evidence, not proof of the new SHA. Public workflows can create new
   logs/artifacts: inspect them and do not supply production/provider credentials.
6. Configure public branch protection/required checks and reviewed PRs through
   separately approved settings actions; confirm plan support. Never bypass or
   downgrade the image gate to obtain a green status. Keep release blocked.
7. Add the approved repository URL to the CV. Do not link private Actions runs as
   the only evidence; the copied audit records their results and limitations.

No deletion of old artifacts or history rewriting is required for B: leave the
original repository private. For A, separately authorize either acceptance of
historical personal email exposure or a carefully planned history rewrite; review
all retained logs/build records and individually approve any deletions. Configure
verified noreply identity for future commits. Rotation is warranted only if an
actual credential exposure is established and separately authorized; none is
newly established here. Previously scanned binary/expired/external evidence
coverage limits remain in the audit. No scanner proves absence of every secret.

## Blockers by purpose

**Public source portfolio:** fresh exact-snapshot Gitleaks verification and owner
approval of the final contents/source-review release, followed by separately
authorized remote creation/publication. Ownership is confirmed; screenshots were
reviewed in the read-only preflight, with no visible private data.
The clean snapshot does not inherit private commit email metadata or retained
Actions artifacts. It must not be presented as a finished production release.

**Production/full release:** unresolved backend OS findings, optional evaluation
risk review, required checks/branch protection, real interactive Entra acceptance,
Phase 18 infrastructure/secrets/operations and Phase 19 end-to-end release criteria.
Phase 17 remains IN PROGRESS; Phases 18–19 remain PENDING.

## Recruiter URL and CV description

Proposed eventual URL (not created or published by this task):
`https://github.com/ujoy100/signaldesk-portfolio`.

**CV:** Built SignalDesk, a telecom support portfolio application using FastAPI,
React, LangGraph, bounded Deep Agents and an authorized MCP Gateway. Implemented
hybrid RAG with Qdrant, PostgreSQL-backed approvals and durable workflows,
Entra/RBAC controls, observability and reproducible synthetic-data evaluations
with RAGAS. Local implementation; cloud deployment pending.

## Validation scope

This preparation changes documentation and snapshot packaging only. Historical
backend 128 passed/1 intentional skip, frontend 7 passed and Playwright 5 passed
remain attributed to prior evidence, not rerun results. Focused checks cover
whitespace, relative Markdown links, exported file hashes, exclusions, strict
workflow parity and independent Git history/remote status. No database, Docker,
paid-model, cloud or broad security audit is needed for these changes.
