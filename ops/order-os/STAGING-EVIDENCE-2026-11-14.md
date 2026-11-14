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
