# SAVEONSUB Evolution Architecture v3

**Status:** Design baseline / implementation plan  
**Date:** 2026-08-10 · Asia/Dhaka  
**Scope:** SAVEONSUB only  
**Current baseline:** `main@9218ddfc4f6fd0fb607bac6c4a672958540a76fa`  
**Safety branch:** `fix/sos-p0-truth-gates-20260810`

## 0. Non-destructive architecture contract

This architecture is an evolution of the current SAVEONSUB stack, not a rewrite.

The following are mandatory invariants:

1. Keep the current Python-generated static architecture as the public content foundation.
2. Keep existing public product URLs (`/p/<id>.html`) and Bangla equivalents (`/bn/p/<id>.html`).
3. Keep current category, blog, trust, PWA, CSS, JavaScript and Cloudflare deployment capabilities unless a replacement has been proven in preview first.
4. Never require a framework migration (React/Next/Vue/etc.) merely to add commerce capabilities.
5. Never make the browser authoritative for price, order, payment or fulfillment truth.
6. Never hand-edit generated product pages as the primary fix when a generator/source exists.
7. Never deploy the repository root; publish only the staged public artifact.
8. All protected contact/payment/legal/provider/pricing values remain authority-controlled.
9. Every migration is additive first, parity-tested second, cut over third, and reversible.
10. Existing pages must continue to render even if the new backend is unavailable.

## 1. Current system being preserved

Measured current flow:

`catalog.json + Python generators -> committed static HTML/assets -> audits -> stage_deploy.py -> _site -> Cloudflare Pages -> saveonsub.com`

Current measured inventory:

- 72 products
- 13 categories
- 234 repository HTML files
- 200 sitemap URLs
- 72 English product pages
- 72 Bangla product pages
- 13 English category pages
- 13 Bangla category pages
- 13 blog pages
- 10 mode-detail pages

Current browser runtime remains useful and is retained:

- `assets/style.css`
- `assets/app.js`
- localStorage cart UX
- PWA/service worker
- language suggestion
- WhatsApp fallback/handoff
- static EN/BN SEO routes

Current limitations that v3 addresses:

- product/plan/media/commercial authority are too tightly coupled in `catalog.json`;
- product pages have a generated social card but no scalable product media gallery model;
- client-side order IDs/localStorage are not a durable order system;
- browser price values cannot be trusted as transactional truth;
- no backend order/payment/fulfillment ledger;
- no internal media/content administration layer;
- no durable event/commerce observability;
- no formal per-plan route model;
- public proof/order claims are not evidence-bound;
- provider eligibility and launch authority are not first-class commercial gates.

## 2. Target architecture

```text
                                  SAVEONSUB
                                      |
             +------------------------+-------------------------+
             |                                                  |
             v                                                  v
   CONTENT / DISCOVERY PLANE                         COMMERCE / OPERATIONS PLANE
   (existing architecture retained)                  (additive Cloudflare edge layer)
             |                                                  |
   catalog/content sources                                   Worker API
             |                                                  |
   Python generators                               +------------+-------------+
             |                                      |            |             |
   committed static output                         D1          Queues       Turnstile
             |                                      |            |             |
   stage_deploy.py                           orders/events   async jobs    abuse control
             |
   Cloudflare Pages
             |
   saveonsub.com
             |
   +----------------------+-----------------------+
   |                      |                       |
product/category/blog    Images                  Stream
static pages             product media          product/demo video
```

The public website remains usable as a static site. Dynamic systems enhance trusted commerce but do not become a hard dependency for content rendering.

## 3. Architecture planes

### 3.1 Content and discovery plane — Git/Python/static

This remains the canonical public-content system.

Responsibilities:

- product identity and descriptions;
- category structure;
- English and Bangla content;
- product/plan route generation;
- media references and accessible metadata;
- SEO metadata and structured data;
- blog/guides/comparisons;
- public navigation/footer/trust content;
- product comparison and recommendation content;
- static fallbacks when API services are unavailable.

