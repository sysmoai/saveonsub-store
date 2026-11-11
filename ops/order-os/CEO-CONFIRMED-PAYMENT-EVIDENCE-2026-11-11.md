# SaveOnSub — Founder-Confirmed Payment & Renewal Evidence SOP

**Fact date:** 2026-11-11 (Asia/Dhaka)  
**Status:** DRAFT / CODE-AND-PROCEDURE ONLY; not deployed, not a new approval of a payment rail or subscription access model.  
**Business boundary:** SaveOnSub only. No cross-unit customers, accounts, evidence, prices or entitlements.

## 1. New founder-confirmed operating fact

EMON confirmed on 2026-11-11 that, for customer payments through bKash, Nagad, Rocket or bank transfer:

1. The customer sends a payment screenshot in the customer conversation.
2. The screenshot remains in that conversation as historical context. The founder uses past conversations for customer support, renewal follow-up and checking the subscription's history.
3. EMON **independently opens the RECEIVING wallet app's transaction history or the receiving bank's history** to verify that money actually arrived.

The founder did **not** state that screenshots verify settlement, that messages contain a trustworthy service-expiry date, that a wallet API is connected, or that every conversation is already linked to a durable order ID. Do not infer any of those facts.

## 2. Two evidence classes must never be conflated

| Evidence class | Source | Permitted use | Not permitted |
|---|---|---|---|
| Customer claim | Screenshot, message, submitted transaction reference | Triage, identify candidate payment, disagreement support, customer history | Mark paid; trigger paid alert; authorize fulfillment; invent service dates |
| Receiving-side settlement evidence | Independently viewed incoming credit in bKash/Nagad/Rocket receiving history, or receiving bank statement, attested by authorized human | Verify incoming funds against order; record immutable proof reference; unlock paid workflow | Scrape personal wallet, forward SMS/OTP to an AI, treat arbitrary screenshot as recipient evidence |
| Provider-confirmed service information | Authorized activation/plan information and actual service start/end date | Record subscription period, handle support and eligibility for opted-in renewal | Infer expiry solely from payment date or payer screenshot |

A customer screenshot can remain in the original customer conversation. It is not automatically a payment-verification evidence reference. If a customer-claim pointer is later captured in CRM, store a **minimal, access-controlled internal locator and claim-received timestamp** only, without public message URLs, card/account information, screenshots, password, MFA code, or entire chat. Do not copy the screenshot to GitHub, public site, unrestricted Google Sheets or agent prompts.

## 3. Human verification checklist (manual until an authorized payment integration exists)

1. Resolve the **SaveOnSub order** and approved SKU/plan, price, customer channel and customer-submitted payment claim. Missing order? Keep it as a lead/payment claim pending an authorized reconciliation process; do not fabricate an order.
2. Identify which of the four permitted receiving channels was selected. Customer screenshot/transaction ID is a *search hint only*.
3. EMON signs in to the receiving wallet/bank independently; inspects its own **incoming** credit/history, not only payer screenshot. Match channel, amount in BDT, receipt/ref details and transaction uniqueness to one specific order. If recipient/provider history and payer claim differ, investigate; never force a match.
4. If not yet visible, amount differs, another order already uses that transaction, the account is wrong, or there is a dispute: **stay payment_review**. Log a minimal private exception and do not release subscription access.
5. When a qualifying incoming credit is seen, the authorized owner uses the existing private payment-verification API: provider, recipient-side reference, **exact incoming amount**, currency, appropriate `receipt_source`, `receipt_confirmed=true` and a private `stmt:` / `r2:sos/private/` recipient-side settlement evidence reference. This is a human attestation, not an independent wallet API settlement event.
6. The Order OS checks owner access, expected amount/currency, rail consistency, duplicate recipient-side reference and pending state; it writes `payment_verifications`, `order_events`, `payment_confirmed`, and one sanitized paid alert in an atomic batch.
7. Fulfillment uses a **provider-permitted mechanism** only. The staff member records delivery and independently verified start/end dates where possible. The customer-claim screenshot remains background evidence rather than expiry proof.
8. Renewals require an actual verified service end date and channel-specific contact consent. If expiry is unknown, mark **expiry unknown**, avoid asserted dates and automated renewal reminders. Support must be accessible even when the customer did not grant marketing consent.

**No screenshot, screenshot URL, typed transaction reference or incoming-message OCR should set `payment_confirmed` automatically.** Do not ask customers for password, OTP, card number or account login through the AI workflow.

## 4. Existing implementation — verified in GitHub source, not live

