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

## Cycle 8 (2026-11-10, design/conversion-seo-upgrade-2026-11-10)
- New build step `conversion_upgrade.py` (after prices_page, before price/claims guards; `--check` in quality-gates):
  134 priced product pages get a monogram tile, Key facts box, Compare plans table, How-ordering steps,
  related-product cards (no amounts: a product page may only show its own prices) and a mobile sticky
  buy bar reusing the page's WhatsApp prefill. Home (/ and /bn): shopper headline, trust bar now lists
  Shared, monogram cards, Why SaveOnSub, payment row, 5-question FAQ + matching FAQPage JSON-LD.
- Fixed: 80px global `section` padding left ~160px blank gaps on product pages; chatgpt-plus/claude-pro
  pages said "not a credential-sharing offer" directly under disclosed shared plans; "CEO-approved
  pricebook" internal wording shown to customers.
- CI: `! grep` lines never failed under `set -e` (bash exempts `!`); now `|| exit 1`. Stale
  "chatgpt-plus must not show ৳3,390" assertions flipped after CEO APPROVE PRICE 3390 (PR #117).
- Blog repair (same PR): hold_content_price_guard turned every legacy blog price into the phrase "current price on the product page" (up to 11x a page, titles like "Google AI Pro at current price on the product page — how is it possible?"). Source sentences rewritten without prices; table cells -> "See product page"; new step `blog_copy_polish.py` (after the guard, `--check`-able) collapses leftovers; Google AI Pro guide lost unverifiable claims (#1 seller, 211+ orders, "lowest-risk", "legitimate regional channels", 30-day guarantee). Bangla guide titles drop the brand suffix when over 60 chars. BN product-page template strings are now Bangla.
- Still open (CEO/facts): netflix-spotify-youtube-premium-price-bd and shared-vs-personal guides still carry 2026-09 era facts (Spotify/YouTube official prices, "Netflix has no official taka price", warranty wording) that need a fresh source check before they are rewritten.

## Cycle 9 (2026-11-10, seo/clean-links-release-audit-2026-11-10, PR #120)
- `link_hygiene.py` (after site_seo_hygiene): internal `*.html` links -> clean URLs; EN/BN hreflang pairs fixed.
- `release_truth_audit.py`: fail-closed pre-release audit (private files, WhatsApp number, dead links,
  sitemap/canonical/hreflang, JSON-LD offers visible, no ratings, AIPS price-free); `--manifest` writes the
  per-page manifest. AIPS `/modes/*` estimates are WARN only until ISO-001 is decided.
- `a11y_polish.py` (after link_hygiene, `--check`): axe WCAG 2 AA over all pages found two repeatable
  defects; scrollable `.tbl` wrappers become focusable labelled regions; in-text links underlined in
  style.css; `.btn` wraps under 480px (bkash blog overflowed at 375px); cookie-banner link underlined.
- Bangla: checkout, order, quiz, all, warranty notice and /bn/prices labels/categories translated;
  BN pages' quiz links now go to /bn/quiz (they pointed at the EN quiz). Doubled "support terms terms"
  from the warranty swap is collapsed in commercial_truth_v2. Bangla order page lost a "5–15 minutes"
  delivery promise; students.html description lost an unverified "student discount" claim.
- Google AI BD prices re-fetched 2026-11-10: unchanged (600 / 2,500 / 8,100 / 25,000 BDT).
- Motion v1 (CEO: "site looks boring"): `motion_polish.py` (after a11y_polish, `--check`) adds hero aurora,
  h1 highlight, a product-name rail (no prices) and a facts band counted from the catalog to EN/BN home,
  and versions `sw.js` CACHE from style/app/catalog content. CSS block "motion v1" + app.js reveal/count-up/
  ticker/scroll-progress; all off under prefers-reduced-motion. Mobile: logo/Track collision fixed, hero
  cards swipe, listing grids 2-up. `category_copy_polish.py` replaces 26 category intros that carried
  unverified numbers/stale "from ৳" prices and the unused official/shared·covered legend; BN cards read
  "৳X থেকে". BN home copy and ticker fully Bangla.

## Cycle 10 (2026-11-10) — buyer-phrase SEO
- Titles: "<X> Subscription Price in BD — from ৳N | SAVEONSUB" when it fits 60 chars (BD "subscription bd" phrasing out-searches "price in bd"); H1 unchanged.
- buyer_intent_polish.py: 3 answers per EN/BN product page from catalog only + FAQPage JSON-LD; `--check` in CI.
- Off-site gaps (owner actions): GSC request indexing for top product URLs, Google Business Profile, real customer reviews, BD backlinks/mentions.
