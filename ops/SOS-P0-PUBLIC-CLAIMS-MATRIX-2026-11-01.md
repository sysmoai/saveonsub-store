# P0 live-claim/source matrix — SaveOnSub only

**Evidence date:** 2026-11-01 Asia/Dhaka. **Scope:** review / staged remediation ONLY.
**Commercial authority:** `ops/PRICING-V2-2026-09-17.json` holds every SKU as inquiry-only under EXEC-010 pending an exact CEO-authorized SKU, price, access model and provider rights. The 2026-10-23 founder's intended BDT 499 affordable entry LANE is **not** an approval of a BDT 499 shared credential offer.
**Crawl caveat:** search-indexed material and public page snapshots are observations, not the canonical Cloudflare deployed SHA. The root, /all, /bn and blog were indexed/crawled on 1 Nov; individual product pages may be older. Before any release independently compare authenticated live response, Cloudflare deployment SHA and the staged candidate.

| Priority | Public surface / evidence | Visible claim or transaction risk | Safe remediation to test (NOT deployed) | Acceptance evidence |
| --- | --- | --- | --- | --- |
| P0 | [Home](https://saveonsub.com/) | ChatGPT Plus from ৳499, Google AI Pro ৳500, displayed compare-at prices, SHARED badges and fast-delivery/warranty generalization | No fixed sell price or comparative % while HOLD. Preserve heading, product intent and WhatsApp inquiry; do not present unapproved checkout | Staged EN homepage has no priced offer / conflicting structured data |
| P0 | [All catalog](https://saveonsub.com/all) | `Add ৳499`/`Add ৳500` actions on historical SKUs and displayed savings | Inquiry-only listing and non-actionable cart for HOLD; labels not permission to sell | All 72 product IDs preserve URLs, zero active cart action and 0 priced JSON-LD offers |
| P0 | [ChatGPT Plus](https://www.saveonsub.com/p/chatgpt-plus) | Historical Starter/Premium shared login tiers, 5–15-minute delivery, price-match/warranty and personal claims; cached snapshot may predate today | Source-based neutral product facts; mark provider rights/quote pending, remove unsupported variants and public price, preserve indexed URL | Staged product page + FAQ + WhatsApp prefill have no shared-access sale promise or fixed price |
| P0 | [Bangla homepage](https://saveonsub.com/bn) | historical ৳499, ৳500, 211+ orders, bestseller ranking and universal quick-delivery claims | Rewrite unsupported numeric and superlative assertions as qualified current information, preserving Bangla usability | EN/BN parity test and page-level QA |
| P0 | [ChatGPT price guide](https://saveonsub.com/blog/chatgpt-plus-price-in-bangladesh) | Historical ৳499 shared, ৳2,990 personal and comparative privacy/warranty/risk statements | Keep pricing-intent URL; date verified provider claims, transparent access conditions and inquiry-only status; no provider-permission inference | No stale offer in blog text, CTAs, metadata or schema; avoid fake modified dates |
| P0 | [FAQ](https://saveonsub.com/faq) | shared seat recommendations and provider-specific price claims that may not be valid for SOS | Remove unsupported purchasable fixed offers, explain inquiry/verification, preserve useful customer-safety FAQ | FAQ matches current governed policy; no fixed-price sales invitation |
| P0 | [Checkout](https://saveonsub.com/checkout) | Client-side order + WhatsApp handoff previously had empty item lines / TOTAL ৳0 after cart cleared | Draft code change captures link before clearing validated cart; payment status always UNVERIFIED until staff verifies merchant-side receipt; no checkout of HOLD plans | Synthetic Node VM regression: items, qty, BDT total, order ID, payment method, local order persistence, emptied cart |
| P0 | [llms.txt](https://saveonsub.com/llms.txt), JSON-LD, sitemap | Legacy generator `build_seo.py` writes hard-coded prices, SEO answers and unsupported counts/privacy claims | Disable retired direct generator. Canonical `build_site.py` / price sanitizers only; no indexed URL loss | Generated llms.txt, schema/FAQ, EN/BN, sitemap, AI-search snippets independently audited |
| P1 | Source `catalog.json` and `assets/catalog.js` | Internal price-precedence metadata references another unit and old FX; legacy `status=live` is not approval | Restrict browser JSON metadata, explicit `sellability=inquiry_only`; do not remove historical source or rename IDs without SEO migration | Test confirms no price precedence / FX anchor / nested `bdt` in generated public JS |
| P1 | Historical `aips-*` bundle IDs | Five historic bundle IDs use another business's prefix; possible contamination of product taxonomy, not proof of customer data mixing | CEO/source provenance review; make no URL/ID change without canonical/redirect plan | Approved mapping, ownership decision, preserved SEO links |

## Code actions performed on draft PR #76 (NOT LIVE)

- Disable direct `build_home.py` and `build_seo.py` execution before their legacy modules can write fixed-price SEO/home content.
- Enforce explicit HOLD in `catalog_hold_gate.py` and public `build_public_catalog.py`; prune historical pricing provenance and fail if a nested amount survives.
- Capture WhatsApp order URI before checkout's local cart is cleared; do not claim payment verified or generate a real sale.
- Regression tests check legacy code has no side effects, public metadata/amounts do not leak, invalid catalog never overwrites safe JS, and synthetic checkout preserves correct item lines/total/order details.
- Canonical build, Actions CI, provider legality, precise live deployment and authenticated browser/payment acceptance **remain unverified**; PR #76 must remain DRAFT.

## Source and dependency closure

Existing [Issue #69](https://github.com/sysmoai/saveonsub-store/issues/69) and [Issue #70](https://github.com/sysmoai/saveonsub-store/issues/70) own releases and operational flow. [Business OS PR #75](https://github.com/sysmoai/saveonsub-store/pull/75) is downstream of payment/Access PRs; forward-port tested fixes only after review. No Cloudflare deploy, role grant, D1 migration, expense, price change, customer outreach or provider purchase follows from this review.

### Exact P0 acceptance checklist

- [ ] Run branch real CI/full canonical build and all Node + Python regression tests.
- [ ] Inspect whole staged `_site` for stale price and claims in EN/BN, category, bundle, blog, FAQ, checkout, redirects, OpenGraph, JSON-LD, sitemap, llms.
- [ ] Test no unauthorized new/old cart purchases, including localStorage tampering, malformed SKU and back-button behavior.
- [ ] Reconcile deployed Cloudflare SHA, current public crawl and candidate release diff with rollback artifact.
- [ ] CEO separately signs product eligibility/price/terms, public claim remediation and production release before any deploy.
