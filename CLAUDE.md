# SaveOnSub — Claude Code session start

@AGENTS.md

`AGENTS.md` (imported above) is the production authority; this file only says how to resume.
Checkpoint, `state.json` and `tasks.jsonl` are HISTORY until reconciled with live state.

1. `git fetch`, `git status`, branch, `git log -1 origin/main`, and list open PRs first. This is the current truth.
2. Read `ops/seo/control/checkpoint.md` and `state.json`; if their `main_sha`/date do not match step 1, treat them as stale
   history, say so, and update them (do not follow their task queue).
3. Take a task from `ops/seo/control/tasks.jsonl` only if it is still unblocked against step 1 (not already done in main
   or an open PR); read only files it names.
4. Build with `python build_site.py` (never a legacy generator). The last step,
   `catalog_reconcile.py`, proves pricebook == catalog.js == EN/BN pages == WhatsApp prefill.
5. Update checkpoint/state/tasks with the delta before ending.

Hard limits: no merge, deploy, DNS, live price, payment or spend change without a
separate explicit CEO approval of that action. Never commit secrets, customer data,
supplier/cost data or provider-rights notes (this repository is public).
Keep AIPS (`aips-*`) isolated and inquiry-only.
