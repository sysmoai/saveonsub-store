# Engineering backlog and extra audit results (2026-11-03)

Read-only findings. Nothing here was applied. Status words: PASS_VERIFIED / PARTIAL / FAIL / BLOCKED / NOT_APPLICABLE.

## A. Extra QA run on the brand branch build (local Chromium, Playwright)

| Check | Result |
|---|---|
| `lang` attribute: `/`, `/p/chatgpt-plus` = `en`; `/bn`, `/bn/all`, `/bn/privacy` = `bn` | PASS_VERIFIED |
| Text size 200% at 320 px wide: horizontal overflow on `/`, `/all`, `/checkout` | PASS_VERIFIED (0 px) |
| Service worker registers and activates | PASS_VERIFIED |
| Offline behaviour | PARTIAL. Playwright's offline switch does not reliably cut service-worker fetches, so the offline page result is not trusted. Needs a real device test. |
| Lighthouse (performance, best-practices) | BLOCKED. Not installed here, no spend or install approved. Run in CI or a real browser later. |
| Screen reader (NVDA/VoiceOver/TalkBack) | BLOCKED. Not available. |

Finding F-1 (SEO/perf, low): `sw.js` precaches `/all.html`, but the navigable URL is `/all`. A visit to `/all` is not served from the precache. Fix: precache the clean URLs too. Not changed.

## B. Issue #88 (conflicting robots rules), read-only

Live `robots.txt` (fetched 2026-11-03, sha256 prefix `fc6cf411e0a55a4e`, saved with this audit) has Cloudflare Managed content first. It lists `GPTBot`, `ClaudeBot`, `Google-Extended`, `Bytespider` and others with `Disallow: /`. The site's own text later lists `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended` with `Allow: /`. `GPTBot` and `ClaudeBot` each appear in two groups.

Python's `urllib.robotparser` (first matching group wins) reports: Googlebot, OAI-SearchBot, PerplexityBot allowed; GPTBot, ClaudeBot, Google-Extended, Bytespider blocked. Google's own parser merges duplicate groups, so its answer for those four may differ. Treat the table as one parser's reading, not as proof of actual crawling.

Not done, and why: the owner policy (allow AI training crawlers or not) is the CEO's decision, and the Cloudflare Bot Preference Sync setting was not opened. No rule was changed.

Smallest fix when the CEO decides: set the policy in Cloudflare (Bot Preference Sync), then make the repo `robots.txt` agree with it, so one source of truth remains.

## C. Cloudflare publishers

- Pages project `saveonsub`: production `77c20d55` (main), custom domains saveonsub.com, www, saveonsub.pages.dev. Seen in the dashboard on 2026-11-02.
- Worker `saveonsub-store` (id `16e887d3ecce497b9036a73556879b70`) exists in the same account. The Workers API returns only its name and id. Its routes, domains and code were not inspected. Before any release, check in the dashboard (Workers & Pages, saveonsub-store, Settings, Domains and Routes) that it does not serve saveonsub.com.

## D. Security and operations backlog (from existing PRs and issues, none assumed live)

Priority order. P0 blocks real orders, P1 before growth, P2 later.

| # | Item | Evidence / where | Priority |
|---|---|---|---|
| 1 | Cloudflare deploy credential: last 5 Canonical Deploy runs failed. Deploys are manual zip uploads. Repair with a scoped Pages token (owner action), keep fail-closed. | Actions history, DEPLOY.md | P0 |
| 2 | Freeze auto-publish on `main` until release review exists. PR #89/#86/#81/#79/#78 all propose variants. Merge exactly one, close the rest. | open PRs | P0 |
| 3 | Privacy claim (PR #94), refund timing, renewal reminder, Terms section 3 provider review. | `POLICY-PROPOSALS-2026-11-02.md` | P0 |
| 4 | Order OS / staff admin (PR #75, #67, #65, #53, #50): none merged, so there is no central order database, staff login or payment confirmation in production. Review as one stack, with Access MFA and RBAC (issues #54, #55). | issues #52-#55 | P1 |
| 5 | Human-verified payment confirmation before any fulfilment message (PR #71). | PR #71 | P1 |
| 6 | Meta inbox saved replies carry another business's prices (isolation violation). Other thread owns it. Do not send. | coordinator note | P0 (other thread) |
| 7 | `aips-live.json` is still tracked in this public repo (excluded from `_site` since PR #90). Remove from the repo in a reviewed PR and rotate nothing, but treat the file as public history. | `stage_deploy.py` EXCLUDE_FILES | P1 |
| 8 | Public repo holds internal docs (audit, gap register, strategy). Move to a private repo. | repo root | P1 |
| 9 | Consent-gated analytics: GA4 (#83) and Meta Pixel (#73) unmerged. Keep inert until IDs and consent copy are approved. | PRs | P2 |
| 10 | Vercel mirror check fails ("Account is blocked") on every PR. Fix the account or remove the integration so PR checks are not red noise. | PR checks | P1 |
| 11 | Backups and recovery: no documented backup of D1/Order OS data or the private brand repo. Write a runbook once the data store is live. | none | P2 |
| 12 | Full Direction A visual reskin (light surfaces, Inter plus Noto Sans Bengali) as a cohort with before/after screenshots and SEO check. | brand kit DECISIONS.md | P2 |
| 13 | SVG logo: no verified vector source exists. Commission a vector redraw (W2) after the S-drawing decision. | AUTHORITY.md | P2 |
| 14 | `sw.js` precache of clean URLs (F-1). | section A | P2 |
