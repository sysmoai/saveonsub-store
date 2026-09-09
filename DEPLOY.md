# DEPLOY.md — SaveOnSub Production Runbook

**Canonical domain:** https://saveonsub.com  
**Source repository:** `sysmoai/saveonsub-store`  
**Source branch:** `main`  
**Canonical host:** Cloudflare Pages project `saveonsub`  
**Secondary mirror:** connected Vercel project `saveonsub`

Last operational review: **2026-09-09**.

## Current deployment truth

The canonical deployment workflow is `.github/workflows/canonical-deploy-manual.yml`. It remains manually dispatchable and, once the reviewed automation change is merged, also runs on pushes to `main`.

The workflow is deliberately fail-closed. It validates repository truth, builds the exact hardened `_site/` artifact, verifies the exact Cloudflare account/project before upload, deploys only `_site/`, and then smoke-tests the real `saveonsub.com` canonical host. Missing/invalid Cloudflare credentials stop the release; they must never be bypassed.

Vercel follows `main` through Git integration and remains an independent build/mirror signal. `saveonsub.com` is not attached to that Vercel project, so Vercel READY is not canonical-live proof.

## Required release pipeline

```text
reviewed GitHub main commit
  ↓
check_prices.py + audit_all.py + deploy_preflight.py
  ↓
build_site.py
  ↓
canonical ordered hardening/cohort pipeline
  ↓
_site/ only
  ↓
release-boundary checks
  ↓
exact Cloudflare Pages project verification
  ↓
Cloudflare Pages deployment using exact release SHA
  ↓
saveonsub.com
  ↓
canonical smoke tests
```

`build_site.py` is the canonical build orchestrator. Do not maintain a second hand-written build sequence in deployment configuration.

## Non-negotiable rules

1. Never publish repository root (`.`); publish only reviewed `_site/` output.
2. Never expose `catalog.json`, build scripts, `.env*`, research/audit files, supplier data or secrets.
3. Preserve the approved 2026-08-19 SaveOnSub brand lock and immutable/cache-safe logo references.
4. Run the canonical `build_site.py` pipeline rather than cherry-picking individual cohort scripts.
5. Do not ship blanket claims that all products are official/customer-owned/private or that every plan receives the same warranty/replacement SLA.
6. Preserve ranking URLs, canonicals, hreflang and internal-link equity unless a reviewed migration is necessary.
7. Pull requests validate only; they do not deploy canonical production.
8. A release is complete only when `https://saveonsub.com/` itself passes post-deploy smoke tests.
9. If Cloudflare authentication or project verification fails, repair the credential/permission; do not route around the guard.

## Current automated validation

`.github/workflows/quality-gates.yml` runs on pull requests and pushes to `main` (plus its configured manual/scheduled modes). It validates source truth/prices, regression safety, staged public output, provider cohorts, technical SEO, crawler policy, approved brand markers and public-source exclusion.

The connected Vercel project executes `python3 build_site.py` and publishes `_site/`. That is a useful mirror and release-preview signal, not canonical proof.

The canonical Cloudflare workflow runs the same build orchestrator and adds exact-project credential verification plus real-host smoke tests. On a `push` event it checks out and deploys the exact pushed SHA; on manual dispatch it deploys current `main`.

## Cloudflare credential requirements

The production secret `CLOUDFLARE_API_TOKEN` must be least-privilege and able to access account `4ca6269edabb6ad2906d70ec6845de22`, Pages project `saveonsub`.

The workflow verifies this project through the Cloudflare API before Wrangler is allowed to upload anything. Secret values must never be printed, committed or requested in chat.

Credential rotation/replacement, DNS changes and domain ownership changes remain human-controlled boundaries.

## Canonical smoke-test minimum

After upload, verify at least:

- homepage responds and contains the staged measurement script;
- `robots.txt` retains `OAI-SearchBot` policy;
- sitemap has clean canonical URLs and no same-origin `.html` entries;
- top governed money pages contain their current fact markers and truth-safe disclosures;
- checkout remains `noindex,follow`;
- old keyword-dump, converted-price, unsupported low-risk/warranty/privacy claims are absent;
- approved branding remains intact.

An upload that does not converge on the canonical host is a failed release.

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
- **Cloudflare deployed** — the hardened artifact was uploaded to the verified Cloudflare Pages project.
- **Canonical live** — `saveonsub.com` itself was smoke-tested successfully after that deployment.

Never use these interchangeably.