Benefits retained:

- very fast first byte and rendering;
- low hosting complexity;
- excellent crawlability;
- deterministic reviewable releases;
- simple rollback to a known Git SHA;
- strong performance on slower Bangladesh mobile connections.

### 3.2 Commerce and operations plane — Cloudflare Worker + D1

New trusted server-side system.

Responsibilities:

- validate product/plan sellability;
- validate current approved price;
- create server-side order IDs;
- recalculate checkout totals;
- store orders and order items durably;
- store payment attempts/status only when authorized;
- store fulfillment state transitions;
- issue safe order-tracking tokens;
- protect writes with Turnstile/rate controls;
- generate auditable events;
- enqueue asynchronous work only when required.

The API must never trust product name, price, discount, availability or total supplied by the browser.

### 3.3 Media plane — Images + Stream + optional R2

Media becomes a first-class product capability without bloating Git or page weight.

**Cloudflare Images**

Use for:

- product hero photography;
- screenshots;
- feature illustrations;
- plan graphics;
- comparison images;
- thumbnails;
- optimized responsive delivery.

**Cloudflare Stream**

Use for:

- product demos;
- setup walkthroughs;
- tutorial videos;
- short product explainers;
- customer education videos.

**R2**

Use only where a generic object store is the better fit:

- original/source design files;
- downloadable guides/assets;
- media archives;
- private artifacts that should be served through a Worker rather than directly exposed.

The existing `assets/` directory remains supported as a local media source and fallback.

## 4. Product and plan information architecture

### 4.1 Product remains the parent entity

Existing canonical URLs are permanent compatibility contracts:

- English: `/p/<product-id>.html`
- Bangla: `/bn/p/<product-id>.html`

A product page becomes the ecommerce parent page containing:

1. breadcrumb;
2. media gallery;
3. product name/provider/category;
4. concise verified value proposition;
5. commerce state / availability;
6. plan selector/cards;
7. feature matrix;
8. who it is for / not for;
9. delivery/fulfillment explanation;
10. provider-safe disclosures;
11. comparison/official-source links;
12. setup/demo video if available;
13. FAQ;
14. related products;
15. related guides;
16. evidence-backed review/proof blocks only when verified.

### 4.2 Every plan gets a stable dedicated route

Target route form:

- English: `/p/<product-id>/<plan-slug>.html`
- Bangla: `/bn/p/<product-id>/<plan-slug>.html`

Examples:

- `/p/example-product/personal-1-month.html`
- `/bn/p/example-product/personal-1-month.html`

A plan page contains:

- parent product identity;
- exact plan label;
- duration;
- availability;
- approved current price if publication is authorized;
- fulfillment model;
- delivery SLA;
- exact inclusions/exclusions;
- account/seat ownership model;
- provider-policy state;
- warranty/refund terms that actually apply;
- dedicated media where useful;
- parent-product link;
- add-to-cart or inquiry action only when commerce eligibility permits it.

### 4.3 Plan page indexing rule

Every plan may have a dedicated page for users, but not every plan should automatically become a search-indexed page.

Default:

- page exists;
- linked from parent product;
- `noindex,follow` until it contains sufficiently unique, useful, verified content.

Only independently valuable plan pages enter the sitemap and use self-canonical/indexable status.

This prevents thin SEO duplication while still providing true ecommerce-style plan detail routes.

### 4.4 Structured data rule

Parent product pages continue to use truthful `Product`/`Offer` markup when commerce is eligible.

Plan pages use a single relevant `Offer` attached to the product where truthful.

Do not force subscription plan types into unsupported Google physical-product variant dimensions merely to obtain variant rich results. Product variant markup is used only where the semantics genuinely match supported search-engine expectations.

## 5. Catalog v2 normalization

The existing `catalog.json` remains readable throughout migration.

Do not replace it in one operation.

Introduce a compatibility loader:

