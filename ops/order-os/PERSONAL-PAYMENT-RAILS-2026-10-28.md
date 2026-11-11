# SaveOnSub — Personal Payment Rails & Paid-Order Notification SOP
**Date:** 2026-10-28 (Asia/Dhaka)  
**Status:** STAGING CODE / NOT DEPLOYED / CEO PRODUCTION GATE REQUIRED  
**Business boundary:** SaveOnSub only. No other business, wallet, customer, ledger, token or webhook may be reused.

## Verified founder input
All current receiving accounts are **Personal / Send Money**, across four supported channels: bKash, Nagad, Rocket and bank transfer. No authenticated provider-approved read API, merchant settlement webhook or bank feed has been demonstrated for these accounts. Do not assume one exists, scrape personal SMS/apps, copy OTPs/passwords, or infer credit from a payer screenshot.

## Roles and event meaning
- **Customer:** sees approved SKU, exact price, access terms and honest delivery window; submits an order and may provide a transaction claim. This creates `payment_review`, **not PAID**.
- **AI sales assistant:** answers verified FAQs, validates contact/claim format and follows up politely. It may not assert receipt or release access.
- **EMON (owner payment verifier by default):** accesses the RECEIVING wallet's actual transaction history or bank statement privately; checks account destination, provider, incoming amount, currency, transaction uniqueness, receipt time and order match. If anything is missing or disputed, leave pending and investigate.
- **Ripon (fulfillment):** is notified after verification and claims/delivers within his approved operator role. He does not independently mark funds received or change prices/account destinations.
- **EMON fallback:** an unclaimed confirmed order is escalated to the owner after `SOS_PAID_ESCALATION_MINUTES` (default **15**, proposed operational parameter, not a customer promise). Critical security/customer-harm incidents may alert human even without payment.

## Four receiving rails
| Rail | Customer-side claim | Independent evidence for authorized verifier |
|---|---|---|
| bKash personal | Reference + order ID | Actual incoming transaction in recipient bKash account history |
| Nagad personal | Reference + order ID | Actual incoming transaction in recipient Nagad account history |
| Rocket personal | Reference + order ID | Actual incoming transaction in recipient Rocket account history |
| Bank transfer (personal) | Reference + order ID | Actual credited entry in receiving bank account/statement |

A screenshot, forwarded message, unverified SMS, customer transaction ID, or browser-side amount is insufficient. If a payer uses a different channel than selected, do not guess; reconcile it manually and record the discrepancy privately.

## Staging API and durable transaction model
1. Public `POST /api/orders` accepts only four normalized channel identifiers: `bkash`, `nagad`, `rocket`, `bank_transfer`. It creates an unpaid P3 order; sends **zero** immediate priority messages.
2. Authorized `POST /api/ops/orders/:id/payment-verification` requires `provider`, `transaction_id`, `amount_bdt`, `currency=BDT`, `evidence_ref`, `receipt_confirmed=true` and `receipt_source`.
3. Valid receipt sources: `receiving_account_history` for bKash/Nagad/Rocket; `bank_statement` for bank transfer. This is a **human attestation**, not independently automated settlement confirmation.
4. `evidence_ref` must identify a private statement/transaction-history record using `stmt:` or `r2:sos/private/`. Never put whole statements in public GitHub or webhook payloads; never accept a public screenshot URL as financial proof.
5. The backend verifies server-side exact order amount and currency; unique active provider reference; authenticated verifier; pending order state. It atomically records the verification/event, sets P0 `payment_confirmed` and queues `paid_order_priority`.
6. The **existing** `workers/order-notifications` Cloudflare Scheduled Worker uses the new paid-only dispatcher, which reads only active verified paid orders and sends restricted metadata, never customer PII or full transaction references.
7. If Ripon has not claimed the paid order by the configured threshold, the dispatcher queues `paid_order_unclaimed` for EMON. A claimed order does not escalate. A cancelled/refunded order's unsent alert is suppressed. Outbox state is `pending`, `sending`, `sent`, `failed` or `dead` (never misrepresent queued as sent).
8. External notification is **at-least-once**; receiver should deduplicate by `delivery_key`. Retries are bounded; unconfigured destinations leave events pending. An alert **does not** imply that a notification has arrived on a device.

