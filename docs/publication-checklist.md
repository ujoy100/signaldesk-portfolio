# Publication security checklist

This is the **full application/private development repository release checklist**.
Its historical-email, retained-artifact and branch-plan items refer to that
repository. The independent portfolio contains neither its history nor its Actions
artifacts. This checklist does not authorize publication or settings changes.

## Public portfolio validation — 3 November 2026

The following checks apply only to the independent public
`ujoy100/signaldesk-portfolio` repository.

- [x] Public PR #11 merged into `main` as
  `f952f55caf4a1f4090134c0fd016ce5d4e978110`.
- [x] Backend migrated from Debian Trixie to Python 3.13 Alpine.
- [x] Frontend Alpine runtime updated to require patched `libexpat`.
- [x] Strict Trivy HIGH/CRITICAL gate passed for the validated public
  backend and frontend images without vulnerability suppressions.
- [x] Post-merge GitHub Actions CI passed.
- [x] Post-merge Playwright browser acceptance passed.
- [ ] Confirm the final recruiter-readiness documentation commit passes
  its own required GitHub checks.
- [ ] Complete final documentation consistency, provenance and
  public secret-scan review.

Evidence:

- [Post-merge CI](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839313)
- [Post-merge browser acceptance](https://github.com/ujoy100/signaldesk-portfolio/actions/runs/41622839342)

These results do not establish cloud deployment or formal production
security approval. The original private repository's full-release
requirements below remain separate and unchanged.

**Phase 17 IN PROGRESS; Phases 18–19 PENDING.**
**Production deployment NOT APPROVED.**

---

## Independent source-review portfolio

- [x] Owner confirms personal learning/portfolio ownership and Codex assistance;
  no employer or client project materials are claimed.
- [x] Scope separates public source inspection from blocked production release.
- [x] Retain third-party notices without adding an open-source license.
- [x] Run fresh Gitleaks; 11 manifest-checksum false positives remain unsuppressed.
- [ ] Resolve the strict secret gate’s checksum false positives through a
  separately approved approach; see [preflight](publication-preflight.md).
- [ ] Obtain owner approval of the final commit before remote creation/publication.

The [publication plan](portfolio-publication-plan.md) governs this narrower route.
The full-release requirements below remain open; production gates are unchanged.

## Owner decisions and manual steps

- [x] Verify historical hero provenance: byte-identical official Vite starter;
  retain its upstream notice in THIRD_PARTY_NOTICES.md. No history rewrite is
  recommended for this asset on current evidence.
- [ ] Decide whether the personal author/committer email already in Git history
  may be public. For future commits, configure the verified GitHub noreply address
  locally. Historical removal requires separately approved rewriting.
- [ ] Review retained Actions build records, nested archives, old logs, forks and
  caches for artwork/private data. Approve any deletion individually; none is
  automatically removed by this checklist.
- [ ] Confirm private secret reports locally. If an actual exposed credential is
  found, approve rotation and incident cleanup; do not paste values into GitHub.
- [ ] Obtain a plan supporting private-repository branch protection, or separately
  decide on visibility later. Configure protected main and required successful
  backend, frontend, secret/dependency, image and browser checks; require reviewed
  pull requests. Settings changes require explicit approval.
- [ ] Verify the exact final commit's CI and browser runs and review annotations.
  A green earlier commit is not evidence for a later commit.
- [ ] Complete real interactive Microsoft Entra sign-in, account switching,
  logout/revocation and role-denial acceptance with sanitized evidence.
- [ ] Visually approve screenshots; confirm they contain only fictional data.
- [ ] Review optional RAGAS/diskcache advisories and document the retained risk.
  Keep the evaluation image isolated and never expose it as the API service.
- [ ] Review rights statement and original/third-party provenance. No MIT/Apache
  or other broad reuse license is intended.
- [ ] Complete Phase 19's own docs, diagrams, release notes, demonstration and
  end-to-end acceptance. Keep Phases 18/19 PENDING until their own gates pass.
- [ ] Explicitly authorize publication only after blockers are resolved. Cloud
  deployment, production secret provisioning and security settings are separate
  approvals; no deployment is performed by CI today.

## Repeatable technical checks

- [ ] Full-history and current-tree Gitleaks with no broad marker allowlist;
  staged diff and ignored file review; dependency audits for runtime and evaluation.
- [ ] Isolated PostgreSQL backend suite, Alembic current/head/check, lock check,
  deterministic metrics, frontend lint/tests/build and real Compose Playwright.
- [ ] Resolve 46 HIGH backend OS package/advisory rows (10 CVEs) and verify
  hosted Trivy gates. Frontend currently reports zero HIGH/CRITICAL findings.
  Local Docker recovery requires free disk space; do not prune volumes.
- [ ] Runtime/evaluation/frontend Docker builds; inspect runtime package boundary
  and build contexts. Preserve development databases and all existing volumes.
- [ ] Review all reachable Git refs plus GitHub pull-request refs and retained
  Actions logs/artifacts. Note inaccessible/expired evidence explicitly.

See [public-release-audit.md](public-release-audit.md) for actual evidence and
remaining coverage limits. Secret scanners cannot prove absence of all secrets.