- `functions/api/ops/orders/[orderId]/payment-verification.ts` already requires a permitted provider, receipt attestation, receiving-side `receipt_source`, private evidence reference, exact amount/currency, privileged role and rejects duplicate verification references.
- `tests/order-os/personal-payment-first.test.mjs` already tests human attestation and P0 alert generation. This change adds explicit regression cases for screenshot/external URL substitutions.
- `orders.payment_reference` can contain the **customer-submitted reference** in plaintext in the internal database. This is a claim (not the independently verified provider reference); review data minimization, RBAC, display/redaction and retention separately before broad imports.
- `payment_verifications` stores a hash of the receiving-side reference and last four characters; raw receiving-side IDs should remain in authorized provider records.
- `functions/api/ops/orders/[orderId]/service-period.ts` accepts service start/end dates in an authorized delivered state but does **not currently require provider evidence/provenance** for those dates. This is a **known gap**, not a verified renewal fact. Plan an additive provenance mechanism and negative tests before automated expiry claims.
- The current private staff UI has a separate owner receipt-attestation form. Receipt confirmation should **not** read screenshot-derived facts as settled evidence.
- `assets/order-config.js` in main has `serverCheckoutEnabled:false`; no live server checkout or automatic wallet integration is claimed.

## 5. Evidence-safe minimal order reconciliation (first sample, CEO-owned)

For the first 5–10 *real* orders, EMON may privately assemble a minimal reconciliation worksheet once privacy/record-import approval is explicit. Recommended fields:

`local_reconciliation_id`, `order_id_if_exists`, `customer_alias` (minimal), `channel`, `approved_plan_id`, `quoted_bdt`, `claim_received_at`, `claim_present_in_conversation` (yes/no), `incoming_credit_seen` (yes/no), `verified_bdt`, `receiving_provider_reference_last4`, `owner_verification_date`, `private_settlement_evidence_ref`, `fulfillment_status`, `provider_verified_start`, `provider_verified_end`, `renewal_consent_status`, `landed_cost_bdt`, `support_issue`.

Do not bulk copy chat exports, contact lists, screenshots or payment account histories. Link an existing authoritative Order OS record rather than making another independent CRM/finance SSOT. Real customer data stays in access-controlled SaveOnSub systems.

## 6. Failure modes and QA

| Scenario | Required outcome |
|---|---|
| Screenshot received but no recipient-side credit verified | Pending payment_review, no P0 paid alert |
| Customer claim matches an ID but owner attestation absent | 400, no paid status |
| Attestation claims `customer_screenshot` as receipt source | 400, no paid status |
| Evidence_ref is a screenshot file or external chat/image URL | 400, no paid status or alert |
| Valid receipt with wrong order amount or wrong rail | 409, manual reconciliation |
| Same recipient-side reference used twice | Second attempt rejected |
| Owner sees real credit and records allowable recipient evidence | Payment confirmed, exactly one P0 alert queued (not necessarily delivered) |
| Valid paid order but unknown provider expiry | Do not send an asserted-date renewal reminder |
| No consent to renewal marketing | Do not send automated promotional renewal messages |
| No R2/merchant statement locator available | **HOLD verification** in the current API; do not fabricate a `stmt:` reference merely to bypass the guard |

## 7. Safety and release gates

- **READ-ONLY / DOCS / SYNTHETIC TESTS ONLY** in this draft PR. No Cloudflare config, D1 migrations, real customer-data import, webhook activation, role change, order status update, price change, campaign launch, message send, merge or production deployment.
- Current checks are **source review**; live staff RBAC, D1 binding, receipt storage access, notification delivery, provider permission, restoration, canonical release SHA and WhatsApp consent remain separately blocked until independently verified.
- Do not use personal P2P payment collection for commercial purposes as implicitly provider-authorized. Check current provider terms and applicable payment rules before scaling.
- Reassess privacy retention and customer-request handling with a documented policy. No arbitrary automatic data deletion or indefinite retention promises.
- PR #123 separately proposes sending the first paid alert to EMON pending Ripon's feedback. Keep this SOP isolated; no assumption that the alert routing change is merged or deployed.

## 8. Decisions not silently made

1. Should SaveOnSub eventually preserve an access-controlled conversation locator in Order OS, and what is the verified consent/retention rule?
2. How should provider-backed subscription expiry provenance be recorded before automatic renewal workflows?
3. What is the approved process for a real payer who used a different rail, split payment or invalid claimed reference?
4. Are current personal receiving rails contractually permissible for the business's actual sales model?

**Next execution gate:** owner reviews this SOP and a synthetic order-to-payment-to-delivery test; reconcile 5–10 real orders only after a scoped customer-data privacy/import approval. Preserve checkout OFF until staged end-to-end evidence is established.
