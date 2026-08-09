# SAVEONSUB Full Architecture & Site Census

**Measured:** 2026-08-10 · Asia/Dhaka  
**Domain:** `https://saveonsub.com/`  
**Repository:** `sysmoai/saveonsub-store`  
**Measured baseline:** `main@9218ddfc4f6fd0fb607bac6c4a672958540a76fa`  
**Working safety branch:** `fix/sos-p0-truth-gates-20260810`

## 1. Executive architecture

SAVEONSUB is a **Python-generated static commerce/PWA site**, not a conventional server-rendered application.

Canonical flow:

`catalog.json + Python generators -> committed HTML/assets -> audits/preflight -> stage_deploy.py -> _site -> Cloudflare Pages`

Browser behavior is provided by shared JavaScript and local browser storage. There is no measured application server or database in the current implementation.

## 2. Site census

### HTML files in the repository: 234

| Route/file family | Count | Purpose |
|---|---:|---|
| Root `*.html` | 23 | Home, store, checkout/order/support/trust/system pages |
| English product pages `p/*.html` | 72 | One page per catalog product |
| Bangla product pages `bn/p/*.html` | 72 | Localized product pages |
| English category pages `c/*.html` | 13 | Crawlable category landings |
| Bangla category pages `bn/c/*.html` | 13 | Localized category landings |
| Blog `blog/*.html` | 13 | 12 articles + blog index |
| Mode detail pages `modes/*.html` | 10 | Bundle/service mode landing pages |
| Bangla general pages `bn/*.html` | 18 | Localized store/support/trust pages |
| **Total** | **234** | |

### Sitemap/indexable URLs: 200

`sitemap.xml` contains 200 `<url>` entries.

| Sitemap group | Count |
|---|---:|
| English product URLs | 72 |
| Bangla product URLs | 72 |
| English category URLs | 13 |
| Bangla category URLs | 13 |
| Blog URLs | 13 |
| Other indexable store/support URLs | 17 |
| **Total** | **200** |

Therefore 34 HTML files are not in the sitemap: 24 operational/general pages plus 10 mode-detail pages.

## 3. Product catalog

### Products: 72
### Categories: 13

| Category | Products |
|---|---:|
| AI Assistants | 14 |
| AI Image & Design | 8 |
| AI Video | 9 |
| AI Voice & Music | 5 |
| AI Code & Dev | 5 |
| AI Writing | 4 |
| Workspace & Productivity | 2 |
| Entertainment | 7 |
| Education & Career | 2 |
| VPN & Security | 3 |
| Bundles | 10 |
| Gaming | 1 |
| BD Lifestyle | 2 |
| **Total** | **72** |

Product identity is expected to stay in parity across:

- `catalog.json` product IDs;
- `p/<id>.html`;
- `bn/p/<id>.html`;
- `assets/social/<id>.png`;
- sitemap product URLs;
- category ItemList membership.

`inventory_site.py` was added on the working branch to make that parity measurable on every future change.

## 4. Source-of-truth and generators

Primary structured source:

- `catalog.json` — product/category/plan/SEO/market metadata used by generators.

Generated/runtime derivative:

- `assets/catalog.js` — browser-consumable catalog data.

Current build pipeline in `build_all.sh`:

1. `build_catalog.py`
2. `build_assets.py`
3. `build_home.py`
4. `build_pages.py`
5. `build_trust.py`
6. `build_seo.py`
7. `build_category.py`
8. `audit_all.py`
9. `deploy_preflight.py`

Other control/audit scripts include `check_prices.py`, `post_deploy_audit.py`, `stage_deploy.py`, and on the working branch `validate_release.py` + `inventory_site.py`.

Generated HTML is committed to Git. CI intentionally ships reviewed committed output rather than regenerating the full site during deployment.

## 5. Frontend/runtime architecture

### Shared browser app: `assets/app.js`

Responsibilities currently include:

- cart in `localStorage`;
- cart totals/count/removal;
- client-side order ID generation;
- local order receipt/history storage;
- WhatsApp order handoff;
- toast notifications;
- site ticker/social-proof messages;
- clipboard helpers;
- mobile navigation;
- PWA/service-worker registration;
- Bangla-browser language suggestion;
- newsletter form that opens a WhatsApp confirmation flow.

### PWA/service worker: `sw.js`

- network-first navigation/pages so price-bearing pages prefer fresh network content;
- stale-while-revalidate for static assets;
- versioned cache name;
- offline fallback to `offline.html`;
- cache only successful same-origin responses.

### Styling

- shared `assets/style.css`;
- static HTML includes a small amount of page-local inline CSS where needed.

## 6. Commerce/order architecture

The current measured implementation is lightweight and mostly client-side:

`product page -> cartAdd() -> localStorage cart -> checkout page -> local receipt/order record -> WhatsApp/payment instruction flow`

No backend order API, authenticated customer account system, inventory database, server-side payment verification service, or transactional database has been measured in the current repo.

