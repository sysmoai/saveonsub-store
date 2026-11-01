# R13 — SaveOnSub Release-Freeze Recovery (review only)

**Evidence reviewed:** 2026-11-02 Asia/Dhaka. **Business:** SOS only.  
**State:** production GO/NO-GO = **NO-GO** pending Cloudflare authenticated release and rollback evidence.

## New verified merge / failed-publish checkpoint

- `main` SHA **`2761db7c10671cdf232c968783cb4f86a4bcad18`** is a merge of [PR #66](https://github.com/sysmoai/saveonsub-store/pull/66) (2026-11-01 19:00 UTC), with 241 changed files and the inherited stack (#84/#77/#76).
- [GitHub Quality Gates 41339530677](https://github.com/sysmoai/saveonsub-store/actions/runs/41339530677) completed SUCCESS against that SHA. The staged `_site` build reported **EXEC-010 HOLD / Price on Request**.
- [GitHub Canonical Deploy 41339530888](https://github.com/sysmoai/saveonsub-store/actions/runs/41339530888) completed FAILURE on the same SHA. The deployment job passed tests and build but stopped **before any Wrangler upload** when scoped `CLOUDFLARE_API_TOKEN` **failed a Cloudflare Pages project read with HTTP 401**. The token exists in the Actions environment but was rejected. Do not assume missing token, repair in plaintext, bypass checks, or blindly retry.
- Read-only public fetch on 2026-11-02 still showed the **old ChatGPT Plus ৳499 shared offer** and **Google AI Pro ৳500 / 211+ orders / AIPS reference** on both `saveonsub.com` and `saveonsub.pages.dev`. The current public content therefore does **not match** the new staged HOLD revision.
- Separate Cloudflare Pages Git integration, deploy hooks, Workers route overrides and the actual Pages deployment ID/source SHA remain **UNVERIFIED** without the owner's authenticated Cloudflare dashboard.

## What this R13 draft PR does

1. Starts from the **current, already merged main** and removes only the automatic `push: main` trigger in `.github/workflows/canonical-deploy-manual.yml`. It keeps `workflow_dispatch` as a placeholder.
2. Adds a top-level job condition `if: ${{ false }}`, so even a manual dispatch **cannot** publish until a future independently approved change enables it.
3. Keeps the existing account/project verification and `wrangler pages deploy` command in source for reviewed restoration, but **never executes** them.
4. Adds four automatic source-level unit tests discovered by the existing Quality Gates, covering event triggers, disabled deployment job, intended Pages project and separation of CI from publishing.

**This draft alone does NOT change production or disable any Cloudflare-native Git integration.**

## Before any approved merge

- [ ] CEO explicitly decides whether the canonical GitHub publisher should remain frozen until the authenticated Cloudflare recovery is complete.
- [ ] Review all changed files; confirm staged 72-SKU commercial HOLD and pricing invariants were not changed by this PR.
- [ ] Confirm current main SHA has not advanced; rebase/review again if it has.
- [ ] Verify Cloudflare Pages project `saveonsub` actual production deployment ID, source SHA, previous restorable deployment, custom domain and Pages Git integration/automatic build settings.
- [ ] Verify `saveonsub-store` Workers route/custom-domain settings and any independent deploy hooks.
- [ ] Require successful GitHub Quality Gates on the exact commit/PR, including all four new freeze tests.
- [ ] Obtain separate human authorization to merge the freeze PR. **Do not merge standalone old PR #79/#80/#81 into main without reconciliation**; their bases predate the 241-file PR #66 merge.
- [ ] Do not publish `main` from Wrangler, Cloudflare UI, Git connection or alternative credentials until a separately approved exact-SHA/rollback release is ready.

## Credential repair — owner only

Cloudflare owner should verify API token is active, correct account scope, and least-privilege Pages permissions in the Cloudflare UI, then update only the authorized GitHub `production` environment secret storage if a controlled release is approved. Record **token identifier and scope** only, **never secret values**. The reported 401 is proof of rejected read authorization at that attempt, not of an expired token or specific missing permission.

## Source links

- [PR #66 merged into main](https://github.com/sysmoai/saveonsub-store/pull/66)
- [Failed deploy HTTP401](https://github.com/sysmoai/saveonsub-store/actions/runs/41339530888)
- [Successful staged Quality Gates](https://github.com/sysmoai/saveonsub-store/actions/runs/41339530677)
- [Previous R09 atomic freeze draft #81](https://github.com/sysmoai/saveonsub-store/pull/81)
- [SYSmoAI SEO Mission SSOT](https://docs.google.com/spreadsheets/d/1VVLmtVGkle13D8esQxORCiNJUmAICDD29e-313Vlfm0/edit)

No customer PII, payment data, secrets, DNS changes or live retail prices were involved.
