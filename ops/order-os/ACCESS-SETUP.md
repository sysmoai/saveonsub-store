# SaveOnSub staff access setup (CEO checklist)

Status: plan only. Nothing here has been configured. Every step below is a CEO
action in the Cloudflare dashboard (Claude may guide in the CEO's browser, but the
CEO clicks Save). No password, OTP, token or secret is ever pasted into chat.

Architecture doc: project file `architecture/SAVEONSUB-BUSINESS-ARCHITECTURE-AND-ADMIN-ACCESS-2026-11-06.md`.

## 0. Before you start
- Both staff Google accounts (EMON, Ripon) have 2-Step Verification ON.
- PR stack #65 → #67 → #71 → #75 → this PR approved by exact SHA.
- Staff Pages project `saveonsub-staff-staging` and D1 `saveonsub-order-os` already exist (empty). Do not create duplicates.

## 1. Cloudflare Zero Trust (free up to 50 users)
1. Zero Trust → choose a team name (e.g. `saveonsub`). The team domain becomes `https://<team>.cloudflareaccess.com` (= `TEAM_DOMAIN`).
2. Settings → Authentication → add Google (or keep One-time PIN). Require MFA on the Google accounts themselves.

## 2. Access applications (order matters: most specific path wins)
| App | Domain / path | Policy |
|---|---|---|
| SOS public order API | `ops.saveonsub.com/api/orders` and `ops.saveonsub.com/api/orders/track` | **Bypass**, Everyone |
| SOS staff | `ops.saveonsub.com` (whole host) **and** `*.saveonsub-staff-staging.pages.dev` | **Allow**, Emails = EMON's and Ripon's login emails only; session 12h |

Copy the staff app's **Application Audience (AUD) tag** (= `POLICY_AUD`).

The public order endpoints accept browser origins `https://saveonsub.com` and
`https://www.saveonsub.com` only (see `functions/api/orders/_middleware.ts`).
**New order creation** requires Turnstile. **Tracking** uses a long bearer secret
in `POST /api/orders/track` JSON (`{ "tracking_token": "<opaque token>" }`),
NOT a `GET ?token=...` URL: URL query bearer tokens can appear in logs and
browser history. A tracking response reveals only the order reference, status,
total, currency and timestamps, not customer contact details. Rate-limit the
public tracking endpoint at the edge; Turnstile is not a substitute for token
checking and is not currently required on tracking reads. Staff-only paths
must never be included in a public Access Bypass.

## 3. Staff Pages project settings (`saveonsub-staff-staging`)
- Custom domain: `ops.saveonsub.com` (DNS record Save = CEO).
- Bindings: D1 `DB` → `saveonsub-order-os` (only this one).
- Variables/secrets (typed in the dashboard by the CEO): `TEAM_DOMAIN`, `POLICY_AUD`, `TURNSTILE_SECRET_KEY`.

## 4. Database (staging first, backup before every migration)
Apply in order in the D1 console: `ops/order-os/schema.sql`, `ops/commerce/001_catalog_content_foundation.sql`,
`ops/order-os/business-schema.sql`, `ops/order-os/lifecycle-finance-schema.sql`.
Then enroll staff with `ops/order-os/operators-enroll.template.sql` (replace the two email placeholders).

## 5. Acceptance (with synthetic data only)
- EMON logs in → sees all orders, can verify a synthetic payment.
- Ripon logs in → cannot verify payment, refund or see finance; can claim, deliver, see the phone only on his claimed order, set a service end date.
- A third Google account is refused by Access; an enrolled-but-inactive email gets 403.
- `https://saveonsub.com` can create a test order once a sellable plan exists (Issue #69); other origins get 403.

## 6. Removing access
Remove the email from the Access policy **and** set `operators.active = 0`.
