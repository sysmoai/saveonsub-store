# Claude Code recovery state — SaveOnSub

Single handoff file for a fresh Claude Code session. Read this first, then `git log -10` and `gh pr list`.
Keep it current after every milestone. It records facts and decisions; it is not a plan to re-litigate.

## Checkpoint

| | |
|---|---|
| Written | 2026-10-23, after the T-05 security work (Bangladesh time) |
| Repo | `sysmoai/saveonsub-store` (**PUBLIC**, see F-014) |
| Worktrees | `...\apps\saveonsub-store` = PR #66 branch `review/sos-production-safety-2026-10-23` (green, untouched by T-05). `...\apps\saveonsub-store-pr65` = security branch `fix/sos-staff-admin-security-2026-10-23` (**PR #67**, draft, base = #65's branch, stacked on #66). |
| PR #66 head | `27ec2ac`, full-regression green (run 39894150661). Not merged. |
| PR #67 head | `fc5b2d8` (see `git log`), pushed with no force. #65's own head `aa031b8` is untouched. |
| GitHub Actions | #66: green. #67: **Quality Gates run 39897537422 = success on `fc5b2d8`** (dispatched manually). Quality Gates only trigger for PRs/pushes targeting `main`, so a PR based on another branch gets no CI; run `gh workflow run "SaveOnSub Quality Gates" --ref <branch>`. Legacy `Vercel` status fails everywhere (F-015). |
| Production deploy | **None from this work. Awaiting CEO authorization.** |
| Safety snapshot | `refs/backup/wip-20261023` (local only; pre-recovery uncommitted work) |

## Verified (actually run locally, Windows, Python 3.14; CI uses 3.12)

`check_prices.py`, `python -m unittest test_audit_home_prices`, `test_whatsapp_cta.py` (9/9), `audit_all.py` (0 gaps),
`deploy_preflight.py`, `build_site.py`, and the full "Verify governed pricing-v2 release boundary" step of
`quality-gates.yml` (extracted and run in bash) all exit 0 against a fresh `_site/`.

**T-05 evidence (security branch):** `node --import ./tests/order-os/register.mjs --test tests/order-os/*.test.mjs` = 66/66 (Node >= 22.18; real handlers + real schema/triggers on in-memory SQLite; synthetic data). `audit_order_os.py` OK and mutation-checked. Strict `tsc` clean on every touched file (1 pre-existing error in `catalog/index.ts`, a `TextDecoder` typing quirk). `wrangler pages functions build` compiles all 12 routes. Full Python CI sequence + release-boundary script pass. `_site` has no functions/ops/tests/schema.
Same scenarios against the original `aa031b8` handlers: 8/8 probes vulnerable (manager reactivates refunded; support completes unpaid; confirm without proof; claim moves unpaid to assigned; viewer sees name and event notes; racing claim overwrites; stale write logs an event).

**Not yet verified:** any browser/staging check, live saveonsub.com, Cloudflare Access/D1/R2 bindings, real role rows in D1.

Run the CI sequence locally (delete `_site/` first, as CI has none when auditing):

```
python build_home.py && python build_pages.py      # generated root pages are tracked; regenerate after catalog changes
python -m unittest test_audit_home_prices && python test_whatsapp_cta.py
python check_prices.py && python audit_all.py && python deploy_preflight.py
python build_site.py
```

Windows needs `tzdata` (now in requirements.txt) for `provider_fact_freshness.py`. In a git worktree `.git` is a file; `stage_deploy.py` now excludes it.
`build_all.sh` / `build_catalog.py` are legacy and crash on the v2 catalog (`KeyError: 'tos'`). Do not use them.
The pipeline of record is `build_site.py` (see `.github/workflows/quality-gates.yml`).

## Pricing authority: EXEC-010 HOLD (founder, 2026-10-23 22:07 Asia/Dhaka)

The table previously here ("CEO decisions on record") was **agent-recorded by
Claude Code, not founder-approved**. The founder confirmed he did not give those
re-prices. EXEC-010 locked decisions are authoritative:

| SKU | Status |
|---|---|
| Google AI Pro | **Price on Request** (EXEC-010 D1): no price, no checkout |
| ChatGPT Plus | **HOLD** (EXEC-010 D2): ৳3,390 not re-approved, not sellable |
| All other products | Price on Request until the founder approves a specific price in his own words |

Enforced by `ops/PRICING-V2-2026-09-17.json` `commercial_hold`, `apply_pricing_v2.py`,
`audit_policy.py`, `audit_commercial_truth_v2.py` and the workflow HOLD asserts.
Netflix facts (`ops/ENTERTAINMENT-COHORT-FACTS-*.json`) still need an authoritative human re-check.