`catalog.json -> catalog_model.py -> normalized v2 objects -> existing/new generators`

The loader first maps v1 data into a v2 in-memory model. Existing generated output is parity-tested before any source split.

Target logical entities:

### Product

```json
{
  "id": "stable-product-id",
  "name": {"en": "...", "bn": "..."},
  "category_id": "...",
  "provider_id": "...",
  "official_url": "...",
  "status": "active|info_only|retired",
  "summary": {"en": "...", "bn": "..."},
  "feature_ids": [],
  "plan_ids": [],
  "media_ids": [],
  "seo": {},
  "content_version": 1
}
```

### Plan

```json
{
  "id": "stable-plan-id",
  "product_id": "stable-product-id",
  "slug": "personal-1-month",
  "label": {"en": "...", "bn": "..."},
  "duration": "P1M",
  "fulfillment_mode": "...",
  "delivery_sla_id": "...",
  "commerce_state": "eligible|info_only|blocked|retired",
  "price_id": "...",
  "provider_eligibility_id": "...",
  "media_ids": [],
  "search_index": false
}
```

### Pricing record

Price is separated from stable plan identity.

```json
{
  "id": "price-record-id",
  "plan_id": "stable-plan-id",
  "currency": "BDT",
  "amount": 0,
  "effective_from": "...",
  "effective_to": null,
  "authority_ref": "...",
  "status": "approved|draft|expired"
}
```

Public generators consume only current approved SAVEONSUB pricing when public-price authority permits it.

### Provider eligibility record

```json
{
  "id": "provider-rule-id",
  "plan_id": "stable-plan-id",
  "commercial_state": "allowed|direct_provider_only|blocked|unknown",
  "evidence_ref": "...",
  "verified_at": "...",
  "review_due": "..."
}
```

Unknown does not become sellable.

### Media record

```json
{
  "id": "media-id",
  "product_id": "stable-product-id",
  "plan_id": null,
  "kind": "image|video|graphic",
  "role": "hero|gallery|feature|demo|howto|comparison",
  "provider": "local|cloudflare_images|cloudflare_stream|r2",
  "source_id": "...",
  "alt": {"en": "...", "bn": "..."},
  "caption": {"en": "...", "bn": "..."},
  "width": 0,
  "height": 0,
  "duration_seconds": null,
  "poster_media_id": null,
  "sort_order": 0,
  "public": true
}
```

## 6. Source layout target

Migration target while keeping existing files functional:

```text
/
|-- catalog.json                  # v1 compatibility until retired safely
|-- catalog_model.py              # compatibility/normalization layer
|-- data/
|   |-- products/
|   |   `-- <product-id>.json
|   |-- plans/
|   |   `-- <plan-id>.json
|   |-- media/
|   |   `-- media_registry.json
|   |-- pricing/
|   |   `-- approved_prices.json
|   |-- providers/
|   |   `-- eligibility.json
|   `-- authority/                # never public
|       |-- contacts.json
|       |-- payments.json
|       `-- legal.json
|-- components/
|   |-- product_gallery.py
|   |-- product_header.py
|   |-- plan_card.py
|   |-- plan_table.py
|   |-- media.py
|   |-- faq.py
|   |-- related.py
|   `-- commerce_cta.py
|-- build_product_pages.py
|-- build_plan_pages.py
|-- build_category.py
|-- build_home.py
|-- build_seo.py
|-- build_assets.py
|-- routes.py
|-- templates.py
|-- assets/
|-- p/
|-- bn/p/
|-- c/
|-- bn/c/
`-- _site/
```

Names are target design names; migration must be incremental rather than a bulk rename.

## 7. Media UX architecture

### Product gallery

Each product page supports:

- one hero visual;
- optional thumbnail gallery;
- optional screenshots/feature graphics;
- optional video thumbnail(s);
- full-screen/lightbox viewing;
- accessible keyboard controls;
- explicit dimensions to prevent layout shift;
- English/Bangla alt text.

### Image performance

Rules:

- hero/LCP image is not lazy-loaded;
- hero uses explicit dimensions and an appropriate responsive source;
- below-the-fold gallery images use native lazy loading;
- responsive sizes are served instead of one oversized image;
- modern formats are preferred through the image delivery layer;
- product social-card generation remains independent from gallery media.

### Video performance

Rules:

- video does not auto-download by default;
- use a poster/thumbnail;
- use lazy loading or click-to-load where applicable;
- use `preload="none"` or metadata only as appropriate;
- captions/transcripts are supported for meaningful long-form video;
- meaningful product/demo videos may emit valid `VideoObject` structured data.

## 8. Product-page component architecture

The current generator contains substantial inline HTML. v3 progressively extracts reusable Python rendering components while leaving output static.

Target component contract:

```text
render_product_page(product, context)
  |- render_breadcrumbs()
  |- render_product_gallery()
  |- render_product_header()
  |- render_commerce_state()
  |- render_plan_selector()
  |- render_feature_matrix()
  |- render_delivery_block()
  |- render_provider_disclosure()
  |- render_demo_media()
  |- render_faq()
  |- render_related_products()
  |- render_related_guides()
  `- render_structured_data()
```

