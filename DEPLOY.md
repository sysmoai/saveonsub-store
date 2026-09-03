# DEPLOY.md — SaveOnSub Production Runbook

**Canonical domain:** https://saveonsub.com  
**Source repository:** `sysmoai/saveonsub-store`  
**Source branch:** `main`  
**Canonical host:** Cloudflare Pages project `saveonsub`  
**Secondary mirror:** connected Vercel project `saveonsub`

Last operational review: **2026-09-03**.

## Current deployment truth

The previous direct GitHub Actions Cloudflare deployment workflow (`.github/workflows/deploy.yml`) was removed on 2026-09-03 after repeated credential/authentication failures. Therefore **there is currently no active GitHub Actions job that automatically publishes `main` to canonical `saveonsub.com`**.

Vercel still follows the repository through Git integration and is useful as an independent build/mirror signal, but `saveonsub.com` is not attached to that connected Vercel project. A Vercel READY deployment must never be called canonical-live.

Do not silently re-create the removed Cloudflare workflow or move DNS to Vercel. Restoring canonical automation requires a reviewed deployment path, valid least-privilege Cloudflare credentials, staged-artifact validation and canonical smoke tests.

## Required release pipeline

```text
GitHub reviewed source
  ↓
check_prices.py
  ↓
audit_all.py / deploy_preflight.py as applicable
  ↓
stage_deploy.py
  ↓
_site/  (public files only)
  ↓
release_hardening.py
  ↓
cache_safe_brand.py
  ↓
release-boundary checks
  ↓
reviewed Cloudflare Pages deployment
  ↓
saveonsub.com
  ↓
canonical smoke tests
```

## Non-negotiable rules

1. Never publish repository root (`.`); publish only reviewed `_site/` output.
2. Never expose `catalog.json`, build scripts, `.env*`, research/audit files, supplier data or secrets.
3. Preserve the approved 2026-08-19 SaveOnSub brand lock and immutable/cache-safe logo references.
4. `release_hardening.py` must run after staging and before brand cache versioning/deployment.
5. Do not ship blanket claims that all products are official/customer-owned/private or that every plan receives the same warranty/replacement SLA.
6. Preserve ranking URLs, canonicals, hreflang and internal-link equity unless a reviewed migration is necessary.
7. Pull requests validate only. They never mean canonical production was updated.
8. A release is complete only when `https://saveonsub.com/` itself is verified after deployment.

## Current automated validation

`.github/workflows/quality-gates.yml` runs on pull requests, pushes to `main`, manual dispatch and weekly schedule. It validates source truth/prices, repository regression, staged public output, staged truth/SEO hardening, AI crawler policy, approved brand markers and public-source exclusion.

The connected Vercel project builds with:

```text
check_prices.py
→ stage_deploy.py
→ release_hardening.py
→ cache_safe_brand.py
```

This provides a useful release-preview artifact, not canonical proof.

## Canonical restoration requirements

Before restoring automated Cloudflare publishing:

- validate the exact Cloudflare account and Pages project `saveonsub`;
- use a valid least-privilege credential without exposing it in code/logs/chat;
- deploy only hardened `_site/`;
- verify homepage, top commercial products, Bangla homepage, robots, sitemap, checkout/WhatsApp path and critical redirects;
- verify approved immutable logo references;
- verify internal source paths remain inaccessible;
- keep a known-good rollback commit/deployment.

Credential rotation/replacement, DNS changes and domain ownership changes are human-controlled boundaries.

## SEO-sensitive release rule

Before changing established URLs, title intent, canonical, hreflang, structured data, navigation or substantial money-page copy:

- capture current search intent and internal links;
- preserve the URL whenever possible;
- use permanent redirects only for necessary moves;
- update internal links/canonical/sitemap together;
- release material SEO/CRO changes in controlled cohorts;
- measure post-release query, indexation and conversion impact.

## Definition of Done

Use these terms precisely:

- **Committed** — source exists in GitHub.
- **Quality gates passed** — source and staged public artifact passed automated checks.
- **Vercel READY** — the mirror/preview built successfully.
- **Cloudflare deployed** — a reviewed upload to the Cloudflare Pages project succeeded.
- **Canonical live** — `saveonsub.com` itself was smoke-tested after that deployment.

Never use these interchangeably.
