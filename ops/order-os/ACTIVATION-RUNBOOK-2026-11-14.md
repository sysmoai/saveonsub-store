# Order OS + Ticket System — activation runbook (NON-PRODUCTION until every gate below is ticked)

Nothing here is deployed. No claim of production readiness is made. Each gate needs a
recorded result from the real service, not a FakeD1 run.

## 0. What exists in code (draft PRs)
Order OS (main) · #163 tickets API on existing `support_threads`/`support_events` · this PR:
assisted intake, assignment, escalation, categories, Bangla ticket page, staff ticket desk.
Tests are synthetic FakeD1 only: they prove logic, RBAC and privacy rules, not Cloudflare behaviour.

## 1. Migration order (one D1 database, apply once, in this order)
1. `schema.sql`  2. `lifecycle-finance-schema.sql`  3. `support-tickets-schema.sql`  4. `support-tickets-intake-schema.sql`
`ALTER TABLE ADD COLUMN` is not idempotent: never re-run 3 or 4. Staging first, on a NEW empty D1.
Production D1 is a separate, new, empty database with the same four files and the real staff rows only.
**Rollback:** the migrations are additive. Before applying to any D1, take `wrangler d1 export`
(Time Travel also works). To roll back, restore from that export/bookmark; do not hand-drop columns.
Never copy staging synthetic rows (e.g. SOS-SYNTH-0001) into production.

## 2. Gates (tick with evidence: date, who, link/log; no secrets)
- [ ] Staging D1 created, 4 migrations applied in order, `PRAGMA table_info(support_threads)` matches.
- [ ] Turnstile widget + `TURNSTILE_SECRET_KEY` set on the staging Pages project; real challenge passes, a failed token is refused.
- [ ] Cloudflare Access on the staff project with **MFA required** and an explicit allow-list; two named staff only.
- [ ] Ripon's ACTUAL role confirmed by login test: `support` cannot claim fulfilment or verify payment; `fulfillment` sees only own-assigned tickets. Role changes need CEO review. Ripon's consent is unconfirmed.
- [ ] Payment receiving configuration approved by the CEO from a verified source (see `CEO-CONFIRMED-PAYMENT-EVIDENCE-2026-11-11.md`). This repo never changes the number.
- [ ] Edge rate limits (below) live and tested from outside.
- [ ] CORS origin list = storefront origins only.
- [ ] `assets/order-config.js` `apiBase` set only after all of the above; page stays noindex until the CEO decides otherwise.

## 3. Edge rate-limit rules to configure in Cloudflare (code cannot enforce these)
| Path | Method | Rule |
|---|---|---|
| `/api/support/tickets/status` | GET, POST | 10 req / 60 s per IP, then 10 min block (anti token-guessing) |
| `/api/support/tickets` | POST | 5 req / 10 min per IP (Turnstile also required) |
| `/api/orders/track` | any | existing rule, same style |
| `/api/ops/*` | any | Access-gated; 120 req / min per IP as a backstop |
Anti-enumeration already in code: identical 404 for unknown id, wrong code and other customer's code;
ids are random 12 chars; codes are 244-bit; only hashes stored; per-order open-ticket cap of 5.

## 4. Customers without a tracking code (manual / WhatsApp orders)
Support/manager/owner uses the staff desk (`/tickets.html`): verifies ownership out of band
(order WhatsApp number match, payment reference last 4, or details only the buyer knows), links the
EXISTING order id (unknown ids are refused, nothing is created), and relays the one-time access code
on the same channel. No order is fabricated and no customer without a record is linked to anyone.
Lost code: staff verify again and rotate; the old code stops working.

## 5. Customer-data handling
Public repo: no customer data, supplier/cost data or credentials committed. Messages are stored
redacted (credentials, emails, links, long numbers). Customer name/phone/email are shown to staff by role only.
`support_events` are append-only; closed tickets are immutable. Retention period and deletion
requests are a CEO/legal decision, not yet defined. Staff never ask customers for passwords/OTPs.

## 6. Measurement (no profit claim without source records)
Compute only from records that exist; show "no data" otherwise.
- Verified-paid orders: orders with a `payment_verifications` row whose `receipt_source` is the receiving-account history. Screenshots/TxnIDs alone count as 0.
- Renewals: a second verified-paid order for the same plan by the same customer within the covered period.
- Actual supplier cost: entered per order by the owner from the real invoice; margin is reported only for orders that have both a verified payment and a recorded cost. Today: none recorded, so no margin is reported.
