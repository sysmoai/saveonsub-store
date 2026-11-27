# SaveOnSub — Delivery, validation and session continuity

## Cold start
Confirm correct working tree, uncommitted changes and upstream. Read AGENTS.md, CLAUDE.md, README.md, DEPLOY.md and existing operations checkpoint/state/task register. Refresh origin/main, list open PRs and CI statuses, verify live Cloudflare production SHA and canonical pages, identify available authenticated MCP integrations and their scopes. Do not use stale checkpoint as current truth, leak secrets or replace other operator edits.

## Work queue
Compare PR #201, #202, #203, #204, #206 and all newly discovered PRs; dedupe work; evaluate existing fact freshness errors, Design cohort verification, historical test failures, shared-SKU HOLD gates, search/indexation gaps, and mobile sales friction. Choose one high-impact, safe, unblocked task. Use a feature branch or worktree. Document exact affected files/URLs, baseline, evidence, risk, owner, tests, approval dependencies. Implement, not just recommend.

## Engineering verification
Read the current repo workflow before running any commands. Known safe starting commands (adapt to current repo):
- python -m pip install -r requirements.txt
- python -m unittest discover -v -s tests -p 'test_*.py'
- python catalog_hold_gate.py
- python build_site.py
- python audit_commercial_truth_v2.py
- python audit_all.py
- python deploy_preflight.py
Use authoritative checks from the latest CI including exact restricted/shared SKU validation. Examine generated _site EN/BN pages, broken links, correct canonicals/hreflangs, indexability, accessibility, mobile UI, accurate WhatsApp prefill, privacy and source exclusion. Synthetic tests only for checkout; never imply a screenshot proves payment. Separate preexisting from newly introduced failures. Do not weaken gates or stamp unverified provider facts.

## Independent review
For meaningful changes request a second reviewer/subagent when available, focused on security, provider access truth, plan restrictions, mobile conversion, SEO no-regression, brand lock and deployment boundary. Review actual diffs and evidence. Open a small, well-scoped draft or normal PR in accordance with repo governance, report changes and missing approvals. Avoid duplicating existing PRs.

## Deployment boundary
The user's desire for autonomy authorizes normal safe analysis and development, not bypassing binding release-specific CEO approval. Never silently merge, deploy, modify live prices/payment/refund/legal terms, spend funds, contact customers, change DNS/permissions/secrets, run production DB migrations, export private data or enable prohibited offers. Keep protected actions BLOCKED pending exact authorization. If authorized, use exact approved 40-character main release SHA, authoritative canonical workflow, scoped Cloudflare project and rollback provenance. Publish only _site, never the repo root. Check actual saveonsub.com after release; CI green, Vercel READY, Cloudflare upload and canonical live are distinct states.

## State across sessions
Use existing ops/seo/control/checkpoint.md, state.json and tasks.jsonl only after checking against fresh origin/main/PR/CI/live state. Persist dated findings, working branch/PR, exact SHA, run commands and results, source links, verified blockers, owner/approval needs, and next safe task. Avoid private information in this public repo. On a new session recompute truth instead of blindly following historical state. There is no actual infinite context, unattended persistence or guaranteed scheduled execution from a prompt alone.

## Daily work loop
OBSERVE > VERIFY > PRIORITIZE > IMPLEMENT > TEST > REVIEW > CHECKPOINT > NEXT.
When blocked, name the narrow reason and continue independent safe work. Report VERIFIED DONE / IN REVIEW / BLOCKED / UNKNOWN with concrete evidence and links, not generic progress narration.
