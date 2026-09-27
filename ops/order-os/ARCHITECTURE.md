# SaveOnSub Order OS v1

Status: implementation branch only. Production activation is blocked until D1, staff auth, notification delivery and canonical-domain smoke tests are verified.

## Objective

Turn SaveOnSub checkout from a browser-local WhatsApp handoff into a durable order operating system:

customer checkout
-> server validates governed catalog price/access truth
-> durable order created
-> priority staff notification queued
-> human verifies payment
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
P1: new order awaiting payment review, customer reply requiring human action
P2: support request, renewal due, stock risk
P3: lead/newsletter/general question

Human operators should receive P0/P1 first.

## Reliability rules

- Client prices are never authoritative.
- Every public order create request requires an idempotency key.
- An order is not shown as accepted until the server confirms persistence.
- Notification sending uses an outbox so an external webhook failure never loses the order.
- Notification retries are bounded and logged.
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
