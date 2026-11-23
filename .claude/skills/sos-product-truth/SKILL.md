---
name: sos-product-truth
description: Use before quoting, describing or publishing any SaveOnSub provider plan, price, eligibility or access model. Validates exact tier, official source date, Bangladesh eligibility and CEO price approval; returns SELLABLE, INQUIRY_ONLY or HOLD.
---
# sos-product-truth
Purpose: stop unsupported product claims. This skill never approves a price; only the CEO does.

Inputs: provider, exact plan/tier, access model (personal seat / team seat / shared consumer login), the question being answered.

Procedure:
1. Find the provider's `ops/*COHORT-FACTS*.json`. Read `verified_on`, `verification_log[-1].not_reverified` and the plan fields.
2. If the needed claim is listed in `not_reverified`, or `verified_on` is older than 14 days, result is `INQUIRY_ONLY`: say it must be re-verified; do not state the number as current.
3. Shared consumer credentials, or any plan whose provider terms forbid sharing, are `HOLD`. Never describe them as sellable.
4. A CEO-approved SaveOnSub price must exist in the pricebook/catalog (`catalog_reconcile.py` is the check). No approved price -> `HOLD` for quoting.
5. Never promise availability, speed, refunds or "official reseller" status.

Output (Bangla, short): `RESULT: SELLABLE|INQUIRY_ONLY|HOLD`, the evidence file+field, the source URL and date, and the single missing item if not SELLABLE.
Escalate to Emon for any price, new SKU or rights question.
