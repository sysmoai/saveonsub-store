# SaveOnSub Order OS v1

Status: implementation branch only. Production activation is blocked until D1, staff auth, notification delivery and canonical-domain smoke tests are verified.

## Objective

Turn SaveOnSub checkout from a browser-local WhatsApp handoff into a durable order operating system:

customer checkout
-> server validates governed catalog price/access truth
-> durable order created
-> unpaid order stored without staff interruption
-> owner confirms received funds against recipient account history / bank statement
-> unique P0 paid-order notification queued atomically with verified payment
-> existing SOS notification Worker informs Ripon and escalates unclaimed payment to EMON
-> human claims fulfillment
-> delivery evidence/status recorded
-> customer can track with a private tracking token
-> support/renewal events stay attached to the same order/customer record
-> every state change is auditable.

## Architecture

Static storefront: Cloudflare Pages (existing canonical host)
Dynamic API: Cloudflare Pages Functions
Operational DB: dedicated SaveOnSub Cloudflare D1 database
Staff UI: protected /ops surface, never public
Anti-abuse: Cloudflare Turnstile on public write endpoints
Notifications: transactional outbox with pluggable delivery adapter
Analytics: privacy-safe order funnel events; no secrets in analytics
AI agents: read/triage/draft/improve; no autonomous payment approval, refunds, credential delivery or destructive actions.

## Order states

draft
submitted
payment_review
payment_confirmed
assigned
fulfilling
delivered
support_open
completed
cancelled
refunded

State changes are append-only in order_events. orders.status is the current projection.

## Priority model

P0: paid/confirmed customer waiting, delivery failure, duplicate payment, security issue
P1: urgent customer reply requiring human action (not routine inquiry or unpaid claim)
P2: support request, renewal due, stock risk
P3: unpaid order, lead/newsletter/general question

Human operators should receive P0/P1 first.

## Reliability rules

- Client prices are never authoritative.
- Every public order create request requires an idempotency key.
- An order is not shown as accepted until the server confirms persistence.
- Notification sending uses an outbox so an external webhook failure never loses the order.
- Notification retries are bounded and logged. Only payment-confirmed orders enqueue paid-order alerts; an unclaimed paid order escalates to EMON after a configured delay.
- Payment confirmation and delivery remain human-controlled.
- Customer tracking uses a random token, not sequential IDs alone.
- No passwords, OTPs, subscription credentials, card data or secret keys are stored in order records.
- Every mutation creates an order_event.
- Staff actions require authenticated operator identity before production activation.

## Lowest-cost deployment strategy

Reuse the existing Cloudflare Pages project. Add D1 and Pages Functions instead of a VPS or a new paid application server. Keep the storefront static so organic traffic does not increase application compute cost linearly.

## AI agent boundaries

Allowed:
- categorize/triage orders and support
- draft replies
- flag SLA risk
- recommend next action
- prepare fulfillment checklist
- generate SEO/content opportunities from aggregate, non-sensitive signals
- run site audits and draft PRs

Human approval required:
- mark payment confirmed
- send account credentials or sensitive access
- refund/discount outside policy
- approve replacement where policy is ambiguous
- change pricing
- modify payment destination
- DNS/domain/security changes
- production promotion while P0 gaps remain

## Staff security model (2026-10-23 hardening)

Source of truth: `functions/lib/order-os/order-workflow.ts` (rules), `redaction.ts` (PII), `ops/order-os/schema.sql`
(storage-level triggers). Behaviour is proven by `tests/order-os/*.test.mjs`, run in the required CI gate.

### Order state machine (server-enforced)

| From | To (ordinary) |
|---|---|
| submitted | payment_review, cancelled |
| payment_review | payment_confirmed (**only** via payment verification), cancelled |
| payment_confirmed | assigned (**only** via claim), refunded |
| assigned | fulfilling, refunded |
| fulfilling | delivered, refunded |
| delivered | completed, support_open, refunded |
| support_open | completed, fulfilling, refunded |
| completed | support_open, refunded |
| cancelled, refunded | none (terminal) |

Three layers: the pure rule table; compare-and-set SQL (`WHERE status = <validated state>`, with the audit event
inserted under the same guard in the same batch, so a lost race writes nothing); and SQLite triggers that make
terminal states immutable and forbid any paid-or-later state without an active matching payment verification.

### Roles

