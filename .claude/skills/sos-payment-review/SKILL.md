---
name: sos-payment-review
description: Use when an order or customer claims payment was made. Checks whether receiving-side settlement evidence exists and keeps the order PAYMENT_REVIEW until the CEO-authorized verifier confirms. Never marks anything PAID.
---
# sos-payment-review
A screenshot, a transaction ID typed by the customer, or "I already paid" is a payment CLAIM, not proof.

Procedure:
1. Record state as `PAYMENT_REVIEW / UNVERIFIED` unless the private register already holds a receiving-side settlement reference entered by the authorized verifier.
2. Ripon and AI agents cannot set PAID. Only Emon (or a separately, provably delegated verifier) can.
3. Do not copy screenshots, wallet numbers, bank details or transaction IDs into GitHub, Slack or chat summaries. Use the SOS order ID only.
4. If payment is unverified, fulfillment is `BLOCKED`. Tell the customer, in plain Bangla, that verification is in progress; give no delivery time guarantee.
5. Flag duplicates (same reference on two orders) and amount mismatches to Emon.

Output: `ORDER_ID | STATE | EVIDENCE_PRESENT (yes/no, no details) | NEXT_OWNER | NEXT_ACTION`.
