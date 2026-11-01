# Asset and data provenance

Reviewed 1 November 2026. This inventory describes evidence available in the
repository; it does not establish rights to material whose origin is unknown.

| Material | Origin / status | Publication handling |
|---|---|---|
| SignalDesk mark/favicon, login grid and workspace decoration | Original HTML/CSS and code-authored SVG favicon authored for this repository; no external image/font dependency | Current UI replacement |
| `frontend/src/assets/hero.png` (historical) | Present in initial commit `6533a2d`; byte-identical to the official Vite v8.3.0 React starter (SHA-256 verified) | Removed from current tree; still retrievable from Git history. upstream MIT notice retained in THIRD_PARTY_NOTICES.md; no artwork-driven rewrite is recommended on current evidence |
| `docs/screenshots/phase15-*.png` | Playwright captures of this application's fictional local workflows | Inspect visually before publication; no tokens, real identities or private infrastructure should appear |
| `backend/data/knowledge/fictional_telecom.json` | Repository-authored fictional telecom guidance | Demonstration material, not carrier policy or customer advice |
| `backend/app/db/seed.py` | Deterministic fictional customer/plan/subscription/ticket fixtures | No production exports; reserved example identities are intentional |
| `backend/app/evaluation/dataset.py` | Repository-authored fictional questions, expected evidence and safety cases | Small synthetic benchmark; not representative customer evaluation |
| React/Vite starter and installed dependencies | Third-party framework/tooling, identified by manifests and lockfiles | Their licenses and notices remain applicable; no ownership claim over dependencies |
| Frozen documentation | User-provided project authority; referenced in phase notes | Full original document is not stored in this repository; no unsupported rights claim |

Fictional phone-like identifiers and example email addresses are fixtures, not
verified unreachable telephone numbers. Never contact them or replace them with
real subscriber data. Do not infer telecom accuracy from synthetic examples.

No MIT/Apache license has been added. The owner retains rights in original work;
public viewability does not grant broad reuse rights. Third-party rights remain
separate. Removing an asset from the current branch does not remove it from
history, forks, caches or retained build artifacts. No history or artifact cleanup
has been authorized or performed in this work.

## Historical hero verification

Official source and corresponding upstream license were retrieved at immutable
Vite commit `434e8e9495436a60789f2b588a04a6a24a3d1661`. Historical and upstream image bytes match SHA-256
`881ffbcaafc212e49addad08846a5b82761355fa20624253af3477ba33262c5c`. See
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for the required upstream
notice, which applies only to Vite material, not original SignalDesk work.
This resolves the previously unknown source; history rewriting is unnecessary
on the evidence found. Historical snapshots lack this newly supplied notice;
do not distribute isolated old snapshots without their applicable notice.

Unused `react.svg`, `vite.svg` and `public/icons.svg` are retained starter
assets, not original SignalDesk artwork. Their upstream framework/brand rights
remain applicable; no branding ownership claim is made. The rendered favicon
is original signal-bar SVG matching the CSS identity.
