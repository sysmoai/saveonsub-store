# Checkpoint — cycle 5 (2026-11-03)

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

## Cycle 5 (V14.0)
- `--seeds` ingests the workbook's research-seed list (category letter legend in the file header; tl;dv rejoined).
- Family status now follows SaveOnSub's own pricebook first: a family with an approved SaveOnSub plan is
  APPROVED_SELLABLE even when the research row carries no access type.
- Seed-only families have no official URL yet, so they stay NEEDS_FACT_VERIFICATION and off the explorer.
- Next: fuzzy-duplicate review of seed families (e.g. google gemini/google, kimi/moonshot, llama/meta).

## Cycle 6 (2026-11-06)
- New build step `product_rich_results.py` (after product_seo_enrich): price in title, price/payment meta,
  visible "Quick answer" + price & ordering FAQ, Product/Offer + FAQPage JSON-LD on 134 priced EN/BN pages.
  `--check` gate in quality-gates; 8 tests. AIPS + inquiry pages untouched.
- Keyword seed map: ops/seo/KEYWORD-MAP-2026-11-06.json (tiers A 18 / B 31 / C 18).
- /prices page dropped: hold_content_price_guard masks prices off product pages (SEO-007, CEO).
- /prices + /bn/prices staged by prices_page.py as pcard listing cards (guard card rule keeps only approved prices); links from every quick answer; sitemap +2.

## Cycle 7 (2026-11-06, after 542d854d live)
- Category pages now show approved 'From ৳X' card prices (guard CARD_LINK) with honest access labels
  (shared/mixed no longer 'Customer-specific'); site_seo_hygiene.py: category titles/meta/ItemList,
  og:image+twitter tags everywhere, 5 BN pages into sitemap. IndexNow key file + indexnow_submit.py
  (run only after a CEO-approved deploy).
