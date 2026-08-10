# SAVEONSUB v3 Architecture Readiness Audit

**Measured:** 2026-08-10 · Asia/Dhaka  
**Branch:** `fix/sos-p0-truth-gates-20260810`  
**Current strict release-candidate head:** `52788f35f2cc9b8d372e800f7bc0a544520ac809`  
**Green validation run:** `Validate Architecture` run `31345771459`

## 1. Architecture baseline

SAVEONSUB remains a compatibility-first evolution of the existing Python-generated static storefront. Existing product IDs and canonical product URLs are preserved; new commerce/media systems are additive and remain fail-closed until separately authorized.

Machine-measured legacy baseline:

- HTML files: **234**
- sitemap URLs: **200**
- products: **72**
- plans: **138**
- categories: **13**
- EN product pages: **72**
- BN product pages: **72**
- product social PNGs: **72**

## 2. Normalized v3 model

The compatibility layer now provides:

- deterministic normalized identity for all **138 / 138** plans;
- unique future EN plan routes: **138 / 138**;
- unique future BN plan routes: **138 / 138**;
- immutable existing EN/BN product routes;
- first-class media normalization with current social-image fallback;
- provider eligibility derived from protected authority records;
- approved price lookup derived only from the SAVEONSUB pricing authority registry;
- `unknown` provider state treated as non-sellable;
- OpenAI shared plans blocked and OpenAI products routed to official-provider/information-only behavior under current provider evidence.

Legacy `catalog.json` remains migration input, not commercial authority.

## 3. Protected authority state

Current authority registries are separated by concern:

- contact authority;
- payment authority;
- pricing authority;
- provider eligibility;
- legal authority;
- launch state.

Current release state is **L1_PUBLIC_INFO_ONLY**.

Authorized now:

- informational EN/BN product pages;
- informational EN/BN category pages;
- provider-status disclosures;
- official-provider links;
- indexing of non-commerce informational routes.

Not authorized now:

- SAVEONSUB selling prices;
- cart/checkout;
- payment destinations/instructions;
- server order creation;
- unverified WhatsApp CTA;
- unverified legal-operator claims;
- provider-prohibited fulfillment.

The dedicated SAVEONSUB WhatsApp value remains pending owner input. Payment destinations remain pending owner input. The SAVEONSUB active-price registry remains empty and public-price authorization remains false.

## 4. Internal ecommerce previews

Preview-only generators now produce and validate:

- **72 EN + 72 BN** upgraded product-page previews;
- **138 EN + 138 BN** dedicated plan-page previews;
- product-to-plan route parity;
- normalized media association;
- price-free, cart-free, Offer-schema-free plan previews;
- `noindex,follow` on dedicated plan previews.

The preview workspace is explicitly excluded from `_site`.

## 5. Strict L1 public-information release artifact

A separate strict builder now produces `_public_v3` rather than sanitizing legacy generated pages at deploy time.

The strict artifact preserves current product URLs and generates:

- 72 EN product pages;
- 72 BN product pages;
- 138 EN dedicated plan pages;
- 138 BN dedicated plan pages;
- 13 EN category pages;
- 13 BN category pages;
- EN/BN home/discovery surfaces and minimal neutral trust/contact pages.

Strict L1 properties validated in CI:

- **0 public SAVEONSUB selling prices**;
- **0 cart/checkout controls**;
- **0 payment destinations**;
- **0 WhatsApp destinations**;
- **0 Offer/AggregateOffer schema**;
- **0 raw `catalog.json` / `assets/catalog.js` publication**;
- **0 unsupported numeric orders/customers/users proof**;
- **0 unverified legal-operator wording**;
- current product canonical URLs preserved;
- detail plan pages excluded from sitemap and marked `noindex,follow`;
- internal JSON absent from the release artifact.

`stage_deploy.py --public-v3` stages only this strict artifact and refuses protected paths.

## 6. Strict release-candidate CI result

`Validate Architecture` run `31345771459` completed with the structural/release-candidate job **SUCCESS**.

Successful steps include:

- control JSON validation;
- Python/JavaScript compile/syntax checks;
- protected authority boundary validation;
- v3 normalized catalog validation;
- current inventory/parity validation;
- EN/BN product/plan preview generation and validation;
- strict L1 build;
- strict L1 hardening;
- strict public-artifact validation;
- strict L1 release-authority gate;
- fail-closed D1 plan seed generation;
- shadow Worker validation and tests;
- bounded legacy staging;
- strict L1 `_site` staging;
- strict release-candidate boundary verification;
- release-candidate artifact upload.

The strict release candidate was uploaded as GitHub Actions artifact:

- artifact ID: `9047271757`
- artifact digest: `sha256:57cc9c0844724d3fe2f210d0ebcfd61bc62d2ffb75369690f800e7231efc8bf7`
- artifact source head: `52788f35f2cc9b8d372e800f7bc0a544520ac809`

## 7. Legacy release report

The separate legacy/current-source `validate_release.py` report remains intentionally red.

This is not a contradiction with the green strict L1 candidate. It proves that the old committed price-bearing commerce tree still contains historical commercial/provider/authority issues and therefore must **not** be the production deployment input.

The production workflow on this branch has been changed so it can deploy only the generated strict L1 artifact, never the repository root or legacy commerce tree.

## 8. Shadow commerce backend

A non-routed `saveonsub-commerce-shadow` Worker foundation now exists with:

- health/capability endpoints;
- server-authoritative quote logic;
- D1 runtime schema;
- all 138 seed plans defaulting to `unknown` + `NULL` price;
- client price ignored by quote calculation;
- blocked/unknown plans unable to quote;
- order creation hard-disabled;
- no customer/payment PII schema in the shadow phase.

It is not deployed because Cloudflare access is currently invalid and because commerce authority is not yet established.

## 9. Cloudflare infrastructure blocker

The existing GitHub Actions `CLOUDFLARE_API_TOKEN` currently fails Cloudflare authentication (`Invalid access token` / authentication error). Read-only Cloudflare identity/Pages/D1 inventory therefore cannot be trusted until the repository secret is replaced with a valid token for the correct account.

No Cloudflare resource has been created, modified, deployed, or deleted during these failed credential probes.

## 10. Current readiness decision

**Code / release-candidate readiness for L1 public information: PASS.**

**Production deployment: BLOCKED_ACCESS** until the Cloudflare credential in GitHub Actions is repaired.

**Commerce activation: NOT READY / NOT AUTHORIZED.** It remains blocked by protected provider/pricing/payment/legal/contact reconciliation even after the informational site is live.

Next execution sequence:

1. repair Cloudflare Pages deployment credential in GitHub Actions;
2. run a read-only credential validation on the branch;
3. reconfirm strict CI green at the exact head;
4. merge the reviewed branch;
5. allow `main` to deploy only the strict L1 artifact;
6. verify the live custom domain and deployment SHA;
7. record rollback point;
8. continue non-production Worker/D1 and media/admin phases;
9. enable commerce only after the protected authority registries are populated and all corresponding gates pass.