The same data model feeds English and Bangla renderers; translation fields must never be inferred at runtime from English commercial facts.

## 9. Runtime API design

Initial API is intentionally small.

Target host:

`api.saveonsub.com`

Initial endpoints:

```text
GET  /v1/catalog/version
GET  /v1/plans/<plan-id>/quote
POST /v1/orders
GET  /v1/orders/<public-token>
POST /v1/orders/<public-token>/contact
```

Later, only when authorized:

```text
POST /v1/payments/initiate
POST /v1/payments/webhook/<provider>
POST /v1/admin/orders/<id>/payment-confirm
POST /v1/admin/orders/<id>/fulfillment
```

### Order creation contract

Browser submits identifiers and quantity, not trusted prices:

```json
{
  "idempotency_key": "...",
  "items": [
    {"plan_id": "...", "quantity": 1}
  ],
  "customer": {"name": "...", "contact": "..."},
  "turnstile_token": "..."
}
```

Server:

1. validates Turnstile;
2. validates request shape;
3. resolves plan IDs;
4. verifies commerce eligibility;
5. reads current approved price;
6. recomputes totals;
7. creates one order idempotently;
8. stores immutable price snapshot/order lines;
9. returns public order ID + tracking token.

## 10. D1 data model

Start as a modular monolith, not microservices.

Core tables:

```text
catalog_versions
plans_runtime
prices_runtime
orders
order_items
order_contacts
payment_attempts
fulfillment_events
order_status_history
idempotency_keys
audit_events
```

Optional later tables:

```text
customers
customer_identities
support_threads
media_drafts
content_drafts
webhook_events
analytics_events
```

Important constraints:

- order ID immutable;
- order item plan ID immutable;
- order price snapshot immutable after creation;
- status transitions append history;
- payment webhooks idempotent;
- queue messages idempotent;
- sensitive data minimized;
- no secrets stored in client assets.

## 11. Checkout migration without breakage

### Phase A — observe only

Keep current cart/checkout behavior.

Add no backend dependency.

Build and test the API separately.

### Phase B — shadow quote

When a visitor views checkout, request a server quote in the background.

Compare browser total vs server total.

Do not change customer behavior yet.

Log mismatches.

### Phase C — server order creation

Use server quote/order ID as truth.

Keep localStorage as UX/cache/fallback only.

### Phase D — payment integration

Only after payment destination/provider authority is explicitly approved.

### Phase E — fulfillment automation

Only after the fulfillment model is provider-safe and operationally proven.

## 12. Admin architecture

Do not expose a public CMS/admin in the first migration.

Initial management remains Git-reviewed.

Target later internal admin:

`admin.saveonsub.com`

Recommended internal capabilities:

