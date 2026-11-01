# SaveOnSub issue #69 — engineering recovery and #75 staging reconciliation

Date: 2026-11-01 Asia/Dhaka. **REVIEW ONLY. No merge or deploy.**

## Source evidence
- `main:catalog.json`: 72 historical products/138 plans. These are **not** current sale approvals.
- PR #66 `catalog.json`: 72 products/0 plans; all carry `commercial_hold=EXEC-010`, `request_price=true`, `pricing_status=price-review-required`, governed revision.
- `apply_pricing_v2.py` intentionally clears plans under policy `commercial_hold.status=HOLD`. **Do not restore stale historical prices.**
- `build_catalog.py`, direct `build_home.py`, `build_seo.py`, and old `build_all.sh` contained price-dependent legacy paths. #66 `audit_all.py` has already removed the old unguarded bestseller minimum found on main.
- `status=live` and `bestseller_rank` preserve historical search/merchandising metadata; neither authorizes a payment or sale.

## Review-only patch
- Add read-only `catalog_hold_gate.py`: explicit HOLD-only plans; unique identifiers; consistent revision; no sale-price derived fields; fail-closed when policy changes.
- Enforce HOLD before public JS generation; add `sellability=inquiry_only` separate from the legacy product's `status`; remove old market/discount/cost fields.
- Replace legacy `build_catalog.py` with a wrapper around the approved public builder.
- Replace old `build_all.sh` with the governed `build_site.py` stage-only build.
- Add `catalog_hold_gate.py` as a canonical build step and synthetic regression coverage.
- **No editing**: catalog.json, price-policy, business roles, client data, payment destination, site domain or Cloudflare.

## Remaining #69 scope
1. The standalone direct `build_home.py` and `build_seo.py` still contain old unguarded price helpers; do not invoke them directly outside the new governed build. Independent unit-level HTML safety and direct entry-point suppression are further review tasks.
2. Run GitHub CI on this exact branch; locally reproduce canonical `build_site.py`, final `_site` audit, EN/BN offers, checkout, WhatsApp text, structured data, SEO continuity, and browser tests. No remote CI or production safety acceptance is asserted by this document.
3. Decide how to represent nonempty future **governed** plan records while keeping unrelated products HOLD. Requires CEO-approved exact SKU, provider authorization, current landed cost, contribution and terms; none are enabled by this patch.

## PR #75 dependency map
- This review branch is based on PR #66. PR #75 descends from #71 => #67 => #66 => #65; forward-port only after review/testing, no blind merge.
- #75's local 94 backend and 7 commerce tests are synthetic. No proof of live Cloudflare acceptance.
- The recorded empty Cloudflare staging resources `saveonsub-staff-staging` and `saveonsub-order-os` must be reverified in the owner account before reuse. Do not recreate.
- Subsequent owner-gated steps: verified staff identities, Cloudflare Access host/preview protection, migration backup and schemas in order (`ops/order-os/schema.sql`, `ops/commerce/001_catalog_content_foundation.sql`, `ops/order-os/business-schema.sql`), D1 bindings, MFA/role/PII/payment/rollback tests, synthetic cloud browser acceptance. R2 only if media is activated.
- WhatsApp/Meta, SOS GSC, live purchase attribution, staff notifications and real-money reconciliation are not verified operational.
- Staging deploy, Access change and D1 migration each require separate CEO authorization. Fixing #69 does not authorize any of them.