| Capability | owner | manager | fulfillment | support | viewer |
|---|---|---|---|---|---|
| Verify payment | yes | only if `PAYMENT_VERIFIER_ROLES` includes `manager` | no | no | no |
| Cancel / refund | yes | yes | no | no | no |
| Claim order | yes | yes | yes | no | no |
| Fulfil (fulfilling/delivered/completed) | yes | yes | own claimed orders | no | no |
| Open/close support case | yes | yes | delivered->support_open | yes | no |
| Reverse a cancelled/refunded order | **yes** | no | no | no | no |
| See customer phone | yes | yes | no | related orders only | no |
| See customer email / name | yes | yes | yes | related orders only (else masked) | no |
| See event notes and actor ids | yes | yes | no | no | no |

"Related" for support = delivered / support_open / completed, or assigned to that operator. Nobody can change a
price or discount through any ops endpoint (no endpoint accepts price fields).
Ripon is assumed to hold the `support` role. The role record is not in the repository; confirm in D1.

### Payment provenance

`POST /api/ops/orders/:id/payment-verification` (owner = CEO only by default; `PAYMENT_VERIFIER_ROLES="owner,manager"` is the only
widening). A customer-submitted reference is a claim, never proof. A required `evidence_ref` cites settlement evidence
(`r2:sos/private/...` object or `stmt:...` merchant-statement id); a screenshot or any URL is refused.
The verifier supplies provider, the provider reference, the exact amount actually received, receipt_confirmed=true and a receipt_source (receiving_account_history for bKash/Nagad/Rocket, bank_statement for bank_transfer). This is an accountable human attestation, not automated financial confirmation. The amount and
currency must equal the order total (the expected total is not revealed on mismatch). Stored: provider, SHA-256 of
`provider:reference`, last four characters, amount, currency, evidence_ref, verifier, time. Not stored: the full reference.
A partial unique index rejects the same reference on a second order and a second active verification on one order.

### Terminal-state reversal

`POST /api/ops/orders/:id/reversal` (owner only, written reason 20-500 chars). Moves a cancelled/refunded order to
`payment_review` only, voids the earlier payment verification, and writes a `terminal_reversal` event. Money must be
verified again before fulfilment can restart.

### Errors

Clients receive stable codes only (`UNAUTHENTICATED`, `FORBIDDEN`, `STAFF_BACKEND_NOT_CONFIGURED`, `STALE_STATE`, ...).
Token, JWKS and database error text is logged server-side and never returned.

## Access JWT and deployment boundary (SOS-T018)

- `TEAM_DOMAIN` must match `^https://[a-z0-9-]+\.cloudflareaccess\.com$`, otherwise every staff request is 503.
- The token `type` claim must be exactly `app`; a missing `type` is 401.
- `operators.last_seen_at` is written at most once per operator per 5 minutes (SQL-side throttle).
- The staff API deploys only to its own Pages project (`wrangler.order-os.toml`, `saveonsub-staff-staging`). The storefront
  workflow deploys from inside `_site/`, so `./functions` is never bundled into project `saveonsub`. Both are enforced by
  `audit_order_os.py`. A Cloudflare dry run is still an owner action.

## Personal Send Money channels — staged 2026-10-28

The user-confirmed current incoming channels are personal bKash, Nagad, Rocket and bank transfer. Neither a customer screenshot nor the customer-entered reference can confirm receipt. No personal-account scraping, forwarding private SMS, screen automation, password or OTP collection is authorized. Production order acceptance remains blocked while SKU permission and governed plan selection are HOLD.

The checkout creates a passive P3 payment_review order; it sends no urgent operator webhook. The owner-only payment-verification endpoint checks exact amount/currency, duplicate provider reference, staff identity, private evidence reference and receipt-source attestation, then atomically updates status to payment_confirmed/P0, records the audit event and queues one sanitized paid_order_priority alert. This backend does not call any wallet API or check balances automatically.

The pre-existing scheduled Worker at workers/order-notifications uses the paid-only dispatch module workers/sos-paid-alerts.mjs. It sends only minimal order ID/amount/provider, skips delivery when a secret webhook is absent, retries failed messages, and creates an owner escalation after the configured interval if status is still payment_confirmed/unclaimed. Delivery is at least once; downstream services should deduplicate by stable delivery_key. No public site, DNS, account destination or live Cloudflare deployment is changed by this branch. See PERSONAL-PAYMENT-RAILS-2026-10-28.md for operator checklist and acceptance gates.
