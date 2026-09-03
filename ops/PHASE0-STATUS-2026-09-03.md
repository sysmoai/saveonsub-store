# SaveOnSub Phase 0 Production Status — 2026-09-03

## Operating rule
Protect the working organic/revenue asset. Measure before broad changes. Fix only verified P0 issues first. No URL migration, framework rewrite, or mass content replacement without regression evidence.

## Canonical production truth
- Canonical domain: https://saveonsub.com
- Current edge: Cloudflare
- Current origin family verified by asset hash: Cloudflare Pages (`saveonsub.pages.dev`)
- GitHub Pages is not the current production origin.
- Vercel is an active production mirror/secondary deployment, but `saveonsub.com` is not attached to the Vercel project.

## Brand lock
- Approved master identity date: 2026-08-19.
- Canonical mark: SaveOnSub `S` formed by price-tag upper element, percentage symbol, and lower circular arrow.
- Deprecated mark: tilted price-tag + ৳ concept.
- Source/staging brand lock marker: `data-brand-lock="2026-08-19-approved"`.
- Vercel mirror currently serves the approved brand-locked build.
- Canonical Cloudflare release is still older and does not yet carry the brand-lock marker.

## Production safety already implemented
- Public-only `_site/` staging.
- `catalog.json`, build scripts, repo docs, `.env*`, package/deploy metadata excluded from public deployment.
- Brand regression checks.
- Price-consistency check.
- PRs cannot publish production.
- Cloudflare credential preflight.
- Bounded retry only for transient deploy failures.
- Post-deploy canonical smoke test.
- Canonical source-leak checks.
- Vercel now publishes `_site/` instead of repo root.

## Verified live safety
At the time of the 2026-09-03 production probe:
- `/` -> HTTP 200
- `/catalog.json` -> HTTP 404
- `/build_assets.py` -> HTTP 404
- `/.env` -> HTTP 404

## External blocker
The only credential stored under the current deployment secret namespace is `CLOUDFLARE_API_TOKEN`, and Cloudflare returns HTTP 401 for token verification. Alternate common Cloudflare token aliases and Deploy Hook aliases were checked without exposing values; none are present.

The connected ChatGPT environment has authenticated GitHub and Vercel access but no authenticated Cloudflare account connector, and GitHub's connector intentionally does not expose secret values or secret-management endpoints. Therefore an active Cloudflare Pages token cannot be minted or substituted from this environment.

## Completion condition for Phase 0 / Step 1
Step 1 becomes COMPLETE only when all of the following are true:
1. Cloudflare API token is active.
2. Token can access Pages project `saveonsub` in the configured account.
3. `_site/` deploy succeeds.
4. `saveonsub.com` serves the approved brand-locked release.
5. Sensitive source paths remain 404.
6. Homepage, product page, Bangla page, checkout and WhatsApp handoff smoke tests pass.

## Do not do
- Do not move the custom domain to Vercel merely to bypass a credential problem.
- Do not delete/rewrite ranked URLs without Search Console evidence and a redirect/canonical plan.
- Do not expose supplier cost, internal pricing intelligence, credentials, proof or customer data in the public repository or public build.
- Do not claim a production release succeeded until the canonical custom domain is verified.
