# Checkpoint — cycle 4 (2026-11-03)

- main f265c25; live 77c20d55. PR #91 (CEO "APPROVED ALL" pricebook) open, CI green, unmerged.
- This branch is stacked on #91: adds `catalog_reconcile.py` (last build step) and fixes
  period labels so yearly / 6-month prices no longer render as "/ month".
- Reconcile result: 77 entries, 67 priced products, 133 plans, 10 inquiry, 0 mismatches.
  Five pricebook IDs have no catalog page and stay inquiry-only (see CAT-003).
- Generated ledger `ops/seo/control/product-coverage.json` is gitignored (contains
  provider-rights statuses); a private copy lives outside the repo on the CEO machine.
- Next: SEO-002 (Product/Offer schema) after CEO decision; SEO-003 keyword map.

## Cycle 2
- GSC (live Chrome): data only from 2026-10-31, 0 clicks / 0 impressions; indexing still processing. No baseline yet.
- kling-ai / pika-labs / gamma-pro are aliases of kling / pika / gamma; only replit and mistral remain held.
- Priced product pages now carry lastmod 2026-11-02 in sitemap; BN bundle-video title de-duplicated.
- Open: SEO-006 (20 indexable pages not in sitemap), ISO-001 (AIPS /modes pages, CEO).

## Cycle 3 (V13.0)
- `universe_registry.py --aips <checkout> --private-out <file>` classifies other units' catalogs; it never reads
  prices or sales copy. Its outputs stay private (gitignored), on the CEO machine under 00_CONTROL/saveonsub/.
- `tools_explorer.py` stages `/tools` (AI Tools Explorer) only when that private family file is present;
  publishing it needs a CEO decision (PUB-001).
- All five pricebook-only IDs resolved as aliases.

## Cycle 4
- `universe_registry.py --atlas <psv>` ingests the Notion ATLAS export (name, category, status/access, site host;
  no prices). Family flags are intersections, so one enterprise-only row does not hide a consumer family.
- Explorer skips families that are only other-unit packages, services or not-sellable per source.
