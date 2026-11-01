# Security policy

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, tokens,
customer information, or identity-provider data. Report suspected security
issues privately to the repository owner through GitHub's private vulnerability
reporting feature when enabled.

## Supported surface

The production surface is the FastAPI `runtime` image and the compiled React
frontend. Provider credentials and local secret files are never part of either
image. The RAGAS toolchain is an optional, isolated evaluation environment and
must not serve production traffic.

## Optional evaluation advisories

The frozen RAGAS 0.3.9 evaluation dependency currently carries
`GHSA-95ww-475f-pr4f` (`PYSEC-2026-3046`); its transitive diskcache 5.6.3
dependency carries `GHSA-w8v5-vhqr-4h9v` (`PYSEC-2026-2447`). No compatible
upstream fixed releases are currently available. These packages are excluded
from the production API image and production dependency audit, while their
advisories remain explicitly tracked.

## Publication and retained evidence

See [the public-release audit](docs/public-release-audit.md) and
[publication checklist](docs/publication-checklist.md) before changing visibility.
The strict full-history scan uses no global fixture allowlist. CI avoids persisting
checkout credentials and automatically uploading Docker build records or
Playwright traces, which can contain authenticated requests. Retained historical
artifacts and personal commit email metadata belong to the private development
repository, not this independent snapshot. Its earlier full-release audit is
historical evidence; the source-review route below governs this portfolio.
Development integration/browser tests must use only isolated `telecom_test_db`;
`compose.acceptance.yaml` supplies the browser-specific database override.

## Runtime OS release blocker — 1 November 2026

The fully updated Python 3.13 Debian Trixie runtime still reports 46 HIGH package/
advisory rows covering ten CVEs in Trivy 0.76.1, with no CRITICAL or Python-package
findings. These are scanner results, not a claim that all are reachable through
the API. The strict CI gate intentionally fails; no allowlist or ignore-unfixed
exception has been added. Frontend Nginx 1.30.6 plus Alpine security updates reports
zero HIGH/CRITICAL findings.

Outstanding IDs: CVE-2025-69720, CVE-2026-119373, CVE-2026-119586,
CVE-2026-16742, CVE-2026-54369, CVE-2026-76642, CVE-2026-78408,
CVE-2026-78409, CVE-2026-78410, CVE-2026-9538. They involve util-linux,
acl, ncurses, SQLite, systemd and Perl source packages. Stable Debian fixes are
not available in the scanned image after `apt-get upgrade`.

Examples independently checked against Debian's tracker:
[util-linux](https://security-tracker.debian.org/tracker/CVE-2026-76642),
[ncurses](https://security-tracker.debian.org/tracker/CVE-2025-69720), and
[SQLite](https://security-tracker.debian.org/tracker/CVE-2026-119373).
Do not deploy, release production containers or claim a clean container audit
until the remaining gate passes. A reviewed source-only portfolio may be made
public only after explicit owner approval under the
[publication plan](docs/portfolio-publication-plan.md). This exception permits
source inspection, not production clearance; all vulnerability gates stay strict.
Rebuild without cached OS-update layers after patched
packages become available, or implement and fully validate a reviewed compatible
runtime reduction. Do not hide package metadata or suppress findings to pass CI.
