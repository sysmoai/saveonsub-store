# AGENTS.md — SAVEONSUB (saveonsub.com)

## Measured project truth
- Repo: `sysmoai/saveonsub-store`
- Architecture: Python-generated, committed static HTML/assets
- Public staging: `python stage_deploy.py` -> `_site`
- Active deploy target in workflow: Cloudflare Pages project `saveonsub`
- Never deploy the repository root
- Legacy GitHub Pages is configuration drift, not the canonical deployment path

## Authority / release controls
- Current provisional control state: `L0_BOOTSTRAP_PRIVATE`
- Bootstrap work does not imply public launch or commerce authority
- Production commerce/public prices/indexing remain fail-closed until current scoped authority is recorded
- Use feature/fix/seo branches for material work; do not make major changes directly on `main`
- Pull requests must not deploy to the production-equivalent Cloudflare branch

## Required release checks
- `python validate_release.py`
- `python check_prices.py`
- `python stage_deploy.py`

See `SOS_ARCHITECTURE_TRUTH.md` and `docs/audit/SAVEONSUB_MASTER_GAP_REGISTER.md` for current evidence and gaps.
