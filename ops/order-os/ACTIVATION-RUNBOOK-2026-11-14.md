# Order OS + Ticket System — activation runbook (NON-PRODUCTION until every gate below is ticked)

A Cloudflare deployment now exists in the SEPARATE staff **staging Pages project**.
This does NOT mean that the customer-facing storefront, support API or private
Order OS is production-ready. The deployment ID, observed protected UI, missing
CORS fix and unverified gates are recorded in
`ops/order-os/STAGING-EVIDENCE-2026-11-14.md`.
Each acceptance gate still requires evidence from the real service, not FakeD1.

## 0. What exists in code (draft PRs)
Order OS (main) · #163 tickets API on existing `support_threads`/`support_events` · this PR:
assisted intake, assignment, escalation, categories, Bangla ticket page, staff ticket desk.
GitHub CI tests use synthetic FakeD1 and confirm logic/RBAC invariants only. Separately,
the CEO reports a live Cloudflare staging synthetic ticket lifecycle pass under the
owner Access login (HTTP 400/404/200/409, reason-required escalation, code rotation,
unknown assignee denial, closed-ticket immutability); raw redacted HTTP logs and
deployment source-SHA parity were not supplied for independent sign-off.
See `STAGING-EVIDENCE-2026-11-14.md`. The CEO's authenticated test does NOT prove
public customer API availability, Ripon login role denial, Turnstile or rate limits.

## 1. Complete fresh-staging D1 migration order (one database; check existing state first)
For a **new empty full Business OS D1**, apply the six tracked files in order:
1. `ops/order-os/schema.sql` (operators, orders, support base)
2. `ops/commerce/001_catalog_content_foundation.sql` (catalog foundation)
3. `ops/order-os/business-schema.sql` (private business records)
4. `ops/order-os/lifecycle-finance-schema.sql` (order costs, refunds, periods)
5. `ops/order-os/support-tickets-schema.sql` (ticket IDs, secrets, history rules)
6. `ops/order-os/support-tickets-intake-schema.sql` (assisted intake, ownership verification, categories)

This reconciles `ACCESS-SETUP.md`'s four base migrations with the two ticket
extensions. **Do not assume the deployed staging D1 is empty.** Read its actual
table/index/trigger inventory and migration history first; apply only missing
approved migrations, after a backup. The ticket `ALTER TABLE ADD COLUMN`
statements in steps 5 and 6 are **not idempotent**: never replay them. The
synthetic six-file regression test is
`tests/order-os/staging-migrations.test.mjs`; it is not a substitute for
the real D1 inventory. Production D1 remains a separately authorized environment.
**Rollback:** the migrations are additive. Before applying to any D1, take `wrangler d1 export`
(Time Travel also works). To roll back, restore from that export/bookmark; do not hand-drop columns.
Never copy staging synthetic rows (e.g. SOS-SYNTH-0001) into production.

## 2. Gates (tick with evidence: date, who, link/log; no secrets)
- [x] **CEO-REPORTED (not independently reproduced):** real Cloudflare staging / owner-Access synthetic ticket lifecycle gave 400 wrong input, 404 unknown/missing/wrong ticket code with no known write, 200 valid status, escalation reason check, code rotation, 404 unknown assignee, 409 immutable closed ticket. Closed synthetic test ticket retained in staging D1; no customer data.
- [ ] Attach sanitized HTTP status, D1 audit/row-count proof and exact deployed commit/deployment ID for the above. Keep raw access codes, Access JWTs and secrets out of reports.
- [ ] Read-only confirm which D1 the staging Pages project actually binds; inventory all six schema stages, verify support columns, integrity, foreign keys and trigger state; backup before any approved migration. Do not claim new empty D1.
- [ ] Turnstile widget + `TURNSTILE_SECRET_KEY` set on the staging Pages project; real challenge passes, a failed token is refused.
- [ ] Staff URLs (including deployment previews) require login from unauthenticated contexts, as observed 14 Nov. Independently verify actual Cloudflare Access applications, two-user allow-list, MFA and path-scoped customer API policies; external probes alone cannot prove them.
- [ ] Ripon's ACTUAL role confirmed by login test: `support` cannot claim fulfilment or verify payment; `fulfillment` sees only own-assigned tickets. Role changes need CEO review. Ripon's consent is unconfirmed.
- [ ] Payment receiving configuration approved by the CEO from a verified source (see `CEO-CONFIRMED-PAYMENT-EVIDENCE-2026-11-11.md`). This repo never changes the number.
- [ ] Edge rate limits (below) live and tested on the **actual API hostname**, including observed 429. Cloudflare zone WAF rules on a proxied custom domain cannot be assumed to protect the `*.pages.dev` staging hostname; verify supported route/plan, without making DNS changes.
- [ ] Exact staging deployment contains approved support-specific `x-ticket-token` CORS fix (#170; NOT in observed `a3df890`); allowlisted-origin and denied-origin real OPTIONS browser tests pass. Order API CORS remains narrower.
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
