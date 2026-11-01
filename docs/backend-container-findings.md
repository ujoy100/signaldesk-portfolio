# Backend container gate review — 1 November 2026

Baseline: `757f24a46f4dfd5cf1e4cb4adac5e1cc6ffc3538`.
[Hosted CI scan](https://github.com/ujoy100/telecom-agentic-ai-support/actions/runs/41314546443)
reports **46 HIGH package/advisory rows, 10 distinct CVEs, 0 CRITICAL and
0 Python-package findings** in the production Debian 13.7 runtime. Frontend
HIGH/CRITICAL count is zero. The strict gate remains red.

## Exact installed-package matrix

Each package in a grouped cell was reported at the corresponding version.
`U1`–`U4` below refer to the four util-linux CVEs in the next table.

| Installed package(s) | Installed version | CVEs | Rows |
|---|---|---|---:|
| bsdutils | 1:2.41.5-0+deb13u1 | U1–U4 | 4 |
| libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, mount, util-linux | 2.41.5-0+deb13u1 | U1–U4 each | 28 |
| login | 1:4.16.0-2+really2.41.5-0+deb13u1 | U1–U4 | 4 |
| libacl1 | 2.3.2-2+b1 | CVE-2026-54369 | 1 |
| libncursesw6, libtinfo6, ncurses-base, ncurses-bin | 6.5+20250216-2 | CVE-2025-69720 each | 4 |
| libsqlite3-0 | 3.46.1-7+deb13u2 | CVE-2026-119373, CVE-2026-119586 | 2 |
| libsystemd0, libudev1 | 257.13-1~deb13u1 | CVE-2026-16742 each | 2 |
| perl-base | 5.40.1-6+deb13u1 | CVE-2026-9538 | 1 |
| **Total** | | **10 distinct CVEs** | **46** |

## Available fixes and stable-release boundary

Checked against Debian's primary security tracker on 1 November 2026. The
hosted scan's Fixed Version column is empty for every row. No fixed Trixie
package is listed for these CVEs. Versions from unstable/testing below are
**not** proposed for mixing into a stable production runtime.

| Label / CVE | Source package | Fixed version evidence | Trixie status |
|---|---|---|---|
| U1: [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642) | util-linux | Debian unstable 2.42.3-1; current fixed unstable/testing 2.42.4-1 | Vulnerable; no DSA |
| U2: [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408) | util-linux | Debian unstable 2.42.4-1; upstream 2.42.4 | Vulnerable; no DSA |
| U3: [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409) | util-linux | Debian unstable 2.42.3-1 | Vulnerable; no DSA |
| U4: [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410) | util-linux | Debian unstable 2.42.3-1 | Vulnerable; no DSA |
| [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369) | acl | Upstream 2.4.0; Debian unstable 2.4.0-1 | Vulnerable; point-release update planned |
| [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720) | ncurses | Upstream 6.5-20251213; Debian unstable 6.6+20251231-1 | Vulnerable; no DSA |
| [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373) | sqlite3 | Upstream fix attributed to 3.54.0; Debian has no fixed package listed | Vulnerable |
| [CVE-2026-119586](https://security-tracker.debian.org/tracker/CVE-2026-119586) | sqlite3 | No fixed Debian package listed; shell through 3.54.1 affected | Vulnerable |
| [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742) | systemd | Upstream 258.10 / 261.2; Debian unstable 261.2-1 | Vulnerable; no DSA |
| [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538) | perl | Archive::Tar 3.10; Debian unstable perl 5.42.3-1 | Vulnerable; postponed |

## Production, tooling and optional evaluation

These 46 findings are installed OS packages in the **production runtime**, not
build-stage-only or optional RAGAS dependencies. Earlier pip/uv inventory findings
were removed in the baseline; the final production image contains no pip/uv,
RAGAS or diskcache. The evaluation target retains its isolated Debian/Git/uv
and frozen optional dependencies; the two documented RAGAS/diskcache advisories
are separate from this 46-row runtime gate.

A source-package association is not proof of application exploitability. The
reported issues involve mount/nsenter operations, pathname ACL processing,
infocmp, SQLite FTS5 / shell recovery, systemd-homed and Perl Archive::Tar.
SignalDesk application code does not directly invoke those utilities; it uses
PostgreSQL for business state and Qdrant for retrieval. Shared libraries can
still be installed/imported transitively. Binary presence, exact code-path
reachability and exploit prerequisites have not been comprehensively proven.
No finding is suppressed or declared harmless on that basis.

## Reviewed remediation boundary

The baseline already runs stable Trixie security updates. Repeating its cached
build is not evidence of a new fix. A supported official Python 3.13 Alpine 3.24
runtime was reviewed as a single bounded alternative. The lock has musl wheels
for native runtime dependencies (and a universal protobuf wheel), but the
[official Alpine 3.24 package index](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/APKINDEX.tar.gz)
currently provides sqlite-libs **3.53.4-r0**, below the 3.54.0 fix boundary above.
It therefore does not establish a clean replacement. No speculative image switch
was applied and no large local Docker build was run.

Not attempted: unstable package mixing, ad hoc upstream library compilation,
removal of package inventory, severity changes, VEX/ignore entries, or removal of
potentially required libraries solely to make the scanner pass. Next safe work
requires supported patched packages or a separately evidenced compatible runtime
whose complete dependency and browser validation passes the same strict gate.
If another proposed runtime still scans red, stop and report its exact findings.

## Validation and disposition

Docker-free checks passed: Ruff lint/format (133 files), pytest **128 passed /
1 intentional paid-test skip** against only `telecom_test_db`, Alembic current/
head/check at `2d4f8a71c930`, uv lock (148 packages), and whitespace checks. The
known optional RAGAS community-import deprecation warning remains visible. Existing hosted
baseline application checks and browser acceptance passed; its container gate
failed as above. No code/image/scanner changes, commit or push are warranted
without a demonstrated fix and successful security checks. This review document
is left for owner review rather than committed under a falsely green claim.

**Phase 17: IN PROGRESS. Phases 18–19: PENDING. Container publication clearance:
NOT RESOLVED.** No database reset, Docker volume deletion, history rewrite,
visibility/security-setting change, cloud deployment or local Docker build was
performed for this review.
