# DEPLOY.md — SaveOnSub Production Runbook

**Canonical domain:** https://saveonsub.com  
**Source repository:** `sysmoai/saveonsub-store`  
**Source branch:** `main`  
**Canonical target:** Cloudflare Pages project `saveonsub`  
**Secondary mirror/preview:** connected Vercel project `saveonsub`

Last operational review: **2026-09-03**.

## 1. Deployment model

```text
GitHub main
  ↓
check_prices.py
  ↓
stage_deploy.py
  ↓
_site/  (public files only)
  ↓
staged-surface validation
  ↓
Cloudflare credential/project verification
  ↓
Cloudflare Pages: saveonsub
  ↓
saveonsub.com
  ↓
canonical production smoke tests
```

Vercel separately follows `main` through its Git integration and publishes Vercel-owned production aliases. It is a useful independent build/mirror signal, but it is **not the canonical `saveonsub.com` host unless the custom domain is explicitly attached there and DNS is deliberately migrated**.

## 2. Non-negotiable release rules

1. Never publish repository root (`.`).
2. Only deploy `_site/` created by `stage_deploy.py`.
3. Do not run or restore legacy asset-generation behavior that can recreate the retired tilted-`৳` logo.
4. `assets/logo.svg` and `assets/favicon.svg` must contain `data-brand-lock="2026-08-19-approved"`.
5. Do not expose `catalog.json`, `build_assets.py`, `.env*`, audit/research files or private commercial data.
6. Pull requests validate but never deploy production.
7. A release is green only when `saveonsub.com` itself passes post-deploy verification.
8. Authentication failures are not transient; fail fast and repair credentials.

## 3. Current GitHub Actions secrets

The workflow expects these repository/environment secrets:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

Never put their values in source files, issues, logs, screenshots or chat.

The Cloudflare API token must be active and must have permission to deploy/read the Pages project `saveonsub` in the configured account. Use the minimum required Pages edit/write scope for the correct account.

## 4. Current known production blocker — 2026-09-03

The build and staged release are healthy, but the configured Cloudflare API token currently fails Cloudflare's token verification endpoint with **HTTP 401**. Previous Wrangler output also reported Cloudflare API authentication errors (`10000`) / invalid access token (`9109`).

Therefore:
- do **not** classify current GitHub Actions runs as production-deployment failures caused by website code;
- do **not** retry the invalid token repeatedly;
- do **not** weaken authentication checks;
- repair/replace the GitHub Actions secret and re-run the failed job.

Once the token is replaced, the workflow itself verifies token status and access to the exact `saveonsub` Pages project before upload.

## 5. CI checks executed before production upload

`python check_prices.py`
- prevents known retired prices from shipping beside affected product names.

`python stage_deploy.py`
- builds the public-only `_site/` directory;
- applies the locked SaveOnSub brand assets across staged HTML;
- excludes internal source and development files.

Staged production-surface check verifies:
- approved logo marker;
- approved favicon marker;
- no staged `catalog.json`;
- no staged `build_assets.py`;
- no staged `.env`.

## 6. Cloudflare deployment behavior

The workflow:
1. verifies both required secrets are present;
2. verifies the API token is active;
3. verifies it can access account project `saveonsub`;
4. deploys `_site/` with the current Git commit hash;
5. uses bounded retries only for genuinely transient failures such as provider throttling;
6. aborts immediately on authentication failures.

## 7. Canonical production smoke test

After Cloudflare reports a successful upload, the release is still not considered complete until the workflow verifies:

- `https://saveonsub.com/` responds successfully;
- `https://saveonsub.com/assets/logo.svg` responds successfully;
- homepage and logo asset expose the approved brand lock marker;
- internal source paths such as `/catalog.json` and `/build_assets.py` are not publicly served.

Future smoke tests should additionally cover the top commercial product pages, Bangla homepage, checkout, WhatsApp links, robots, sitemap and critical redirects.

## 8. Vercel mirror verification

The connected Vercel project currently auto-builds GitHub `main`. A healthy Vercel production build means the repository can be staged/deployed independently, but it does not prove `saveonsub.com` is updated.

Use Vercel as:
- independent build validation;
- staging/mirror comparison;
- emergency reference during a Cloudflare incident.

Do not silently point the canonical domain to Vercel as a workaround. Any host migration requires DNS/domain verification, SEO/canonical checks and rollback planning.

## 9. Safe rollback

If a canonical release causes a customer-facing regression:
1. identify the last known-good Git commit/deployment;
2. prefer reverting the offending Git change over editing production files manually;
3. deploy the reviewed reverted `_site/` through the same pipeline;
4. re-run canonical smoke tests;
5. document the root cause before reintroducing the change.

Never solve a production incident by publishing the repo root, bypassing brand/security checks or exposing secrets.

## 10. SEO-sensitive deployment rule

Before changing established URLs, canonicals, redirects, hreflang, major page intent or ranking content:
- capture the current baseline;
- preserve URL equity where possible;
- add permanent redirects for necessary moves;
- update internal links/canonical/sitemap consistently;
- release in controlled cohorts for material SEO/CRO changes;
- monitor after deployment.

## 11. Definition of Done for production

A SaveOnSub production change is **DONE** only when all applicable items are true:

- [ ] Reviewed source change exists in Git.
- [ ] Price/truth checks pass.
- [ ] `_site/` staging passes.
- [ ] Approved SaveOnSub brand remains intact.
- [ ] Internal/non-public files are excluded.
- [ ] Cloudflare credential/project verification passes.
- [ ] Cloudflare Pages deployment succeeds.
- [ ] Canonical `saveonsub.com` smoke test passes.
- [ ] Critical customer journey still works.
- [ ] No unplanned URL/canonical/SEO regression is detected.
- [ ] Rollback commit/deployment is identifiable.

## 12. Production status language

Use precise wording:
- **"Committed"** = code is in GitHub.
- **"Vercel READY"** = Vercel mirror built successfully.
- **"Cloudflare deployed"** = Cloudflare upload succeeded.
- **"Canonical live"** = `saveonsub.com` itself was verified after deployment.

Never use these interchangeably.
