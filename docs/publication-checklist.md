# Publication security checklist

Public release is **blocked** until the owner resolves the items below. This
checklist does not authorize making the repository public or changing settings.

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
