# Claude Code recovery state — SaveOnSub

Single handoff file for a fresh Claude Code session. Read this first, then `git log -10` and `gh pr list`.
Keep it current after every milestone. It records facts and decisions; it is not a plan to re-litigate.

## Checkpoint

| | |
|---|---|
| Written | 2026-10-23 09:16 (Bangladesh time) |
| Repo | `sysmoai/saveonsub-store` — local: `C:\Users\emonh\SYSmoAI-Stack\apps\saveonsub-store` |
| Branch | `review/sos-production-safety-2026-10-23` (PR #66, base `main`) |
| Merged-in state | `9b387d2` + remote `c9015e8` + `b963d3c` (CI recovery) + `ae76df9` (merge) |
| Pushed? | Yes. Head `900c215` pushed to origin (fast-forward, no force). |
| GitHub Actions | **`full-regression` run 39894150661 = success on `900c215`** (first green on this branch). The legacy `Vercel` status still fails (F-007). |
| Production deploy | **None from this work. Awaiting CEO authorization.** |
| Safety snapshot | `refs/backup/wip-20261023` (local only; pre-recovery uncommitted work) |

## Verified (actually run locally, Windows, Python 3.14; CI uses 3.12)

`check_prices.py`, `python -m unittest test_audit_home_prices`, `test_whatsapp_cta.py` (9/9), `audit_all.py` (0 gaps),
`deploy_preflight.py`, `build_site.py`, and the full "Verify governed pricing-v2 release boundary" step of
`quality-gates.yml` (extracted and run in bash) all exit 0 against a fresh `_site/`.

**Not yet verified:** any browser/staging check, live saveonsub.com, PR #65 admin security.

Run the CI sequence locally (delete `_site/` first, as CI has none when auditing):

```
python build_home.py && python build_pages.py      # generated root pages are tracked; regenerate after catalog changes
python -m unittest test_audit_home_prices && python test_whatsapp_cta.py
python check_prices.py && python audit_all.py && python deploy_preflight.py
python build_site.py
```

`build_all.sh` / `build_catalog.py` are legacy and crash on the v2 catalog (`KeyError: 'tos'`). Do not use them.
The pipeline of record is `build_site.py` (see `.github/workflows/quality-gates.yml`).

## CEO decisions on record (EMON HOSSAIN, 2026-10-23)

| SKU | Decision | Notes |
|---|---|---|
| ChatGPT Go | **Stay ৳1,299** | Documented exception to the ৳500 net-profit floor (~৳158 est. contribution at $8 anchor). Recorded in `ops/PRICING-V2-2026-09-17.json`. Engineering suggestion of ৳1,690 declined. |
| Google AI Pro | **Restore ৳3,390** | Risk accepted on record: Google bills Bangladesh directly at ৳2,500/mo (gemini.google/bd, 2026-10-23). Page must state access method honestly. |
| Netflix | Bangladesh-scoped tiers (Mobile 2.99 / Basic 3.99 / Standard 7.99 / Premium 9.99 USD) | Previous session corrected its own US-tier mistake from `netflix.com/bd`. Source not independently re-verified by this session. Needs a human spot-check. |

No other price was changed. Engineering recommendations are not CEO-approved prices.

## What was fixed (root causes)

1. `audit_all.py` `min()` on empty `plans[]` (run 39869844323). Resolved via `c9015e8`'s tested `audit_home_prices.py`.
2. Generated pages were stale/broken: `build_pages.py` crashed on the v2 catalog and truncated `p/chatgpt-plus.html` to 0 bytes (open-before-render). Fixed; inquiry-only pages carry `data-inquiry-only`.
3. Stage cohorts assumed full priced pages: `google_ai_cohort`, `design_cohort` (explicit inquiry path), `chatgpt_cohort` (shared label only if a shared plan exists), `runway_cohort` (plan renamed by Pricing V2; retired Unlimited plan must stay disabled).
4. Leftover "A SYSmoAI venture" footer branding removed; audit now fails if SYSmoAI appears in Organization schema.
5. Release gate contradicted committed decisions (Go, Google AI Pro, Netflix date) — gate and SSOT reconciled per the decisions above.

## Findings register

Priority: P0 release-blocking · P1 important · P2 improvement · P3 optional. Owner: CEO = needs Emon.

| ID | Pri | Finding | Evidence | Owner | Status |
|---|---|---|---|---|---|
| F-001 | P0 | `full-regression` red on PR #66 | run 39869844323; later c9015e8 run 39893629926 | Claude | Fixed locally; **confirm on Actions** |
| F-002 | P1 | Runway "Unlimited — 1 Month" ৳15,990 is still in the pricing policy/raw catalog although Runway ended new Unlimited sales 2026-06-01. The public page is disabled by `runway_cohort.py`, but the SSOT still lists it. | `runway_cohort.py` text; `catalog.json` | CEO | Open — remove from policy or confirm a real fulfilment path |
| F-003 | P1 | Canva block hard-codes "US$180/year" while `design_cohort.py` notes sources conflict ($144 vs $180). | `design_cohort.py` lines ~68–81 | Claude+CEO | Open — verify on canva.com, then fix text |
| F-004 | P1 | Google AI Pro ৳3,390 > Google's own ৳2,500. Customer-facing copy must justify honestly. | decision above | CEO | Risk accepted; copy review pending |
| F-005 | P1 | `SYSmoAI-Stack/AGENTS.md` banned-claims grep lists bKash/Nagad/Wise/Payoneer/Stripe, but SaveOnSub copy relies on bKash/Nagad. Stack rule and store reality conflict. Also says SaveOnSub deploys to "GH Pages" while the intended host is Cloudflare. | AGENTS.md vs site copy | CEO | Open — needs ruling |
| F-006 | P1 | PR #65 (staff admin, 49 files, +2813/-130; `functions/api/ops/*`, `functions/lib/order-os/*`, `staff-ui/`, D1 schema) not audited; its `full-regression` is red. Its own description lists unresolved items (F-012). | PR #65 | Claude | **Next major task** |
| F-007 | P2 | Obsolete `Vercel` status check fails on every PR ("deployment blocked"). Cloudflare is the host. | PR checks | CEO | Open — decide whether to remove the Vercel integration; do not weaken `full-regression` |
| F-008 | P2 | 12 open PRs, several stale (#45–#53, #59, #64). | `gh pr list` | CEO | Triage after #66/#65 |
| F-009 | P2 | Legacy `build_all.sh`/`build_catalog.py`/`build_assets.py` crash or would overwrite approved branding. | local run | Claude | Open — delete or guard |
| F-010 | P2 | Local Python 3.14 vs CI 3.12. | env | Claude | Watch |
| F-012 | P0 for any production use of #65 | Per #65's own description: owner/manager `canTransition` allows any transition incl. leaving terminal states like `refunded`; `payment_confirmed` has no payment-provenance record; `staff-ui/` needs its own Access-protected Pages project + staging D1/private R2; `wrangler pages deploy _site` from repo root would bundle `./functions` onto the canonical host; canonical deploy credential fails and the workflow falls back to global-key/deploy-hook secrets (should be one scoped Pages token). Not verified by this session yet. | PR #65 body | Claude+CEO | Open — verify in code, then fix on #65's branch only |
| F-011 | P2 | Hard-coded `data-entertainment-facts` date in the workflow means every fact refresh breaks the gate. | quality-gates.yml | Claude | Open — read the date from the facts file |

## Task ledger

| ID | Task | State |
|---|---|---|
| T-01 | Recover repo state, snapshot WIP | Done |
| T-02 | Fix audit crash + build pipeline | Done (local) |
| T-03 | Reconcile gate with CEO price decisions | Done (local) |
| T-04 | Push + confirm Actions green | Done — run 39894150661 success |
| T-05 | Audit PR #65 (authn/authz, role boundaries, public-artifact boundary, PII) with synthetic accounts | **In progress** — read-only recon done (file list + PR description); code review not started |
| T-06 | Cloudflare preview deploy + browser smoke test (home, critical product pages, WhatsApp encoding, checkout, mobile, branding) | Not started — needs verified wrangler/Cloudflare access |
| T-07 | Per-SKU commercial validation (72 SKUs: provider terms, cost, FX, margin vs ৳500) | Not started — evidence-based, no invented costs |
| T-08 | SEO/Core Web Vitals baseline + Search Console plan | Not started |
| T-09 | Resolve F-002, F-003, F-005 with CEO | Waiting on CEO |

## Exact next action

```
git status -sb && gh run list --branch review/sos-production-safety-2026-10-23 --limit 3
```
The newest run is green (see above) → continue T-05 (`gh pr checkout 65`, read `git diff main...HEAD --stat`, audit auth/role code first).
If red → `gh run view <id> --log-failed`, reproduce locally with the sequence above, fix root cause.

## Approvals still required from CEO

- Production merge/deploy of anything (explicit authorization needed; none given).
- F-002 (Runway Unlimited), F-005 (payment-rail wording rule), F-007 (Vercel).
- Any change to approved prices.

## Do not

Force-push, reset, delete branches/stashes, commit `.claude/`, `CLAUDE.md` (local graphify config), `.wrangler/`, secrets or
customer data, redraw the approved logo, or run `build_assets.py`.
