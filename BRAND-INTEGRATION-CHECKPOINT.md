# Brand kit v1.0 integration: durable checkpoint

Branch `brand/integrate-final-brand-2026-11-02`, cut from `main` @ `f265c25` (2026-11-02). Resume from here; do not redo verified steps.

## State by phase

| Phase | State | Evidence |
|---|---|---|
| 0 Recover | DONE | CEO originals SOS-007..011 SHA-256 OK (project shared folder). Design Project "SaveOnSub Design System V2 DRAFT" opened in the CEO's Chrome; kit downloaded (zip sha256 `b0bd2faa…`), 132/132 kit checksums OK. PR #74 and #92 read. |
| 1 Browser | PASS_VERIFIED | Claude in Chrome: Design Project, Cloudflare Pages dashboard (read-only). |
| 2 Brand repo | PARTIAL | Built and committed locally at `C:\Users\emonh\SYSmoAI-Stack\apps\saveonsub-brand-system` (`87e6806`, verify PASS, deterministic zip sha256 `a1e4a6e0…`). GitHub creation/push BLOCKED by the session's permission guard; CEO runs the command in the final report. |
| 3 Website brand | DONE (this branch) | See "Changes". |
| 4 Audit | PARTIAL | Policy items prepared in `POLICY-PROPOSALS-2026-11-02.md`, not applied. /all counts verified 62+10=72. |
| 5 Topology | DONE (documented) | See below. No preview deployment made: local preview only. |
| 7 Tests | see PR body | Quality-gates steps run locally, brand tests, browser QA (7 widths, 13 pages), axe-core 4.10.2. |

## Authority decision

Brand kit v1.0 (Design Project decision SOS-CEO-20261102-002) is current. SOS-D001 transparent icon is from SOS-008; SOS-007 (black-corner tile) is legacy. PR #74 and PR #92 are superseded, not merged. Full chain and the open two-S-drawings question: private repo `AUTHORITY.md`.

## Changes

- `assets/brand/`: 20 public-safe kit files + `brand-export.json` (brand 1.0.0, source commit, SHA-256 each). Produced only by `saveonsub-brand-system/scripts/export_web.py`.
- `assets/logo.svg`: embeds kit `wordmark-reverse-600w.png` byte-for-byte (site header/footer are dark). Brand-lock marker kept for existing guards.
- `assets/favicon.svg`: embeds kit `favicon-48.png` (M1).
- `stage_deploy.py`: icons/OG/favicon.ico are copied from `assets/brand/` after hash verification; no resizing or text rendering. Manifest gains maskable icons; colours N1 `#082034`. theme-color `#102634` → `#082034` at staging.
- `cache_safe_brand.py`: keeps real alpha (reverse wordmark has white letters); favicon-32 is the pinned M1 file.
- `assets/style.css`: `--sos-*` tokens; accent `--green` → teal-on-dark `#34c3b2` (kit-sourced) instead of unsourced `#14d4b8`.
- `checkout.html`: inline WhatsApp link underlined (axe `link-in-text-block`, WCAG 1.4.1).
- `tests/test_brand_kit_integration.py`, `tests/browser_qa.py`.

## Deployment topology (2026-11-02)

- GitHub `main` push → `.github/workflows/canonical-deploy-manual.yml` → wrangler → Cloudflare Pages `saveonsub`. Last 5 runs all `failure` (credential preflight), so today nothing auto-publishes from GitHub.
- Cloudflare Pages `saveonsub`: production 77c20d55 (main, live). Domains saveonsub.com, www, saveonsub.pages.dev. Deployments are uploads; never roll back to f7f1e404 or 1c6b91b9 (leak).
- Vercel builds `main` as a mirror (not on saveonsub.com).
- Cloudflare also lists a Worker named `saveonsub-store` (not inspected; possible separate publisher, verify before any release).
- Caching: `_headers` caches `/assets/*.png` for 7 days and `sw.js` is stale-while-revalidate, so returning visitors may see old fixed-name icons for up to 7 days. The header logo uses a content-hashed filename and updates at once.

## Next steps

1. CEO: create/push the private brand repo (command in report), then upload the release zip.
2. CEO: review this draft PR; decide P-01..P-04.
3. Optional non-production preview: Cloudflare Pages "Create deployment" with branch `brand-preview` (preview URLs are non-production). Needs the CEO's click.
4. Release only with a separate CEO decision naming the exact SHA.
