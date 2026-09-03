# AGENTS.md — SaveOnSub Production Authority

## Project
- Business: SaveOnSub / SAVEONSUB
- Canonical domain: https://saveonsub.com
- Repository: sysmoai/saveonsub-store
- Owner / CEO: Emon Hossain
- Current operating authority date: 2026-09-03
- 50,000+ monthly organic visitors is a growth target, never a current fact or guarantee.

## Primary operating doctrine
The existing live website is already a revenue-producing organic-search asset. Never replace or casually rebuild it.

**PROTECT → MEASURE → FIX → ENRICH → AUTOMATE → SCALE**

Preserve existing ranking URLs, search intent, useful content, internal-link equity, working conversion paths and lightweight static delivery unless evidence justifies a controlled change. Large migrations, framework rewrites, domain moves, URL changes and broad content deletions require an explicit migration plan, baseline and rollback path.

## Current stack truth
- Frontend: generated static HTML + CSS + vanilla JavaScript.
- Data/build source: repository data and Python generators.
- Public release directory: `_site/`, produced by `stage_deploy.py`.
- Browser state currently handles cart/recent order history; there is not yet a central production order database, customer-account backend or automated payment gateway.
- GitHub `main` is the source branch.
- Vercel is connected to this repository and auto-deploys `main` to Vercel-owned production aliases. `saveonsub.com` is not currently attached to the connected Vercel project.
- Canonical production path is intended to be GitHub Actions → Cloudflare Pages project `saveonsub` → `saveonsub.com`.
- Do not describe GitHub Pages / `gh-pages` as the current production path.
- As of 2026-09-03, the Cloudflare deployment workflow is fail-closed because the configured `CLOUDFLARE_API_TOKEN` returns HTTP 401. Build/staging and the Vercel mirror are healthy. Do not claim the newest commit is canonical-live until the Cloudflare credential is repaired and canonical smoke tests pass.

## Final brand lock
- The CEO-approved SaveOnSub logo/icon supplied on 2026-08-19 is final and locked.
- Preserve the exact approved `S` icon formed by the price-tag upper element, percentage symbol and lower circular arrow, plus approved SaveOnSub.com lockups.
- Approved primary palette: teal/green + dark navy/charcoal + white/light neutral.
- Do not redraw, approximate, re-typeset, recolor, distort, crop incorrectly, substitute or AI-regenerate the mark.
- The older tilted price-tag + `৳` concept is deprecated.
- Production `assets/logo.svg` and `assets/favicon.svg` must retain `data-brand-lock="2026-08-19-approved"`.
- `stage_deploy.py` enforces the approved brand assets across staged HTML. Do not bypass it.

## Brand and business constants
- Primary WhatsApp / customer contact: **+880 1305 869242**.
- Canonical WhatsApp URL: `https://wa.me/8801305869242`.
- Brand promise/positioning should emphasize verified savings, clear plan labeling and real human support without unsupported superiority claims.
- Do not reuse sister-business proof, customer data, contacts, payment evidence or order counts as SaveOnSub proof unless explicitly and truthfully labeled as store-family evidence.

## Claim safety and product truth
Every customer-facing claim must be current and evidence-backed. Never publish or retain unsupported claims about:
- `#1`, `best`, `most trusted`, `cheapest`, `only`;
- customer/order/review/traffic counts;
- savings percentages, compare-at prices or bestseller ranks;
- exact delivery, response or replacement SLAs;
- warranty/refund guarantees;
- `official`, `authentic`, `personal`, `customer-owned`, partner/reseller/distributor status;
- privacy, account sharing, provider policy or legal status.

Every product must disclose the real access method before payment. Provider-specific statements require a source and verification date. Do not convert a shared/managed mechanism into an `official` or `personal` label for marketing.

## SEO no-regression contract
Before changing an established indexable URL, title intent, canonical, hreflang, structured data, navigation or major body content:
1. Capture the current URL and search intent.
2. Check current internal links and canonical/hreflang relationships.
3. Preserve the URL unless a migration is necessary.
4. If a URL changes, provide a permanent redirect and update canonical/internal links/sitemap consistently.
5. Prefer controlled cohorts for major SEO/CRO changes instead of site-wide speculative edits.
6. Never fake freshness by changing published/modified dates without meaningful content changes.
7. Structured data must match visible page content.

## Production safety
- Never publish the repository root.
- Only `_site/` is a production artifact.
- Internal files such as `catalog.json`, build scripts, `.env*`, research/audit docs, supplier/cost/margin information and credentials must never be served publicly.
- Never print, expose, request or commit secret values.
- Pull requests may validate/stage but must not deploy canonical production.
- A release is complete only after the canonical domain passes smoke tests; an upload alone is not enough.
- If Cloudflare authentication fails, do not weaken the workflow or route around validation. Repair credentials.

## Deployment authority
The authoritative deployment procedure is `DEPLOY.md` plus `.github/workflows/deploy.yml`.

A green production release requires, at minimum:
- price consistency check passes;
- `_site/` staging passes;
- approved brand markers pass;
- internal-source exclusion checks pass;
- Cloudflare token is active and can access project `saveonsub`;
- deployment completes;
- `https://saveonsub.com/` returns successfully;
- canonical `assets/logo.svg` carries the approved brand-lock marker;
- prohibited source paths remain inaccessible.

## Management system
Use the repository as the technical source of truth, but do not put private commercial secrets into a public repository. Until repository privacy is changed/split, keep supplier credentials, purchase costs, margin intelligence, customer data and payment evidence outside this repo.

Priorities, in order:
1. Production reliability and rollbackability.
2. Truth/brand/security consistency.
3. Measurement (Search Console, web analytics, conversion events).
4. Improve pages already earning impressions/clicks/sales.
5. Original Bangladesh-specific product/price/comparison content and media.
6. Central order/payment/customer backend and admin operations.
7. Renewal, WhatsApp and fulfilment automation.
8. Authority/backlink/video expansion toward the 50K organic target.

## Human approval boundaries
Never silently perform destructive or irreversible actions involving domain/DNS ownership, payment money movement, credential rotation, deletion of ranking URLs, bulk deletion of content, customer-data exports, refunds or provider-account access. Prepare/validate changes and use the safest reversible path.