## Required private configuration (none set by this branch)
- Dedicated **SaveOnSub staging D1** with exact compatible schema; only SOS project bindings.
- Private Access-authenticated staff UI and correct operator identities/roles, MFA and auditing.
- `SOS_RIPON_ALERT_WEBHOOK` = scoped, verified SOS-only Ripon notification destination.
- `SOS_EMON_ALERT_WEBHOOK` = scoped, verified SOS-only CEO fallback destination.
- Optional `SOS_PAID_ESCALATION_MINUTES`; default 15, tunable 5–120 minutes after owner agrees actual staffing coverage.
- A working Cloudflare Scheduled Worker using existing `workers/order-notifications/wrangler.toml`. No second Worker required.
- Approved compliant sellable SKUs, provider rights, current prices, truthful SLAs, stock/fulfillment and customer refund policy. Catalog and CI blocker #69 must be solved first.

## Synthetic release tests
- Unpaid claim/screenshot/reference creates no paid status or human urgency.
- Missing/bad human receipt attestation → rejected; bank/MFS source mismatch → rejected.
- Wrong amount/currency, reused provider transaction ID, repeat verification, wrong role → rejected.
- Correct incoming receipt → one atomic P0 outbox message, no PII/reference in outbound payload.
- Notification worker retry/duplicate/timeout and no-webhook behaviour, CEO unclaimed escalation, claimed exclusion and refund suppression.
- Original #65/#66/#67 security tests, source-vs-live SHA, protected staging browser, rollback, privacy consent and independent QA all pass.

## Commercial and compliance gate
Personal P2P vs authorized P2B collection must be reviewed against each provider's current terms and Bangladesh requirements; using a personal account is not evidence of commercial authorization. bKash offers separate Merchant/Online Business and Personal Retail Account paths that may be investigated, but do **not** create or upgrade an account, change website payment details or buy any service without CEO review. Marketing/SEO/ads must not promote blocked SKUs.

**Release status:** Code in a stacked GitHub draft PR only. No live money movement, production account modification, customer data ingestion, deployment or live alert registration.

## Staged protected human interface

The implementation branch adds `staff-ui/orders.html` and `staff-ui/orders.js`, linked from the existing private catalog screen. The form makes an owner explicitly check an actual received credit, enter the channel, receiving-account reference, exact incoming amount and a private `evidence_ref`, and check an attestation checkbox before the payment API is called. The UI never treats a browser-side claim as proof, never caches secrets in localStorage and displays the status as queued, not delivered. Paid-order claim / start fulfillment / mark delivered buttons call the existing server-enforced staff endpoints. The new form is a staged browser feature only: no live authentication, accounts or production deploy established yet.

### Blocking Ripon role compatibility

The preexisting `functions/lib/order-os/order-workflow.ts` only permits `owner`, `manager` and `fulfillment` to claim an order. The legacy architecture document assumes Ripon may be a `support` user, which can **not** claim or mark orders delivered. The actual D1 operator record has not been authenticated. Before live use, verify Ripon's own MFA login and real role, then have EMON approve the narrow role assignment that meets fulfillment duties. Do not silently widen support permissions, let agents impersonate owner, or alter Cloudflare Access roles without approval.

### Provider selection mismatch

The payment-verification endpoint now rejects a provider that differs from the channel recorded on the order. If a customer used a different personal wallet or bank than selected, hold the original order for manual reconciliation and correct it only through an auditable owner-approved workflow; do not misclassify the incoming money or reuse a reference across orders.

### Alert race and CI

An unclaimed escalation waiting in the outbox is suppressed if Ripon claims before dispatch; this race scenario is included in local worker tests and the CI-targeted test file. Local Worker simulated SQLite tests passed (6/6); full stacked repository CI, Cloudflare staging tests, and real mobile delivery are still unverified. The alert delivery contract is at-least-once, not exactly-once.
