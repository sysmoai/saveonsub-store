# AGENTS.md — SAVEONSUB (saveonsub.com)

## Measured project truth
- Repo: `sysmoai/saveonsub-store`
- Architecture: Python-generated, committed static HTML/assets + browser JS/localStorage + PWA service worker
- Measured baseline (2026-08-10): **234 HTML files, 200 sitemap URLs, 72 products, 13 categories**
- Public staging: `python stage_deploy.py` -> `_site`
- Active deploy target in workflow: Cloudflare Pages project `saveonsub`
- Never deploy the repository root
- Legacy GitHub Pages is configuration drift, not the canonical deployment path

## Canonical architecture references
- `SOS_ARCHITECTURE_TRUTH.md`
- `docs/architecture/SAVEONSUB_FULL_ARCHITECTURE_2026-08-10.md`
- `docs/audit/SAVEONSUB_MASTER_GAP_REGISTER.md`
- `docs/roadmap/SAVEONSUB_BD_LEADERSHIP_ROADMAP.md`

## Authority / release controls
- Current provisional control state: `L0_BOOTSTRAP_PRIVATE`
- Bootstrap work does not imply public launch or commerce authority
- Production commerce/public prices/indexing remain fail-closed until current scoped authority is recorded
- Use feature/fix/seo branches for material work; do not make major changes directly on `main`
- Pull requests must not deploy to the production-equivalent Cloudflare branch

## Safe development workflow
1. Measure the current main SHA and site inventory.
2. Work on a dedicated branch.
3. Change source/generators before generated pages; do not hand-fix generated output as the primary solution.
4. Regenerate deterministically.
5. Verify catalog, EN/BN product pages, category routes, sitemap and product social assets remain in parity.
6. Review customer journeys and the staged `_site` tree.
7. Never change protected prices, payment destinations, contact numbers, legal identity, provider eligibility, DNS or production without reconciled authority.
8. Merge/deploy only when release gates match the approved launch state.
9. Verify the canonical live domain after deployment and record deployment SHA/ID + rollback point.

## Required checks
- `python inventory_site.py`
- `python validate_release.py`
- `python check_prices.py`
- `python audit_all.py`
- `python deploy_preflight.py`
- `python stage_deploy.py`

## Growth direction
Improve **SAVEONSUB only**. Prioritize provider-safe fulfillment, accurate product facts, Bangla/English discovery, fast mobile UX, measurable conversion, durable order/lead records when approved, and evidence-backed trust claims.
