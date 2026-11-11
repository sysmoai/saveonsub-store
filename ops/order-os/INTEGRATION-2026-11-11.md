# Admin + Order OS on current main (2026-11-11)

Status: **DRAFT branch, not merged, not deployed.** Nothing in Cloudflare was created or changed.

## What this branch is

One branch that carries the whole existing admin/Order OS stack onto today's `main` (f5ee660),
instead of five stacked drafts that were 90 commits behind:

| Source PR | What it added | State here |
|---|---|---|
| #50 Order OS v1 | public `/api/orders`, track, D1 schema, staff queue | included |
| #51 public-artifact boundary | `functions/` never in `_site` | included (merged with main's newer `tests`/`aips-live.json` exclusions) |
| #53 commerce SSOT + media | catalog/media tables, poster pipeline | included |
| #65 integration of #51+#50+#53 | — | superseded by this branch |
| #67 security | Access JWT, state machine, payment provenance, PII redaction, atomic claims | included |
| #71 payment-first rails | owner-only payment attestation, paid-only alerts | included |
| #75 Business OS (Codex) | `staff-ui/business*`, `functions/api/ops/business*` | included **unchanged** (Codex-owned) |
| #106 gaps G1–G6 | CORS, fulfiller phone, order costs, renewals, refund evidence | included |

No competing backend was written. Codex's branch `codex/business-os-2026-10-30` was not modified.

## Changes made during integration (and why)

1. `ops/PRICING-V2-2026-09-17.json`: added a stable `plan_id` to each of the 133 CEO-approved plans
   (slug of label + duration). **No price, label or access type changed** (diff is 133 added lines).
   The order API needs a stable plan identity; the old stack never had it because every plan was on HOLD.
2. `functions/lib/order-os/catalog-policy.ts`: the server now uses an **allow-list** (`personal`, `team`).
   Shared and official-guide plans (62) cannot become server orders and stay WhatsApp-only until the
   provider-rights decision. Before, only `shared*` was blocked, so `official` guides would have been orderable.
3. `assets/order-v2.js` is **inert** while `serverCheckoutEnabled` is false: the live checkout keeps its
   current form, WhatsApp message and `confirmWA()` (browser test: main vs branch give the same cart and
   WhatsApp message). The old version injected a phone form and rewrote the WhatsApp text even when off.
4. Storefront content files from the old stack (`build_home.py`, `build_seo.py`, `entertainment_cohort.py`)
   were kept at `main`'s version: one bumped a "verified" date without re-verification.
5. `checkout.html` script tags (old stack wrote a literal `\n`), `staff-ui/assets/logo.svg` synced to the
   brand-kit logo, test fixtures given `plan_id`.
6. New acceptance test `tests/order-os/built-catalog.test.mjs` + CI step: after `build_site.py`, every priced
   plan has a unique `plan_id`, personal plans resolve at the catalog price, a client-sent price is ignored,
   a replayed idempotency key does not duplicate, a shared plan gets 409 and writes nothing.

## Verified on this branch (cloud container, synthetic data only)

- `quality-gates.yml` steps: all pass (133 Python tests, 108 Order OS tests, release truth audit, catalog gate).
- `business-os.yml` steps: all pass, including `wrangler pages functions build`.
- `sos-commerce-ssot.yml`: pass.
- Built `_site/` vs `main`'s `_site/`: identical HTML except the extra `plan_id` argument in `cartAdd(...)`
  and the two inert checkout scripts. No `functions/`, `staff-ui/`, `ops/`, `tests/`, `workers/`,
  `catalog.json` or `aips-live.json` in `_site/`.
