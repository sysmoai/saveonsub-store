# SaveOnSub Order OS / support staging: read-only evidence checkpoint

Date: 2026-11-14 (Asia/Dhaka). Evidence is scoped to the **staging Pages project** and draft GitHub branches. This is *not* a customer-facing production acceptance or an authorization to deploy.

## Observed from the CEO's connected browser (read-only)

- Cloudflare Pages project: `saveonsub-staff-staging`; domain `saveonsub-staff-staging.pages.dev`.
- The Pages UI labels its environment **Production**, but that is the production environment *inside this staging project*, **not** the live `saveonsub.com` storefront.
- The selected deployment source is branch `staging/order-os-tickets`, commit `a3df890aa8871e8a0cb61d3a5ea8f636ba1ba569` ("Merge PR 164 into staging branch").
- Cloudflare deployment ID: `606c4daf-b9e4-4c77-828d-24bdea657dc9` (short URL `606c4daf.saveonsub-staff-staging.pages.dev`).
- An already-authenticated browser displayed the staff ticket desk, `Authenticated role: owner`, `Protected ticket queue loaded`, and **no visible tickets**. This is an observed UI/read result; it does **not** independently establish real D1 schema parity, two-account allowlist, MFA or Ripon RBAC negative tests.
- Independent unauthenticated URL retrieval reported `login_required` for the staff desk, `/api/ops/tickets`, the immutable deployment preview and the customer support-status / order-tracking endpoints. It confirms a visible login barrier on those probes only. It does **not** prove the correct path-scoped Bypass rules, Access session security, the HTTP status codes or functional token-based customer API.
- Repository readback of the deployed staging source's `functions/api/support/_middleware.ts` shows it still re-exports `../orders/_middleware`. The latter allows `content-type` but not `x-ticket-token` in CORS preflight. The support-specific fix and regression tests are in **draft PR #170** (stacked on #164), **not** in deployment `a3df890`.
- The connected branch's `assets/order-config.js` remains `apiBase: ""`, `turnstileSiteKey: ""`, `serverCheckoutEnabled: false`. Public checkout/ticket activation is **not** proven and is not authorized by this read-only checkpoint.

Evidence references:
- `https://github.com/sysmoai/saveonsub-store/commit/a3df890aa8871e8a0cb61d3a5ea8f636ba1ba569`
- `https://github.com/sysmoai/saveonsub-store/pull/163`
- `https://github.com/sysmoai/saveonsub-store/pull/164`
- `https://github.com/sysmoai/saveonsub-store/pull/170`
- Cloudflare Pages deployment details under the CEO-authorized account (ID above); never copy cookies, account tokens, Access JWTs or Turnstile secrets into the repository.

## Blockers (still not verified)

1. **D1 migration inventory and backup:** list the real bound staging D1 and its migrations via authorized dashboard access; prove the exact six-file full-OS schema order in `ACTIVATION-RUNBOOK-2026-11-14.md`. Test `PRAGMA table_info(support_threads)`, trigger presence, `PRAGMA foreign_key_check` read-only. Do not replay any `ALTER TABLE ADD COLUMN` against an already migrated D1; export/backup before any subsequently approved migration.
2. **Access policy boundaries:** verify host rules separately for `*.pages.dev`, deployment preview hostnames and any `ops.saveonsub.com` domain. Staff paths `/api/ops/*` and `/tickets` must require allowlisted staff identity and MFA. A deliberately public customer API path requires a much narrower Bypass application (`/api/support/tickets*`, `/api/orders*` as needed), not an unconditional host-wide Bypass. A Bypass also removes Access enforcement and its Access request logging on that route, so token checking, Turnstile (create), rate limit and application logging must remain sound.
3. **Real browser preflight:** after an *authorized staging deploy of the exact #170 fix*, use a fresh browser origin `https://saveonsub.com` to send OPTIONS to staging `/api/support/tickets/status` with `Access-Control-Request-Method: GET` and `Access-Control-Request-Headers: x-ticket-token`. The response must permit the canonical storefront origin and `x-ticket-token`. The same preflight against `/api/orders/track` must **not** add this extra ticket header; a foreign origin must be denied. Record status, CORS headers, deployment ID/commit and time; no real customer data.
4. **Authentication and role checks:** CEO and Ripon each independently authenticate with assigned real accounts, confirmed MFA, intentional role, and permitted paths; test a third unauthorized identity, inactive operator, support vs fulfillment restrictions, payment verification and private-cost visibility. Staff screenshot/role label alone cannot prove these controls.
5. **Turnstile and rate limits:** staging real widget and server-side verification; invalid/missing proof must fail; public create endpoints rate-limited, token/status endpoints anti-enumeration. The read-only external probes above returned login-required for customer endpoints; do not assume they are correctly enabled or broken until exact Access applications and expected response codes have been reviewed.
6. **Order/payment/commerce:** the payment receiving destination and its ownership, merchant settlement readback, provider fulfillment authorization, service coverage, retention/consent, and any real data import remain independently gated. Screenshots, fake D1 orders, and an authenticated staff page are not proof of sales or payment.
7. **Release:** PR stack #163 -> #164 -> #170 must be reviewed at current exact SHAs and full CI. No push to `staging/order-os-tickets`, Cloudflare Access/policy changes, new paid service, merge to `main` or live deployment without the corresponding CEO approval and rollback evidence.

## What was done in this checkpoint

