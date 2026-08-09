# SAVEONSUB Bangladesh AI-Tools Leadership Roadmap

**Created:** 2026-08-10 · Asia/Dhaka  
**Scope:** `saveonsub.com` only  
**Operating rule:** grow through measured, reversible development; never bypass provider eligibility, price/contact/payment/legal authority, or release gates.

## Strategic position

SAVEONSUB already has a large bilingual static footprint: 72 products, 13 categories, 234 HTML files and 200 sitemap URLs. The next advantage should not be "more pages at any cost". The moat should be:

**Bangladesh-local payment convenience + bilingual discovery + verified product facts + provider-safe fulfillment + fast mobile UX + evidence-backed trust + excellent support.**

Current Bangladesh search results show a crowded market. Competitors emphasize large catalogs, bKash/Nagad/Rocket, fast activation, shared/group-buy access, and high customer-count claims. OneBrain also invests heavily in long-form Bangladesh-specific educational content. SAVEONSUB should differentiate by being more measurable and trustworthy rather than copying unsupported claims.

## Phase 0 — Integrity foundation (P0/P1 before growth)

Goal: make it difficult to deploy a commercially unsafe or internally inconsistent site.

- Merge fail-closed release/inventory controls after review.
- Resolve provider eligibility, especially shared-login models that violate provider rules.
- Create a SAVEONSUB-only approved pricing registry.
- Create one approved contact registry.
- Create one approved payment-destination registry.
- Reconcile exact legal operator wording.
- Make launch state drive commerce, public price visibility and indexing behavior.
- Remove or evidence unsupported order/bestseller/customer-count claims.
- Record previous-good production SHA/deployment ID for rollback.
- Disable or properly contain legacy duplicate hosting after authority is clear.

Exit criteria: no unresolved P0 can silently become public commerce.

## Phase 1 — Deterministic architecture & quality gates

Goal: every change is measurable before it reaches users.

- Run `inventory_site.py` in CI.
- Add source/generated parity manifest: source hash, generator version, catalog hash, route manifest, asset manifest and authority version.
- Add broken-link/canonical/hreflang validation.
- Add HTML/schema validation for Product, Offer, FAQ, ItemList and breadcrumbs.
- Add performance budgets for HTML/CSS/JS/image size.
- Add accessibility checks targeting WCAG 2.2 AA.
- Add mobile customer-journey smoke tests for EN and BN.
- Remove obsolete `.next`, `.astro`, Replit/Vercel artifacts only after proving they are unused.
- Correct measured content drift such as the homepage `62+` count after deterministic regeneration.

Target engineering SLOs:

- zero missing catalog/product/social/sitemap parity;
- zero broken internal links in shipped pages;
- zero unauthorized internal files in `_site`;
- mobile LCP < 2.5s, CLS < 0.1, INP < 200ms on representative pages;
- no critical accessibility violations.

## Phase 2 — Provider-safe product registry

Goal: make each product record operationally trustworthy.

Extend product data with explicit fields such as:

- provider;
- official product/tier name;
- commercial model (`official_direct`, `customer_owned_activation`, `provider_supported_seat`, `informational`, `blocked`);
- eligibility status;
- provider evidence URL/date;
- SAVEONSUB price approval ID/date;
- fulfillment SLA evidence;
- warranty/refund applicability;
- last verified date;
- public claims/evidence references.

Generators must only emit `Offer`, `InStock`, cart/checkout actions or sell prices when the product state permits commerce.

## Phase 3 — Durable commerce/lead backend

Goal: stop relying on browser-local state as the only operational record.

When commercially authorized, add a small, auditable backend for:

- server-generated order IDs;
- durable carts/orders/leads;
- payment method + transaction-reference capture;
- order status timeline;
- WhatsApp handoff with server-side order context;
- support notes;
- fulfillment state;
- refund/replacement state;
- consent/privacy events;
- event logging for conversion measurement.

Keep the static storefront if it continues to deliver speed; add backend services only where durable state is required.

## Phase 4 — Search & content leadership

Goal: own Bangladesh-specific AI buying/learning intent with useful pages, not thin SEO pages.

