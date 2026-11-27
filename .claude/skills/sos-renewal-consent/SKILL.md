---
name: sos-renewal-consent
description: Use before recommending or drafting any renewal or follow-up message. Requires recorded customer consent and a provider-verified expiry date; otherwise no outbound message is proposed.
---
# sos-renewal-consent
Procedure:
1. Check the private RENEWALS record for `Outreach_Consent` and `Provider_Expiry_At`.
2. Consent absent/unknown OR expiry unverified -> result `NO_OUTREACH`; list what must be collected first (not by contacting the customer unprompted).
3. Both present -> may prepare a DRAFT reminder (never auto-send), using the channel the customer consented to.
4. Renewal price must come from the current approved price (sos-product-truth), not from the previous order.
Missing consent or expiry may be collected only at the customer's next inbound contact or through an already-consented channel; NEXT_OWNER defaults to Ripon (customer operations) with Emon informed for pricing.
Output: `RENEWAL_ID | RESULT: NO_OUTREACH|DRAFT_OK | MISSING | NEXT_OWNER`.
