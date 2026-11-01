# GitHub Actions dependency review

Reviewed 1 November 2026 against official repository release notes, tag objects,
and action.yml manifests. Every JavaScript action uses Node 24; no runtime
override hides deprecated runtimes. Hosted Ubuntu 24.04 runners satisfy the
Node 24 runner requirement. Checkout credentials are not persisted. Docker build
records are no longer automatically uploaded; existing artifacts are retained
pending owner review. Workflow permissions remain contents: read.

| Action | Release | Immutable commit |
|---|---|---|
| [actions/checkout](https://github.com/actions/checkout/releases/tag/v7.0.1) | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| [actions/setup-node](https://github.com/actions/setup-node/releases/tag/v7.1.0) | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| [actions/upload-artifact](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| [actions/dependency-review-action](https://github.com/actions/dependency-review-action/releases/tag/v5.0.0) | v5.0.0 | `a1d282b36b6f3519aa1f3fc636f609c47dddb294` |
| [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv/releases/tag/v10.3.3) | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` |
| [docker/setup-buildx-action](https://github.com/docker/setup-buildx-action/releases/tag/v4.4.1) | v4.4.1 | `f87e5991a6d7451dcb8d9637bfbc97413f497069` |
| [docker/build-push-action](https://github.com/docker/build-push-action/releases/tag/v7.4.0) | v7.4.0 | `c3c9e263c25d99ce0380d002d59b67737d91b0dc` |

Review scope: official release provenance, runtime, inputs used by this project,
credential persistence, and release security changes; this is not a line-by-line
audit of bundled third-party JavaScript. setup-node retains Node 22 for the
application toolchain. setup-uv uses explicitly pinned uv CLI 0.13.6 after the container audit found
the old CLI compromised-root-store advisory.
Dependabot proposes updates; review release notes and immutable SHAs before merging.

Gitleaks v8.24.3 is pinned to the inspected registry manifest digest
`sha256:e1b35e12a8c6fa8901f060459cfb6b2fc4c484d3afbe3b029733a3bbfab07055`.
The former global marker allowlist was removed entirely; full history passes
without exceptions. Playwright traces and failure screenshots are no longer
uploaded automatically because traces can carry bearer credentials and responses.
Local failure diagnostics remain available for private investigation. The
upload-artifact release above was reviewed but is no longer used.

Runtime image builds now load local runner tags and run immutable Trivy 0.76.1
(`sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c`)
against both OS and application packages. HIGH/CRITICAL findings fail the job;
unfixed findings are not ignored. No provider secrets are available to this job.
