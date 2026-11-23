# sos-product-truth scenarios (synthetic fixtures only; no real provider rights evidence)
Run each with the skill loaded; expected result must match. Observed on 2026-11-23 (headless `claude -p`, simulated inputs).

| # | Input (synthetic) | Expected | Observed |
|---|---|---|---|
| N1 | fresh facts, price approved, Rights_Source empty | HOLD | HOLD |
| N2 | Access_Type = shared consumer login (provider forbids sharing), rest valid | HOLD | HOLD |
| N3 | Valid_Until expired | HOLD | HOLD |
| N4 | Approval_ID and Approved_By empty | HOLD | HOLD |
| N5 | no confirmed fulfillment route | HOLD | HOLD |
| N6 | fresh facts + price, provider authorization missing | HOLD | HOLD (same as N1) |
| N7 | facts verified_on older than 14 days | INQUIRY_ONLY | INQUIRY_ONLY |
| P1 | all fields valid, fulfillment confirmed (DEMO ids) | SELLABLE | SELLABLE |

Limits: prose-skill behaviour tests, not proof of real provider authorization or production SELLABLE path. The 14-day rule matches CI provider_fact_freshness.py (fail >14d); unchanged.
