---
name: sos-product-truth
description: Use before quoting, describing or publishing any SaveOnSub provider plan, price, eligibility or access model. Validates exact tier, official source date, Bangladesh eligibility, CEO price approval, provider/supplier authorization and fulfillment readiness; returns SELLABLE, INQUIRY_ONLY or HOLD.
---
# sos-product-truth
Purpose: stop unsupported product claims. This skill never approves a price or a rights arrangement; only the CEO does.
A fresh fact file plus an approved price is NECESSARY but NEVER SUFFICIENT for SELLABLE.

Inputs: provider, exact plan/tier, access model (personal seat / team seat / shared consumer login), the question being answered.

Procedure:
1. Find the provider's `ops/*COHORT-FACTS*.json`. Read `verified_on`, `verification_log[-1].not_reverified` and the plan fields.
2. Read the last `verification_log` entry's not-reverified list (key spelling varies: `not_reverified`, `NOT_reverified`, or a `*_findings`/`confidence` note; if no such field exists, treat every claim as unverified). If the needed claim is listed there, or `verified_on` is older than 14 days, result is `INQUIRY_ONLY`: say it must be re-verified; do not state the number as current.
3. Shared consumer credentials, or any plan whose provider terms forbid sharing, are `HOLD`. Never describe them as sellable.
4. A CEO-approved SaveOnSub price must exist in the pricebook/catalog (`catalog_reconcile.py` is the check). No approved price -> `HOLD` for quoting.
5. Authorization and readiness (all required, checked in the PRIVATE register, never copied into the public repo): the matching APPROVED_OFFERS row must have `Rights_Source` (provider/supplier authorization for this exact tier and for resale in Bangladesh), `Access_Type` that is a provider-permitted arrangement, `Approval_ID` + `Approved_By`, `Valid_Until` not expired and `Status` active, and a named, currently available fulfillment route (Ripon/Emon confirm it can actually be delivered now). Any item missing, expired or unconfirmed -> `HOLD`; never SELLABLE.
6. Never promise availability, speed, refunds or "official reseller" status.

Output (Bangla, short): `RESULT: SELLABLE|INQUIRY_ONLY|HOLD`, the evidence file+field, the source URL and date, and the single missing item if not SELLABLE. SELLABLE additionally lists: price approval ref, rights source ref, access type, fulfillment route (IDs only, no costs or supplier names).
A third-party or SERP snapshot (e.g. `bd_serp_snapshot`, `saveonsub_offer_snapshot`) is never an approved price.
Escalate to Emon for any price, new SKU or rights question.