This makes the site operationally simple, but it limits reliable analytics, order reconciliation, fraud controls, customer history, automation, and server-side conversion measurement.

## 7. Localization architecture

The site has a strong English/Bangla route model:

- English product/category pages under `/p/` and `/c/`;
- Bangla equivalents under `/bn/p/` and `/bn/c/`;
- hreflang pairs use `en-bd`, `bn-bd`, and `x-default`;
- browser-language suggestion in `assets/app.js` points visitors to an available Bangla alternate.

The public sitemap contains both EN and BN product/category routes.

## 8. SEO/discovery architecture

Measured SEO surfaces include:

- canonical links;
- EN/BN hreflang;
- `sitemap.xml`;
- `robots.txt`;
- `llms.txt`;
- product `Product`/`Offer` JSON-LD;
- category `ItemList` JSON-LD;
- breadcrumbs;
- FAQ structured data on product/content pages;
- Open Graph/social images;
- crawlable static category and blog pages.

Current `robots.txt` globally allows crawling except checkout and explicitly allows several AI crawlers. On the safety branch this conflicts with the provisional L0 launch state and is intentionally blocked by the release validator until indexing authority is reconciled.

## 9. Hosting/deployment architecture

### Baseline main

The observed workflow targets Cloudflare Pages project `saveonsub` using Wrangler.

The baseline pipeline stages publishable content into `_site`; the repository root must never be deployed because it contains internal build/data/strategy material.

### Working safety branch

The draft safety PR adds/changes:

- no production-equivalent Cloudflare deployment on pull-request events;
- fail-closed release-integrity validation;
- all `.json` private by default in staging;
- explicit runtime JSON allowlist;
- launch-state control record;
- architecture/gap documentation.

GitHub Pages also remains enabled as a legacy public configuration, sourced from `gh-pages`; the currently observed branch contains only `.nojekyll`, not the storefront.

## 10. Public/private data boundary

Must remain private by default:

- `catalog.json` source/provenance;
- `aips-live.json`;
- Python/shell/build scripts;
- Markdown strategy/audit/marketing documents;
- control/authority records;
- pricing provenance;
- any future customer/order/payment evidence.

The working branch changes `stage_deploy.py` so JSON is excluded by default and any browser-fetched JSON requires an explicit public allowlist entry.

## 11. Current measured inconsistencies / risks

These are architectural/product-development inputs, not permission to change protected facts:

1. **Homepage count drift:** `index.html` Open Graph description still says `62+ subscriptions`, while the measured catalog is 72.
2. **Provider/commercial eligibility:** some shared-plan commerce, especially OpenAI-related sharing, is currently blocked by the safety validator pending compliant product modeling.
3. **Unsupported proof:** product/order/bestseller numbers exist without an attached SAVEONSUB evidence mechanism.
4. **Cross-brand pricing provenance:** active source metadata references AIPS; SAVEONSUB commercial pricing needs its own approved registry.
5. **Launch/indexing authority:** current public deployment/indexing state is not fully reconciled against the bootstrap-vs-launch authority model.
6. **Production parity unknown:** the execution environment could fetch the domain title through the web tool but could not independently resolve the domain via local DNS, so exact live-SHA parity is not proven.
7. **Legacy deployment drift:** GitHub Pages remains enabled while Cloudflare is the measured intended deploy path.
8. **No server-side commerce system:** conversion/order/customer analytics depend heavily on local browser state and WhatsApp rather than a durable backend.
9. **No verified Search Console baseline in this audit batch.**
10. **Analytics baseline is not trusted until a real measurement property and event model are verified.**

## 12. Safe development operating model

Every future development batch should follow:

1. Measure current `main` SHA and live behavior.
2. Run/record `inventory_site.py` counts and parity.
3. Reconcile authority for any protected price/contact/payment/legal/provider change.
4. Create a dedicated branch.
5. Change source/generator first; never hand-fix generated pages as the primary solution.
6. Regenerate deterministically.
7. Run inventory, audits, release validation and staging checks.
8. Review diff for page/product/SEO parity.
9. Preview/test customer journeys.
10. Merge/deploy only when release gates are appropriate for the current launch state.
11. Verify canonical live domain after deployment.
12. Record deployment SHA/ID and rollback point.

## 13. Growth direction: become the strongest AI-tools provider experience in Bangladesh

Engineering should optimize for **trust + discoverability + product utility + reliable fulfillment**, not only catalog size.

Priority layers:

- truth/authority/compliance first;
- accurate product and pricing registry;
- excellent Bangla + English SEO and comparison content;
- provider-safe product modeling;
- fast mobile UX for Bangladeshi networks;
- reliable conversion tracking;
- server-side order/lead/payment event capture when approved;
- customer support and fulfillment observability;
- evidence-backed reviews/testimonials;
- structured product comparison and recommendation tools;
- Search Console/analytics-driven content iteration;
- performance/accessibility regression gates.

This document is the architectural baseline; it does not itself authorize commerce, prices, payments, legal claims, DNS changes, or production release.
