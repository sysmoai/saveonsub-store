# SAVEONSUB Store — Engineering and Commercial Safety

**Canonical business:** SAVEONSUB / https://saveonsub.com
**GitHub:** [sysmoai/saveonsub-store](https://github.com/sysmoai/saveonsub-store)
**Production:** Cloudflare Pages project `saveonsub` — not Vercel or GitHub Pages.
**Authority:** CEO-approved commercial policy, provider eligibility and a verified release. A source file, green test or draft PR is NOT a live price or transaction approval.

## Current source truth (1 Nov 2026)

- `main:catalog.json` retains **72 historical products and 138 historical plan records**; these are source history, not a sellable current pricebook.
- Review branch PR #66 and its PR #76 follow-up hold all **72 products** at **zero approved sellable plans**, with explicit `EXEC-010`, `request_price=true` and `pricing_status=price-review-required`. Do not restore the 138 historic plans as customer offers.
- Affordable **BDT 499 entry-price lane** remains a **CEO commercial research objective**, with a possible exception to the former BDT 500-per-order contribution threshold. It does not authorize shared credentials, any exact plan, a published price, a refund rule, or payment collection.
- Full storefront and search-intent URLs must be preserved. Setup, training and support are optional services; do not replace the subscription store with consulting-only content.
- See [Issue #69](https://github.com/sysmoai/saveonsub-store/issues/69), [Issue #70](https://github.com/sysmoai/saveonsub-store/issues/70), [PR #76](https://github.com/sysmoai/saveonsub-store/pull/76), and [P0 public claims matrix](ops/SOS-P0-PUBLIC-CLAIMS-MATRIX-2026-11-01.md).

## Correct safe developer workflow

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest -v test_audit_home_prices
python3 -m unittest discover -v -s tests -p 'test_*.py'
python3 catalog_hold_gate.py
python3 build_site.py
python3 audit_commercial_truth_v2.py
python3 audit_all.py
```

- `build_site.py` is the **only canonical governed builder**. It writes a sanitized `_site/` candidate; running it is **not** a deployment.
- `build_all.sh` and `build_catalog.py` are safe compatibility entrypoints, delegating to the governed build/public catalog pipeline.
- `build_home.py` and `build_seo.py` are **retired**: direct execution fails closed because these historic generators contain stale pricing and unsupported commercial claims.
- `assets/catalog.js` is generated at build time from a scrubbed, inquiry-only projection. Never treat an old checked-in asset as proof of a reviewed release.
- The synthetic checkout test uses no real customer or payment data: `node tests/checkout_handoff_synthetic.mjs .`.

## Deployment protection

**Never deploy the repository root.** Only stage `_site/` to the exact authorized Cloudflare Pages project after the CEO approves the reviewed candidate. Public output must exclude `catalog.json`, Python scripts, staff APIs, SQL migrations, private records, customer data, source images and secrets. Follow `DEPLOY.md` and `.github/workflows/canonical-deploy-manual.yml` with rollback and canonical-domain smoke tests. Staging Cloudflare/D1/Access setup and production release are separate human-approval gates.

The private staff / Order OS is separately staged in draft [PR #75](https://github.com/sysmoai/saveonsub-store/pull/75). Historical local tests, an empty D1 resource or an HTML dashboard are **not** proof of live authenticated commerce. Human receiving-side payment verification is required before an order is marked paid; screenshots, typed references and browser localStorage are not verified settlement.

## Brand, safety and business separation

- Locked original SaveOnSub PNG is immutable. Never draw, regenerate or recolor the approved logo; use verified locked derivative assets.
- Canonical WhatsApp: **+8801305869242** / https://wa.me/8801305869242.
- No unverified bestseller/order counts, 100% privacy/ownership promises, universal instant delivery, misleading price comparisons, unsupported rights/resale claims, fake ratings, or price in structured data while commercial HOLD applies.
- No raw customer data, payment account details, credentials, supplier costs, margin ledgers or personal business secrets in this public repository.
- Keep other brands' products, finance, credentials, orders, evidence and customers strictly separate; legacy `aips-*` product IDs are a taxonomy/provenance review item, not authorization to merge businesses.
- Search performance and the 50K monthly organic traffic objective must be reported from real SOS-owned analytics. A target is never a measured result.

**Approval boundary:** No unapproved merge/deploy, price changes, money movement, D1 migration, Access grants, ad spending, bulk messaging, DNS changes or production schema changes.