## What was fixed (root causes)

1. `audit_all.py` `min()` on empty `plans[]` (run 39869844323). Resolved via `c9015e8`'s tested `audit_home_prices.py`.
2. Generated pages were stale/broken: `build_pages.py` crashed on the v2 catalog and truncated `p/chatgpt-plus.html` to 0 bytes (open-before-render). Fixed. (The earlier note that inquiry pages carry `data-inquiry-only` was not true of the built `_site`; HOLD is verified by `audit_commercial_truth_v2.py` instead.)
3. Stage cohorts assumed full priced pages: `google_ai_cohort`, `design_cohort` (explicit inquiry path), `chatgpt_cohort` (shared label only if a shared plan exists), `runway_cohort` (plan renamed by Pricing V2; retired Unlimited plan must stay disabled).
4. Leftover "A SYSmoAI venture" footer branding removed; audit now fails if SYSmoAI appears in Organization schema.
5. Release gate contradicted committed decisions — superseded by SOS-T018: gates now assert the EXEC-010 HOLD.

## Findings register

Priority: P0 release-blocking · P1 important · P2 improvement · P3 optional. Owner: CEO = needs Emon.

| ID | Pri | Finding | Evidence | Owner | Status |
|---|---|---|---|---|---|
| F-001 | P0 | `full-regression` red on PR #66 | run 39869844323; later c9015e8 run 39893629926 | Claude | Fixed locally; **confirm on Actions** |
| F-002 | P1 | Runway "Unlimited — 1 Month" ৳15,990 is still in the pricing policy/raw catalog although Runway ended new Unlimited sales 2026-06-01. The public page is disabled by `runway_cohort.py`, but the SSOT still lists it. | `runway_cohort.py` text; `catalog.json` | CEO | Open — remove from policy or confirm a real fulfilment path |
| F-003 | P1 | Canva block hard-codes "US$180/year" while `design_cohort.py` notes sources conflict ($144 vs $180). | `design_cohort.py` lines ~68–81 | Claude+CEO | Open — verify on canva.com, then fix text |
| F-004 | P1 | Google AI Pro ৳3,390 > Google's own ৳2,500. Customer-facing copy must justify honestly. | decision above | CEO | Risk accepted; copy review pending |
| F-005 | P1 | `SYSmoAI-Stack/AGENTS.md` banned-claims grep lists bKash/Nagad/Wise/Payoneer/Stripe, but SaveOnSub copy relies on bKash/Nagad. Stack rule and store reality conflict. Also says SaveOnSub deploys to "GH Pages" while the intended host is Cloudflare. | AGENTS.md vs site copy | CEO | Open — needs ruling |
| F-006 | P1 | PR #65 audit. Confirmed in code and fixed on PR #67: unsafe transitions, payment_confirmed without provenance, claim starting fulfilment on unpaid orders, PII/event leakage, read-then-write races, raw exception text. Catalog and media APIs reviewed: no confirmed defects. #65 itself is red only because its provider facts are 25 days old (same on `main`); #66 refreshes them. | PR #65, #67 | Claude | Fixed on #67 (draft, not merged) |
| F-007 | P2 | Obsolete `Vercel` status check fails on every PR ("deployment blocked"). Cloudflare is the host. | PR checks | CEO | Open — decide whether to remove the Vercel integration; do not weaken `full-regression` |
| F-008 | P2 | 12 open PRs, several stale (#45–#53, #59, #64). | `gh pr list` | CEO | Triage after #66/#65 |
| F-009 | P2 | Legacy `build_all.sh`/`build_catalog.py`/`build_assets.py` crash or would overwrite approved branding. | local run | Claude | Open — delete or guard |
| F-010 | P2 | Local Python 3.14 vs CI 3.12. | env | Claude | Watch |
| F-012 | P0 for any production use of #65 | Status: transitions and payment proof FIXED on #67. Still open: staff-ui hosting, `./functions` bundled onto the canonical host, deploy credential. Original text, per #65's description: owner/manager `canTransition` allows any transition incl. leaving terminal states like `refunded`; `payment_confirmed` has no payment-provenance record; `staff-ui/` needs its own Access-protected Pages project + staging D1/private R2; `wrangler pages deploy _site` from repo root would bundle `./functions` onto the canonical host; canonical deploy credential fails and the workflow falls back to global-key/deploy-hook secrets (should be one scoped Pages token). Not verified by this session yet. | PR #65 body | Claude+CEO | Open — verify in code, then fix on #65's branch only |
| F-011 | P2 | Hard-coded `data-entertainment-facts` date in the workflow means every fact refresh breaks the gate. | quality-gates.yml | Claude | Open — read the date from the facts file |

| F-013 | P1 | `main` has **no branch protection and no rulesets**, so the Quality Gates are advisory: anything can be pushed to `main`, which Vercel auto-deploys and the Cloudflare workflow can publish. | `gh api .../branches/main/protection` = 404; rulesets `[]` | CEO | Open. Recommend: require PR + `full-regression`, block force-push on `main` (admin action; not changed by Claude) |
| F-014 | P1 | The repo is **public**, and review branches pushed in this engagement (history of #66 incl. commit `9b387d2`, and the first commit of #67) contained purchase-cost and margin arithmetic. `AGENTS.md` forbids that here. The tip of #67 is redacted and `main` never had it, but branch history still holds it. Not on the live site (checked `catalog.js` and `_site`). | git history | CEO | Open. Best fix: make the repo private. Also squash-merge #66/#67 so `main` history never carries it. No force-push was done. |
| F-015 | P2 | Vercel is still connected and auto-deploys `main` to its own aliases; its account is blocked, so every PR shows a failing `Vercel` status. Cloudflare is production. Not a required check (no protection exists). | AGENTS.md; PR checks | CEO | Open. Remove the Vercel GitHub app/project (admin) and `vercel.json`; do not touch `full-regression` |
| F-016 | P2 | Provider-fact freshness fails after 14 days, so `main` and every PR go red again around 2026-11-06 unless facts are re-verified from official sources. | `provider_fact_freshness.py` | Claude+CEO | Open. Schedule re-verification; never just bump dates |
| F-017 | P2 | Policy unrecorded: may `support` (Ripon) mark support cases `completed`; may payment verification be delegated; role rows for Emon/Ripon in D1. Least privilege applied. | ARCHITECTURE.md | CEO | Open |

## Task ledger

| ID | Task | State |
|---|---|---|
| T-01 | Recover repo state, snapshot WIP | Done |
| T-02 | Fix audit crash + build pipeline | Done (local) |
| T-03 | Reconcile gate with CEO price decisions | Done (local) |
| T-04 | Push + confirm Actions green | Done — run 39894150661 success |
| T-05 | Audit + fix PR #65 security | **Done on PR #67** (draft, not merged), Actions green. Awaiting CEO review. |
| T-06 | Cloudflare preview deploy + browser smoke test (home, critical product pages, WhatsApp encoding, checkout, mobile, branding) | Not started — needs verified wrangler/Cloudflare access |
| T-07 | Per-SKU commercial validation (72 SKUs: provider terms, cost, FX, margin vs ৳500) | Not started — evidence-based, no invented costs |
| T-08 | SEO/Core Web Vitals baseline + Search Console plan | Not started |
| T-09 | Deployment hardening review | Recorded as F-013, F-014, F-015 and the process below; actions need CEO/admin |
| T-10 | Resolve F-002, F-003, F-005, F-014, F-017 with CEO | Waiting on CEO |

## Exact next action

```
cd C:\Users\emonh\SYSmoAI-Stack\apps\saveonsub-store-pr65
git status -sb && gh run list --branch fix/sos-staff-admin-security-2026-10-23 --limit 3
```
T-06 (private staging) needs from the CEO: a scoped Cloudflare Pages API token, a separate Pages project for `staff-ui/` behind Access, a staging D1 + private R2, and Access `TEAM_DOMAIN`/`POLICY_AUD`. Run `wrangler whoami` first; do not assume access. No staging was created.
Without credentials, T-07 (commercial audit) and T-08 (SEO) can proceed.

### Recommended release process (T-09)
Protect `main` (PR + `full-regression` required, no force-push, no direct push). Deploy to Cloudflare Pages from GitHub Actions only, with one scoped Pages token (no global API key, no deploy-hook fallback), deploy only `_site/`, smoke-test `saveonsub.com`, and record the previous deployment id for rollback. Staff API/UI on a separate Access-protected Pages project, never the canonical host. Remove Vercel.

## Approvals still required from CEO

- Production merge/deploy of anything (explicit authorization needed; none given).
- F-002 (Runway Unlimited), F-005 (payment-rail wording rule), F-013 (protect `main`), F-014 (repo privacy), F-015 (Vercel), F-017 (role policy).
- Any change to approved prices.

## Do not

Force-push, reset, delete branches/stashes, commit `.claude/`, `CLAUDE.md` (local graphify config), `.wrangler/`, secrets or
customer data, redraw the approved logo, or run `build_assets.py`.