Build evidence-backed clusters around:

1. `AI subscription Bangladesh`
2. `ChatGPT / Claude / Gemini / Perplexity price in Bangladesh`
3. `buy AI tools with bKash/Nagad`
4. student AI stack Bangladesh
5. freelancer AI stack Bangladesh
6. developer AI tools Bangladesh
7. creator/video AI tools Bangladesh
8. business/team AI adoption Bangladesh
9. official vs local payment/activation explanations
10. provider comparisons and "which tool should I buy?" decision pages

For each cluster:

- English + Bangla where search intent exists;
- one primary canonical page per intent;
- original comparisons and provider-verified facts;
- internal links to product/category/help pages;
- FAQ only when visible content supports it;
- last-verified dates for prices/features;
- no unsupported superlatives or fake freshness.

## Phase 5 — Best-in-class discovery UX

Goal: help a Bangladeshi user select the right tool faster than a generic marketplace.

Develop:

- richer search/filter by job-to-be-done, price, provider, plan model, delivery and risk;
- compare 2–4 products side by side;
- improved "Find My AI" quiz driven by catalog facts;
- student/freelancer/developer/creator/business solution hubs;
- "free tier may be enough" recommendations where true;
- provider-direct purchase option when that is the safer/better choice;
- Bangla-first mobile navigation and search refinements;
- transparent "last verified" badges.

## Phase 6 — Trust system

Goal: make every trust claim auditable.

- verified-purchase review pipeline;
- evidence ID behind public order/customer/review counts;
- public support/fulfillment SLA methodology;
- clear replacement/refund state machine;
- incident/status history for material outages;
- transparent reseller/activation disclosure;
- privacy/minimization controls for customer data;
- security reporting contact.

Never publish a customer count, review rating, bestseller rank, savings percentage or delivery statistic without a documented evidence source and measurement window.

## Phase 7 — Measurement & conversion optimization

Goal: optimize with real data rather than assumptions.

Implement/verify:

- analytics property + consent model;
- Search Console property and sitemap monitoring;
- server-side order/lead events;
- funnel events: product_view, plan_select, add_to_cart, checkout_start, payment_instruction_view, whatsapp_handoff, order_created, fulfilled, refunded;
- UTM attribution;
- EN vs BN funnel comparison;
- product/category landing-page conversion;
- organic query/page cohorts;
- Core Web Vitals by template family.

Only after clean measurement should A/B tests change conversion-sensitive UX.

## Phase 8 — Scalable content/product operations

Goal: update 72+ products safely as providers change rapidly.

- scheduled provider fact review queue;
- stale-data alerts based on `last_verified`;
- price-change workflow with approval IDs;
- generator tests preventing missing EN/BN/social/sitemap assets;
- content templates with manual editorial requirements for YMYL/legal/payment/provider-risk sections;
- release notes for catalog changes;
- automatic noindex/informational fallback when eligibility becomes uncertain.

## Immediate sequence

1. Finish/merge architecture and safety controls.
2. Generate and persist the deterministic site inventory.
3. Resolve P0 provider/commercial/authority gaps.
4. Add source/generated parity CI.
5. Fix content-count drift through generators and deterministic rebuild.
6. Verify live domain/deployment SHA and rollback point.
7. Establish Search Console + analytics baseline.
8. Improve the highest-intent AI category/product pages using measured query data.
9. Design durable order/lead backend only after protected payment/legal/product requirements are approved.
10. Iterate from measured conversion, search and support data.

## Definition of "#1"

Do not use "#1" publicly without independent substantiation. Internally, treat leadership as a measurable scorecard:

- organic non-brand clicks for priority BD AI intents;
- top-3 keyword coverage;
- qualified conversion rate;
- fulfillment success/median time;
- support response time;
- verified repeat-purchase rate;
- refund/replacement rate;
- mobile Core Web Vitals pass rate;
- verified-review volume and rating;
- provider-compliance incident rate;
- EN/BN content coverage and conversion.

The target is to become the strongest AI-tools buying and guidance experience for Bangladesh by measured customer outcomes, not by an unsupported marketing label.
