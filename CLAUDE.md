# SaveOnSub — Claude Code session start

`AGENTS.md` is the production authority; this file only says how to resume.

1. Read `ops/seo/control/checkpoint.md` (compact handoff) and `state.json`.
2. `git status`, branch, `git log -1`; compare with `state.json`.
3. Take the top unblocked item in `ops/seo/control/tasks.jsonl`; read only files it names.
4. Build with `python build_site.py` (never a legacy generator). The last step,
   `catalog_reconcile.py`, proves pricebook == catalog.js == EN/BN pages == WhatsApp prefill.
5. Update checkpoint/state/tasks with the delta before ending.

Hard limits: no merge, deploy, DNS, live price, payment or spend change without a
separate explicit CEO approval of that action. Never commit secrets, customer data,
supplier/cost data or provider-rights notes (this repository is public).
Keep AIPS (`aips-*`) isolated and inquiry-only.
