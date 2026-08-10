# SAVEONSUB v3 Architecture Readiness Audit

**Measured:** 2026-08-10 · Asia/Dhaka  
**Branch:** `fix/sos-p0-truth-gates-20260810`  
**Structural CI head:** `d1ff38815754e66aa733662dba43fc1304de61e6`  
**Workflow run:** `Validate Architecture` #1

## 1. Structural audit result

**PASS**

The non-deploy structural job successfully:

- parsed `catalog.json` as valid JSON;
- compiled `inventory_site.py`, `stage_deploy.py`, and `validate_release.py` under Python 3.12;
- ran product/route inventory parity successfully;
- staged the explicit public artifact through `stage_deploy.py`;
- verified no `.json` file entered `_site`;
- verified required public files exist in `_site`.

Staging result:

- public staged files: **322**
- staged size: **5.19 MB**
- internal JSON leak check: **PASS**

## 2. Exact current product/plan baseline

Machine-measured from the current catalog:

- HTML files: **234**
- sitemap URLs: **200**
- products: **72**
- plans: **138**
- categories: **13**
- root Python scripts: **16**
- JavaScript files: **3**
- CSS files: **1**
- product social PNGs: **72**

Product page parity:

- catalog product IDs: in parity with EN product pages;
- catalog product IDs: in parity with BN product pages;
- catalog product IDs: in parity with social PNG files;
- duplicate product IDs: **0**.

## 3. Current route baseline

- root HTML: **23**
- EN product pages: **72**
- BN product pages: **72**
- EN dedicated plan pages: **0**
- BN dedicated plan pages: **0**
- EN category pages: **13**
- BN category pages: **13**
- blog pages: **13**
- mode detail pages: **10**
- BN general pages: **18**

## 4. Current plan model baseline

138 catalog plans currently break down as:

### Plan `type`

- `personal`: **55**
- `shared`: **54**
- `bundle`: **10**
- `official`: **3**
- `unknown`: **16**

### Plan `tos`

- `personal`: **67**
- `shared-med`: **38**
- `shared-low`: **26**
- `official`: **7**

### v3 plan readiness

- plans with stable IDs: **0**
- plans missing stable IDs: **138**
- duplicate stable plan IDs: **0** (none exist yet)
- products without plans: **0**

This is the primary reason v3 introduces stable plan identity before creating dedicated plan pages or server-authoritative commerce records.

## 5. Current media readiness baseline

Catalog-first media modeling does not exist yet:

- products with first-class `media` field: **0**
- products with first-class `gallery` field: **0**
- products with first-class `video`/`videos` field: **0**
- dedicated EN plan pages: **0**
- dedicated BN plan pages: **0**

The existing site does have one generated social PNG per product, but that is an Open Graph/social-card pipeline rather than an ecommerce product-gallery model.

## 6. Current product status baseline

- `live`: **51**
- `new`: **12**
- `gap-fill`: **9**

v3 must not interpret these labels as sufficient commercial eligibility. A separate provider/commercial eligibility state is required.

## 7. Release-integrity result

**INTENTIONALLY BLOCKED**

`validate_release.py` reported **32 integrity failures**. This is expected while the existing P0/P1 commercial and authority gaps remain.

Failure classes observed include:

- active price precedence referencing AIPS;
- OpenAI/ChatGPT shared-commerce plans;
- unsupported order-count claims;
- unsupported bestseller claims;
- Terms normalizing provider-prohibited shared fulfillment;
- generated commerce below the provisional L0 state;
- commerce authorization missing;
- public-price authorization missing;
- robots/indexing state inconsistent with L0 control.

The architecture work must not disable or weaken these checks simply to produce a green release.

## 8. Additional metadata drift observed

GitHub repository description still advertises **64 products / 214 pages**, while the machine inventory is **72 products / 234 HTML files**.

This is public metadata drift, not architecture truth. Update only through a separate reviewed metadata change.

## 9. Readiness decision

SAVEONSUB is ready to begin **Phase 1 of Evolution Architecture v3** on a non-production branch:

1. stable plan IDs;
2. catalog normalization adapter;
3. media registry abstraction;
4. route helper abstraction;
5. schema validation;
6. deterministic parity tests.

It is **not** ready to switch production checkout/order/payment behavior to a new backend because release/commercial authority blockers remain open.

## 10. Safety conclusion

The architecture upgrade can proceed safely as additive source/model/preview work because:

- the existing public route structure is measured;
- current product parity is machine-verified;
- plan/media migration gaps are now quantified;
- public staging boundary is machine-verified;
- release blockers remain fail-closed;
- no production deployment is part of the v3 architecture commits.
