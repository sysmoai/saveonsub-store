# SOS PR #183 — one-time canonical Cloudflare release packet
Date: 2026-11-17 (Asia/Dhaka)
Status: READY FOR REVIEW; **not evidence of a live Cloudflare release**.

## Exact intended build source (immutable)
`6d8c8898985896e7857dfbb35ea4d277d0873170` — PR #183 merged main.
Main push Quality Gates: https://github.com/sysmoai/saveonsub-store/actions/runs/44034275907 (success).
The release workflow pins this SHA even though the workflow and test updates are added later. It never publishes whatever happens to be the newest main without a new review.

## Approved offer and forbidden fulfillment
- ChatGPT Go Personal (customer email), 1 month — CEO price BDT 1,290, expected on EN/BN product pages and catalog. Exact legitimate fulfillment/real procurement feasibility still require human verification before fulfilling orders.
- ChatGPT Business Premium Shared (2-3), 1 month — CEO price BDT 1,499 in protected pricing source; **HOLD** in `ops/HELD-PLANS-2026-11-14.json`. Do not expose it as orderable or imply provider-supported credential sharing/resale; the live offer should omit the old BDT 1,299 also.
- Four existing OpenAI/Claude shared-plan holds remain unchanged.
- No sales outreach, domain changes, purchases, provider credentials, payment destination updates, or unrelated brand actions.

## Why old site is stale
Last public inspection showed ChatGPT Go BDT 450 and Business Premium Shared BDT 1,299, despite the GitHub-approved prices. Source merge and successful staging CI do not deploy Cloudflare canonical production. GitHub workflow was manually dispatchable but had `if: false`; previous scoped Cloudflare token preflight returned HTTP 401. That is not authorization to bypass its security checks.

## Safe one-time operator action (after PR merge)
1. Open GitHub Actions > **SaveOnSub Canonical Deploy** > **Run workflow**, branch **main**, once. No push/schedule auto-deploy is enabled. This action does not require giving any token or password to an assistant.
2. Before upload, workflow checks out exact source commit `6d8c8898985896e7857dfbb35ea4d277d0873170`, runs regression and canonical build, validates configured `CLOUDFLARE_API_TOKEN` against account `4ca6269edabb6ad2906d70ec6845de22` and Pages project `saveonsub`, and reads the existing production deployment ID for rollback. Missing token, HTTP 401, no previous production deployment, failed tests or build => stop before upload.
3. Upload only `_site/` via Wrangler to `saveonsub`, branch `main`, referencing the exact release SHA. No alternative token, no DNS/Vercel cutover, no repository-root upload.
4. Workflow checks canonical `saveonsub.com` for Go 1,290, absence of Go 450 and old Business 1,299, Business Premium Shared 1,499 not visible/orderable, held warning, required other price protections, robots, sitemap, checkout noindex, and logo markers. Verification failure is a FAILED RELEASE, not success.
5. Record Cloudflare deployment ID/source SHA and previous production deployment ID; if the canonical host fails or business-critical regression appears, use Cloudflare Pages > Deployments > previous successful production deployment > Roll back. Do not rollback blindly if a Worker or different deployment topology is serving the host. Independent operator verification is required for exact routes and cache.

## Remaining truth gates
- Confirm the customer-owned Go activation route and incurred provider charges before any accepted paid order.
- Business Premium Shared remains HOLD until a provider-authorized separate-seat / reseller mechanism is documented and positive, verifiable unit economics established. CEO price approval alone is not permission to share credentials.
- Canonical custom domain, Pages Git integration and any Worker overrides require authenticated Cloudflare owner readback. No statement here certifies these were verified.

## Evidence
- Pricing: `ops/PRICING-V2-2026-09-17.json`
- Held plan: `ops/HELD-PLANS-2026-11-14.json`
- CI: `https://github.com/sysmoai/saveonsub-store/actions/runs/44034275907`
- Go live: `https://saveonsub.com/p/chatgpt-go`
- Business live: `https://saveonsub.com/p/chatgpt-business`
- Price index: `https://saveonsub.com/prices`