- upload/select product images;
- upload/select videos;
- reorder gallery media;
- draft product/plan copy;
- manage availability;
- review order queue;
- confirm manual payment only when authorized;
- update fulfillment state;
- view audit log.

Admin authentication should be isolated from customer sessions. The admin should never publish protected commercial facts without a review/authority workflow.

A media upload action should upload directly to Cloudflare Images/Stream with restricted one-time upload authorization where possible; API secrets must never be exposed to the browser.

## 13. Security architecture

### Existing controls retained

- CSP/security headers;
- static public artifact boundary;
- no repository-root deployment;
- explicit public JSON boundary;
- no backend secrets in generated pages.

### New controls

- Turnstile on order/admin write flows where appropriate;
- mandatory server-side Turnstile verification;
- input validation at API boundary;
- prepared SQL statements;
- idempotency for order/payment/queue writes;
- per-route rate limiting/rules;
- least-privilege Cloudflare bindings;
- secrets only in Worker secret storage/configuration;
- append-only audit events for protected state changes;
- admin isolated behind an authenticated control plane;
- payment/provider webhooks verified according to provider specification;
- customer-facing order lookup uses opaque public token, not sequential database ID.

## 14. Queue architecture

Do not introduce a queue for simple synchronous checkout validation.

Use Cloudflare Queues only for work that benefits from asynchronous retries:

- fulfillment request dispatch;
- notifications;
- analytics/event fan-out;
- webhook post-processing;
- media processing coordination;
- content refresh jobs.

Every queue message gets a unique event ID and consumer de-duplicates before causing side effects.

A dead-letter queue is required for critical fulfillment/payment workflows once queues are introduced.

## 15. Observability

Each API request should carry a request/correlation ID.

Record structured logs for:

- request ID;
- route;
- order public ID where applicable;
- result status;
- validation failure class;
- latency;
- catalog version;
- price version;
- commerce eligibility version;
- queue event ID.

Never log payment secrets, passwords, full tokens or unnecessary personal data.

Track operational metrics:

- checkout quote success/failure;
- browser/server total mismatches;
- order creation success;
- duplicate/idempotent requests;
- payment-state transitions;
- fulfillment SLA states;
- media delivery errors;
- API 4xx/5xx;
- page performance regressions.

## 16. Build/release architecture

Target non-production CI:

```text
source change
   |
   v
schema validation
   |
normalized catalog validation
   |
product/plan/media parity
   |
regenerate static output
   |
check generated diff
   |
SEO/schema validation
   |
link/media validation
   |
security/release checks
   |
stage_deploy.py
   |
preview artifact
```

Production remains a separate authorized action.

Required gates grow to include:

- `inventory_site.py`;
- JSON/schema validation;
- product/plan ID uniqueness;
- no orphan plan pages;
- EN/BN route parity policy;
- media-reference validity;
- image alt-text completeness;
- sitemap/canonical parity;
- generated-output parity;
- internal-data leak check;
- release authority gate;
- smoke-test manifest.

## 17. Release artifact manifest

Every release should eventually produce an internal manifest:

```json
{
  "git_sha": "...",
  "catalog_hash": "...",
  "catalog_version": "...",
  "price_registry_hash": "...",
  "provider_registry_hash": "...",
  "product_count": 72,
  "plan_count": 0,
  "public_route_count": 0,
  "media_reference_count": 0,
  "generated_at": "...",
  "launch_state": "..."
}
```

Counts are generated, never typed manually.

The commerce Worker records the catalog/price version used to create each order.

## 18. Backward compatibility rules

### URLs

Existing URLs never change merely because architecture changes.

If a route must change in the future, a permanent redirect and canonical migration plan are mandatory.

### Cart

Existing localStorage cart keys are read during migration.

A cart schema version is introduced before changing structure.

### Service worker

Every cached-asset behavior change gets a new cache version through the existing content-hash mechanism.

### CSS

Current class names remain functional while new component classes are added.

### JavaScript

