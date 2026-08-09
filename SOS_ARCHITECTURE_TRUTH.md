# SAVEONSUB Architecture Truth

**Measured:** 2026-08-10 (Asia/Dhaka)  
**Repository:** `sysmoai/saveonsub-store`  
**Baseline main SHA:** `9218ddfc4f6fd0fb607bac6c4a672958540a76fa`

## Canonical implementation observed

1. `catalog.json` and Python generator scripts are source inputs.
2. Python scripts generate committed static HTML and browser assets.
3. CI does not regenerate the full site; it validates reviewed committed output.
4. `stage_deploy.py` creates an explicit public `_site` tree.
5. The current GitHub Actions workflow targets Cloudflare Pages project `saveonsub`.
6. The repository root must never be deployed.

## Measured site census

The 2026-08-10 baseline contains:

- **234 HTML files** in the repository;
- **200 sitemap URLs**;
- **72 catalog products**;
- **13 categories**;
- **72 English + 72 Bangla product pages**;
- **13 English + 13 Bangla category pages**;
- **13 blog pages** (12 articles + index);
- **10 mode-detail pages**;
- **23 root HTML pages** and **18 Bangla general pages**.

Full route/product breakdown: `docs/architecture/SAVEONSUB_FULL_ARCHITECTURE_2026-08-10.md`.
Deterministic future census/parity check: `inventory_site.py`.
Development sequence: `docs/roadmap/SAVEONSUB_BD_LEADERSHIP_ROADMAP.md`.

## Hosting / deployment truth

- Current workflow: `main push -> release integrity checks -> price checks -> stage_deploy.py -> _site -> Cloudflare Pages` on the working safety branch.
- Pull requests must not deploy to the production-equivalent Cloudflare branch.
- Latest observed Cloudflare workflow for baseline main SHA failed; a successful Cloudflare production deployment for that SHA has not been verified.
- GitHub Pages remains enabled as a legacy public host sourced from `gh-pages`.
- The observed `gh-pages` branch contains only `.nojekyll`, so it is not currently a storefront copy, but the duplicate public serving path remains configuration drift.
- Custom-domain DNS and current production HTTP behavior were not independently verified from the execution environment and remain `UNKNOWN` until measured through authoritative DNS/Cloudflare evidence.

## Known obsolete / drifting controls

- Baseline `AGENTS.md` described GitHub Pages as the deployment target and said Cloudflare was not required; the working branch corrects this.
- `.next/`, `.astro/`, `.replit`, and `vercel.json` are present despite the measured static/Python architecture.
- These artifacts are not to be deleted until their remaining operational use is proven absent.

## Source -> generated parity

Generated HTML is committed. Therefore every release needs deterministic evidence that reviewed generated output corresponds to approved source inputs. Existing CI does not yet provide a complete source hash / generated manifest / authority-version parity proof. This remains an open P1 gap.

`inventory_site.py` is the first parity layer: it compares catalog product IDs with EN product routes, BN product routes and per-product social PNGs, and reports route/sitemap/category counts without network access.

## Public data boundary

- Markdown, Python, shell, repository/config files and JSON are internal by default.
- Runtime JSON is fail-closed and requires explicit `PUBLIC_JSON_ALLOWLIST` approval in `stage_deploy.py`.
- `catalog.json`, `aips-live.json`, pricing provenance, control records and customer/order data must not enter `_site`.

## Rollback

A previous-good production SHA and Cloudflare deployment ID have not yet been independently verified. Do not claim a rollback point until both are recorded.