Read-only browser/Cloudflare metadata, authorized GitHub source inspection and anonymous login-boundary probes. No secrets accessed, no D1 writes, no customer messages, no Access policy modification, no Cloudflare deployment or branch merge. CI in #170 uses synthetic data and cannot substitute for the staged security proofs above.


## Subsequent CEO-reported real-staging synthetic ticket test (14 Nov 2026)

**Provenance:** CEO-supplied summary of a test carried out on the actual Cloudflare staging service while authenticated using the CEO's Access login. The raw request/response log, exact testing deployment ID and timestamp, and D1 audit-event export were **not provided or independently reproduced in this checkpoint**. The results below are therefore **REPORTED PASS**, not independently signed-off production acceptance. They are a meaningful improvement over FakeD1-only tests.

| Test | Reported outcome | Evidence status |
| --- | --- | --- |
| Malformed input | HTTP 400 | CEO-REPORTED PASS |
| Unknown order | HTTP 404; no write | CEO-REPORTED PASS |
| Synthetic ticket creation | One-time DISPLAY of access code | CEO-REPORTED PASS |
| Correct code to view status | HTTP 200 | CEO-REPORTED PASS |
| Wrong or absent code | Same HTTP 404; avoids existence disclosure | CEO-REPORTED PASS |
| Escalation | Reason required | CEO-REPORTED PASS |
| Code rotation | New code works | CEO-REPORTED PASS; old-code rejection should also be recorded in service log |
| Assign unknown operator | HTTP 404 | CEO-REPORTED PASS |
| Closed ticket mutation | HTTP 409 | CEO-REPORTED PASS |

The synthetic test ticket is reportedly **closed and retained in the staging D1**. Do not delete, alter, export sensitive identifiers or copy it into production; treat it as test/audit evidence. The earlier authenticated page view displaying zero tickets was a separate earlier observation and does not supersede this later CEO report.

**Important terminology:** "Access code shown once" means the secret is revealed at issuance and its hash is stored; it is not a single-use login OTP. A valid ticket code may be reused until rotated; rotation invalidates the previous code. The actual one-time-use Cloudflare Turnstile challenge token is a different concept.

### What this test DOES NOT prove

- Ripon's separate real Access login, least-privilege role, and negative authorization checks against payment verification, private financial data, unassigned orders and assignment actions.
- Real Turnstile site key + `TURNSTILE_SECRET_KEY` Siteverify response, invalid-token rejection, expiration/replay tests, or fail-closed behavior under outages. Test/stub credentials are not production verification.
- Real order-linked ownership verification: no usable genuine staging order existed in the reported test. Unlinked staff-assisted tickets cannot prove paid-order ownership.
- A customer-facing (unauthenticated Cloudflare Access) browser reaching narrowly public ticket endpoints. CEO session success is NOT public consumer success. The specific Access Bypass app/policy, allowed paths, and cross-origin preflight need independent approval and testing.
- Cloudflare per-IP/route rate limits, throttling response (e.g. 429), anti-bruteforce monitoring, and privacy-safe logging.
- Actual D1 migration ledger, database backup/restore demonstration, code-to-deployment source SHA parity for the later tests, concurrent writes/retry behavior, leak-free retention/deletion policy, or production/payment fulfillment.
- The draft `x-ticket-token` CORS fix in PR #170 being on the deployed staging artifact. An authenticated same-origin test may pass while a storefront cross-origin preflight still fails.

### Release acceptance order — no automatic actions

1. Preserve redacted staging HTTP test matrix (method, path, status, expected response, no-write counts, timestamp, deployed source SHA and Cloudflare deployment ID); never log ticket access tokens, OTPs, passwords or JWTs.
2. Read-only inspect bound staging D1's exact schema/migration state; take backup before *any separately authorized* D1 migration. Do not rerun non-idempotent ALTER statements.
3. Confirm CEO and Ripon accounts, explicit role matrix, MFA and denied third identity; document real negative tests.
4. Obtain CEO-approved Turnstile secret through the Cloudflare secrets UI (never store in repository); verify Siteverify success, invalid/missing/replayed tokens, hostname and no-write failures.
5. Prove path-specific Access policies and customer API protection (no broad bypass); coordinate draft PR #170 CORS and #172 tracking-token contract to avoid partial client/backend deployment. Test allowed and denied origins from an actual browser.
6. Configure and observe rate limits on **the actual domain/route**; demonstrate 429/mitigation without affecting unrelated checkout traffic. Cloudflare documents that zone WAF settings apply when a Pages custom domain is proxied through that zone; **do not assume a rate limit configured on the `saveonsub.com` zone automatically protects `saveonsub-staff-staging.pages.dev`**. Verify the actual hostname/plan coverage and test 429. Do not add a custom domain or change DNS without specific CEO approval.
7. Synthetic linked-order end-to-end: order creation, tracking proof, ticket creation, staff response, escalation, code rotation, close, audit events and denied writes. Keep every test clearly synthetic. Re-test rollback/restore in staging.
8. Separately verify authorized payment receiver, supplier fulfillment rights, privacy/retention, notifications, support SOP, monitoring, and release parity. Only after independent CEO exact-SHA approval should a production merge or deployment be considered.

**Verdict:** the real staging synthetic ticket lifecycle is *CEO-reported passed*, but public customer availability, real staff isolation, bot/abuse defenses, and production safety remain **NOT VERIFIED**. `#163/#164/#170` remain draft/not merged into main.