New modules are additive. Existing global functions remain until all generated pages are migrated and tested.

### Catalog

`catalog.json` remains an accepted input until the v2 adapter proves output parity.

## 19. Migration phases

### Phase 0 — truth and protection

Already in progress on the safety branch:

- architecture census;
- gap register;
- launch-state control;
- fail-closed release validation;
- safer `_site` staging;
- inventory parity tool;
- no PR deployment to production-equivalent branch.

Exit criteria:

- architecture inventory reproducible;
- production authority understood;
- provider/commercial blockers visible;
- no internal JSON leak;
- branch/preview workflow safe.

### Phase 1 — normalized model without visual change

Add:

- `catalog_model.py` adapter;
- IDs/validation for every plan;
- price registry abstraction;
- provider eligibility abstraction;
- media registry abstraction;
- route helper abstraction;
- schema validation.

Requirement:

Generated current pages must remain materially identical unless a separately approved truth/compliance correction is intended.

### Phase 2 — media-capable ecommerce product pages

Add:

- product gallery component;
- Cloudflare Images/local provider adapter;
- video component/Stream adapter;
- feature table;
- plan cards with dedicated detail links;
- accessible responsive images;
- VideoObject support where applicable;
- plan page generator;
- EN/BN plan routes.

No backend dependency required yet.

### Phase 3 — non-production commerce API

Add:

- Worker project;
- D1 schema/migrations;
- quote endpoint;
- order endpoint;
- order tracking endpoint;
- Turnstile validation;
- structured logging;
- idempotency.

Run only in preview/test until data and security tests pass.

### Phase 4 — shadow validation

Existing checkout still completes through the current flow.

New API receives background quote requests and compares totals/availability.

No customer transaction is blocked by the new API during shadow testing.

### Phase 5 — server-authoritative orders

Switch order creation to API only after:

- successful shadow parity;
- rollback path proven;
- order data privacy reviewed;
- contact/payment authority reconciled;
- monitoring active.

WhatsApp remains a fallback/support channel.

### Phase 6 — operational admin

Add internal admin only after the backend model is stable.

Media upload/selection is the first safe admin use case.

Commerce mutation controls remain permissioned/audited.

### Phase 7 — payment and fulfillment automation

Only after provider/payment/legal authority and implementation evidence exist.

Introduce:

- authorized payment integration;
- verified webhook processing;
- queue-backed notifications/fulfillment where useful;
- reconciliation reporting.

### Phase 8 — customer experience layer

Optional later capabilities:

- customer account/order history;
- saved comparisons;
- product recommendations;
- renewal reminders;
- support history;
- personalized but privacy-respecting discovery.

Do not require account creation for basic browsing.

## 20. Product media authoring workflow

Initial safe workflow:

1. upload approved media to Cloudflare Images/Stream or add a local asset;
2. receive stable media ID;
3. add media record to internal source;
4. run schema/media validation;
5. regenerate product page;
6. preview EN and BN pages;
7. test image/video performance and accessibility;
8. review diff;
9. release through normal gates.

Later admin workflow may automate steps 1-4, but still produces a reviewable content revision before public publishing.

## 21. Dedicated product/plan page acceptance criteria

A product page is complete only when:

- stable product ID exists;
- EN/BN route policy is satisfied;
- category membership valid;
- provider URL/evidence state valid;
- media hero/fallback valid;
- all plan references resolve;
- commerce actions match eligibility;
- structured data matches visible content;
- canonical/hreflang correct;
- mobile layout passes;
- keyboard/focus behavior passes;
- no unsupported proof is displayed.

A plan page is complete only when:

- stable plan ID exists;
- parent product resolves;
- duration/fulfillment/SLA are explicit;
- price status is current/authorized or price is omitted;
- eligibility is explicit;
- CTA behavior is allowed for the current commerce state;
- canonical/indexing rule is explicit;
- parent/plan structured data is truthful;
- page provides meaningful information beyond duplicating the parent.

## 22. Performance budget direction

