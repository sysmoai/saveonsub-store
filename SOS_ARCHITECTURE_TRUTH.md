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

## Hosting / deployment truth

- Current workflow: `main push -> release integrity checks -> price checks -> stage_deploy.py -> _site -> Cloudflare Pages`.
- Pull requests must not deploy to the production-equivalent Cloudflare branch.
- Latest observed Cloudflare workflow for baseline main SHA failed; a successful Cloudflare production deployment for that SHA has not been verified.
- GitHub Pages remains enabled as a legacy public host sourced from `gh-pages`.
- The observed `gh-pages` branch contains only `.nojekyll`, so it is not currently a storefront copy, but the duplicate public serving path remains configuration drift.
- Custom-domain DNS and current production HTTP behavior were not independently verified from the execution environment and remain `UNKNOWN` until measured through authoritative DNS/Cloudflare evidence.

## Known obsolete / drifting controls

- `AGENTS.md` still describes GitHub Pages as the deployment target and says Cloudflare is not required.
- `.next/`, `.astro/`, `.replit`, and `vercel.json` are present despite the measured static/Python architecture.
- These artifacts are not to be deleted until their remaining operational use is proven absent.

## Source -> generated parity

Generated HTML is committed. Therefore every release needs deterministic evidence that reviewed generated output corresponds to approved source inputs. Existing CI does not yet provide a complete source hash / generated manifest / authority-version parity proof. This remains an open P1 gap.

## Public data boundary

- Markdown, Python, shell, repository/config files and JSON are internal by default.
- Runtime JSON is fail-closed and requires explicit `PUBLIC_JSON_ALLOWLIST` approval in `stage_deploy.py`.
- `catalog.json`, `aips-live.json`, pricing provenance, control records and customer/order data must not enter `_site`.

## Rollback

A previous-good production SHA and Cloudflare deployment ID have not yet been independently verified. Do not claim a rollback point until both are recorded.
