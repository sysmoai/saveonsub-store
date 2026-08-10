# SAVEONSUB v3 Architecture Readiness Audit

**Measured:** 2026-08-10 · Asia/Dhaka  
**Branch:** `fix/sos-p0-truth-gates-20260810`  
**Validated branch head before this audit-only freeze:** `9f346af06b05cb8ba45f3b25f0a14632f5742884`  
**Exact-head push validation run:** `Validate Architecture` run `31345900869`

## Readiness conclusion

SAVEONSUB Evolution Architecture v3 has a green strict L1 public-information release candidate and a separate intentionally red legacy storefront audit.

The architecture remains an additive evolution of the existing Python/static/Cloudflare stack. Existing canonical product URLs remain invariant. New plan/media/backend capabilities are introduced behind compatibility and fail-closed authority layers rather than by rewriting the storefront.

## Measured baseline

- 72 products
- 138 plans
- 13 categories
- 234 legacy repository HTML files
- 200 legacy sitemap URLs
- 72 EN + 72 BN legacy product pages
- 72 product social images

## V3 model state

- all 138 legacy plans normalize to deterministic unique v3 identities;
- all 138 have unique future EN routes and 138 unique BN routes;
- existing product routes remain unchanged;
- first-class media normalization exists with local social-image fallback;
- provider/commercial state is derived from protected authority registries;
- pricing is derived only from the SAVEONSUB pricing registry;
- `unknown` is not sellable;
- OpenAI shared commerce is blocked; OpenAI product paths are direct-provider/information-only under current provider evidence.

## Current authority state

Launch state: `L1_PUBLIC_INFO_ONLY`.

Authorized:
- public informational product/category pages;
- English/Bangla discovery;
- provider-status disclosures;
- official-provider links;
- indexing of non-commerce information pages.

Not authorized:
- SAVEONSUB selling prices;
- cart/checkout;
- payment destinations/instructions;
- server order creation;
- unverified WhatsApp CTA;
- unverified legal-operator claims;
- provider-prohibited fulfillment.

Protected registries remain fail-closed:
- WhatsApp value: pending owner input / null;
- payment destinations: pending owner input / empty;
- active SAVEONSUB price registry: empty;
- public price authorization: false;
- exact legal operator: pending primary evidence.

## Internal v3 preview tree

Validated preview-only output:
- 72 EN + 72 BN upgraded product-page previews;
- 138 EN + 138 BN dedicated plan-page previews;
- product/plan route parity;
- normalized media association;
- price-free/cart-free/Offer-schema-free plan pages;
- `noindex,follow` on plan pages.

Preview files are explicitly excluded from deployment.

## Strict L1 public-information artifact

The strict release builder produces `_public_v3`; it does not deploy/sanitize the legacy commerce tree.

Validated strict properties:
- 0 SAVEONSUB selling prices;
- 0 cart/checkout controls;
- 0 payment destinations;
- 0 WhatsApp destinations;
- 0 Offer/AggregateOffer schema;
- 0 raw `catalog.json` / `assets/catalog.js` publication;
- 0 unsupported numeric order/customer/user proof;
- 0 unverified legal-operator wording;
- canonical current product URLs preserved;
- plan detail pages excluded from sitemap and `noindex,follow`;
- internal JSON absent.

`stage_deploy.py --public-v3` stages only this strict artifact and refuses protected/legacy commerce paths.

## Exact validation evidence

At branch head `9f346af06b05cb8ba45f3b25f0a14632f5742884`, push run `31345900869` completed the full `structural-audit` successfully.

Green steps included:
- authority/control JSON validation;
- Python and JavaScript syntax checks;
- protected authority boundaries;
- normalized catalog model;
- inventory/parity;
- internal product/plan previews;
- strict L1 build/hardening;
- strict public-artifact validation;
- strict L1 release-authority gate;
- fail-closed D1 plan seed;
- shadow Worker validation and quote tests;
- bounded legacy staging;
- strict `_site` staging and boundary verification;
- release-candidate artifact upload.

The separate legacy/current-source release report remains intentionally red because the old price-bearing commerce tree is unsafe and must not become the deployment source.

## Cloudflare blocker

The same exact-head push run performed a read-only Wrangler credential probe. `wrangler whoami` failed against Cloudflare `/accounts` with `Invalid access token [code: 9109]`.

No Cloudflare resource was created, changed, deployed, or deleted by the credential probe.

Therefore:

- **L1 code/release-candidate readiness: PASS**
- **Cloudflare production deployment: BLOCKED_ACCESS**
- **commerce activation: NOT READY / NOT AUTHORIZED**

## Next execution sequence

1. replace the invalid Cloudflare Pages deployment token in GitHub Actions;
2. re-run read-only credential verification;
3. reconfirm strict exact-head validation;
4. merge the reviewed branch;
5. let `main` deploy only the strict L1 artifact;
6. verify `saveonsub.com` live behavior and deployment SHA;
7. record rollback point;
8. continue shadow Worker/D1 and media/admin phases;
9. enable commerce only after protected price/payment/contact/legal/provider registries are fully populated and all corresponding gates pass.