Do not sacrifice the current static-site speed for richer media.

Enforce:

- responsive images;
- explicit image dimensions;
- hero-only priority loading;
- lazy noncritical media;
- click/lazy video loading;
- no autoplay video with sound;
- minimal JavaScript for product rendering;
- static HTML for essential product/plan facts;
- no client-only rendering for SEO-critical content;
- cache-safe versioning for code/catalog assets.

## 23. SEO architecture direction

Preserve:

- static crawlable pages;
- canonical URLs;
- EN/BN hreflang;
- sitemap generation;
- product structured data;
- breadcrumbs;
- blog/category internal linking.

Add:

- media-aware image metadata;
- video structured data where eligible;
- plan page indexing policy;
- automated canonical/hreflang validation;
- automated orphan-page detection;
- product/plan sitemap segmentation if the indexable surface grows materially;
- search performance feedback loop once Search Console evidence is connected.

## 24. Failure and fallback behavior

If commerce API is unavailable:

- product/category/blog pages still load;
- media still renders;
- browsing/search works;
- cart may remain local;
- checkout clearly reports that server order creation is unavailable rather than inventing success;
- WhatsApp support fallback may remain available if current contact authority permits it.

If Images/Stream is unavailable:

- product hero has local/static fallback where configured;
- video area fails closed without breaking page layout.

If D1/Queue fails:

- no order is reported successful unless durable order creation is confirmed;
- retries use the same idempotency key;
- asynchronous failures are observable and recoverable.

## 25. What is deliberately NOT part of this architecture

- no full-site React/Next/Vue rewrite;
- no microservice explosion;
- no Kubernetes;
- no always-on origin server merely to serve static pages;
- no direct database rendering of every SEO page;
- no automatic public price changes from market scraping;
- no automatic provider-policy override;
- no unreviewed AI-generated customer claims;
- no public admin keys/tokens;
- no production migration without rollback evidence.

## 26. Immediate implementation sequence

The safest independently executable sequence is:

1. extend inventory to count plans and media readiness;
2. add non-deploy PR validation workflow;
3. introduce JSON/schema validation and stable plan IDs without changing public pages;
4. introduce `catalog_model.py` compatibility adapter;
5. prove regenerated output parity;
6. introduce media registry + local media gallery with one test product in preview only;
7. add Cloudflare Images adapter while retaining local fallback;
8. add Stream video component in preview;
9. build dedicated plan page generator with `noindex,follow` default;
10. expand product page components and preview across EN/BN;
11. only then start the separate Worker/D1 commerce layer.

This sequence improves architecture while keeping customer-facing transactional behavior isolated until the content/build foundation is proven.

## 27. External technical basis reviewed

The architecture was cross-checked against current first-party platform/search guidance including:

- Cloudflare Workers Static Assets and Pages-to-Workers migration guidance;
- Cloudflare D1 managed SQL/database bindings;
- Cloudflare Images storage/transformation delivery;
- Cloudflare Stream upload/player delivery;
- Cloudflare R2 object storage;
- Cloudflare Queues delivery/retry/DLQ guidance;
- Cloudflare Turnstile mandatory server-side verification;
- Cloudflare Workers observability/logging;
- Google Search Central ecommerce/product structured data;
- Google Search Central product variant guidance;
- Google Search Central video structured data and video SEO guidance;
- web.dev responsive image and video performance guidance.

## 28. Architecture decision

**Decision:** evolve SAVEONSUB into a hybrid static-edge ecommerce architecture.

**Keep:** Python generators, static pages, current URLs, Git review, EN/BN, PWA, CSS/JS, Cloudflare public hosting, current SEO structure.

**Add:** normalized product/plan/price/provider/media models, scalable media delivery, dedicated plan routes, a server-authoritative Worker/D1 commerce layer, abuse controls, observability and later internal administration.

**Do not cut over any customer-critical runtime path until its additive replacement has passed parity, preview, rollback and authority gates.**