- Local synthetic review server (`tests/order-os/business-local.mjs`, loopback, test JWT keys):
  owner → payment verification endpoint reachable (400 only for missing evidence pointer);
  fulfillment (Ripon's role) → `403 PAYMENT_VERIFICATION_FORBIDDEN`; finance figures hidden from
  fulfillment ("Owner / manager access required"). No horizontal overflow at 375px or 1440px.
  `SOS_LOCAL_ROLE=fulfillA` selects the role for this local review.
- Known UI defect: on `business.html` at 375px the brand logo is cropped in its white tile (Codex CSS; not changed here).

## Cloudflare reality (read-only check 2026-11-11)

- D1 `saveonsub-order-os` exists (created 2026-10-29), **0 tables**, no binding verified.
- **No SaveOnSub R2 bucket** (only other units' buckets exist). Media upload endpoints need one.
- Staff Pages project, Access application, Turnstile widget, secrets, custom domain: **not verified**
  from the cloud (the connector cannot read Pages/Access). Treat as not configured.

## Exact acceptance gaps (owner = who must act)

| # | Gap | Owner | Reversible? |
|---|---|---|---|
| C1 | Merge this branch (replaces #65/#67/#71/#75/#106 as the review unit) | CEO approval phrase | yes (revert) |
| C2 | Apply migrations to D1 `saveonsub-order-os` in order: `schema.sql`, `ops/commerce/001_catalog_content_foundation.sql`, `business-schema.sql`, `lifecycle-finance-schema.sql`; export first | CEO approval; Claude can run via connector after approval | export/restore |
| C3 | Create Pages project `saveonsub-staff-staging` (or confirm it exists), bind `DB` → `saveonsub-order-os` | CEO (dashboard) | yes |
| C4 | Zero Trust Access app on `*.saveonsub-staff-staging.pages.dev` (and later `ops.saveonsub.com`), Allow = EMON + Ripon emails, 12h session; Bypass only `/api/orders` + `/api/orders/track` | CEO (dashboard) | yes |
| C5 | Secrets typed by CEO in dashboard: `TEAM_DOMAIN`, `POLICY_AUD`, `TURNSTILE_SECRET_KEY` | CEO | rotate |
| C6 | Enroll operators with `operators-enroll.template.sql` (EMON=owner, Ripon=fulfillment, decided 2026-11-06) | CEO approval | `active=0` |
| C7 | Build then deploy staff project: `python build_site.py` then `npx wrangler pages deploy --config wrangler.order-os.toml` (as documented in that file) from a clean checkout of the approved SHA (functions bundle needs the **built** `catalog.json`) | CEO approval | rollback deployment |
| C8 | Paid-order notification channel (Worker `workers/sos-paid-alerts.mjs` + webhook secret) | CEO choice of channel | yes |
| C9 | R2 bucket for private media (cost ~free tier) | CEO approval | delete bucket |
| C10 | D1 backup: `wrangler d1 export saveonsub-order-os` before every migration + weekly; restore rehearsal on a scratch DB | Claude after C2 | — |
| C11 | Storefront server checkout stays OFF (`serverCheckoutEnabled:false`) until C2–C8 pass on staging with synthetic orders | CEO approval to flip | yes |
| C12 | Provider-rights decision for 59 shared + 3 official-guide plans (they stay WhatsApp-only meanwhile) | CEO | — |

## Staging acceptance script (run after C2–C7, synthetic data only)

1. EMON signs in through Access (Google + 2-step) → `/orders.html` shows "Authenticated role: owner".
2. Ripon signs in → role fulfillment; `POST /api/ops/orders/<id>/payment-verification` → 403.
3. A third Google account → blocked by Access; an enrolled-but-inactive email → 403 from the API.
4. Request without `Cf-Access-Jwt-Assertion` to `/api/ops/*` → 401.
5. Synthetic order via `/api/orders` from `https://saveonsub.com` origin with a test Turnstile key → 201;
   same idempotency key → duplicate; other origin → 403; shared plan → 409.
6. Owner records payment with an evidence pointer → order `payment_confirmed`, one outbox row.
7. Ripon claims, delivers, sets service end date; renewal appears in `/api/ops/renewals`.
8. Remove Ripon from Access + `active=0` → next request 403.
9. Delete synthetic rows; export D1; record evidence in this file.
