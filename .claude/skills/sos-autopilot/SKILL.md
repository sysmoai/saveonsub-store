---
name: sos-autopilot
description: Set up and operate a persistent, scheduled, evidence-first Claude Code growth program for the existing SaveOnSub store. Use for unattended local-PC engineering cycles, separate cloud monitoring, GSC/GA4/merchant SEO triage, high-intent buyer acquisition, safe PRs, continuous QA, reliable checkpoint handoffs and automation scheduling without duplicating work or bypassing business governance.
---

# SaveOnSub — Persistent Autonomous Growth Controller

This skill is a **control plane**, not a blanket permission grant. Primary goal: grow qualified nonbranded discovery, conversion to real paid orders, and sustainable profitability for https://saveonsub.com by repeatedly shipping evidenced, reversible, tested changes in the **existing** `sysmoai/saveonsub-store` repository.

**Act now**, rather than answering with a theoretical plan. Reuse existing project code and operational records. No private data in this public repository. User wants minimal repetitive prompting, but actual local scheduling/cloud routines need accessible authenticated tools and must be verified after configuration.

## Mandatory reads

1. Read root `AGENTS.md`, `CLAUDE.md`, `DEPLOY.md` and current authoritative commercial/brand protection scripts.
2. Read [references/BOOTSTRAP.md](references/BOOTSTRAP.md) to discover scheduling tools, install **one** suitable persistent automation arrangement and verify it.
3. Read [references/SCHEDULE.md](references/SCHEDULE.md) for exact Asia/Dhaka routine names, schedules, lock/isolation design and watchdog.
4. Read [references/WORKSTREAMS.md](references/WORKSTREAMS.md) for current priority lanes, acceptance criteria, research, SEO, CRO, merchant listings, GA4, engineering and QA.
5. Read [references/GOVERNANCE.md](references/GOVERNANCE.md) before any write, third-party connection, CI, PR, deployment or communication.

When the separate `/sos-growth` skill from PR #207 is installed, load it as supplementary guidance, but **do not depend on that draft PR being merged**; this skill must work from `main` plus its own files.

## First execution sequence

1. Identify exact repo and current branch. Do not switch or reset an active human/agent checkout. Create an isolated worktree for changes. Confirm `origin`, `origin/main` SHA, `gh pr list`, open PRs and CI; do not trust historical checkpoint state.
2. Discover `claude --version`, `claude auth status` (never expose tokens), installed Desktop vs CLI vs cloud routines, `claude mcp list`, provider-authenticated Chrome, GitHub/GSC/GA4/Bing/Cloudflare capabilities, and existing scheduled tasks. Verify actual availability before claiming access. Do not install paid products, modify access rules or bypass authentication.
3. Use the following deployment-safe scheduling preference:
   - For **local files + Chrome**, use Claude Desktop's native **Local Scheduled Tasks**, selecting the SaveOnSub working folder and **isolated worktree**. Claude Desktop must be running and computer awake to execute. This is independent of a persistent chat session.
   - For PC-off **read-only research/review** use Claude Code **Cloud Routines** (if enabled), with tightly scoped SaveOnSub GitHub repo and connectors. They work from a fresh cloud clone and cannot access local files or local Chrome sessions.
   - If Desktop schedules are unavailable but CLI works, use the official non-interactive `claude -p` with a **carefully reviewed Windows Task Scheduler** wrapper, separated from existing checkouts. Run dry-run/synthetic tests before activating. Use `--permission-mode auto` if supported, never `--dangerously-skip-permissions`. Failing tool permissions are blockers, not a reason to circumvent safeguards.
   - `/loop` is suitable only for a temporary open-session task (recurring session tasks expire after 7 days), **not** the primary persistent scheduler.
4. Build exactly the runnable, deduplicated schedule in SCHEDULE.md using the already available mechanism. If it cannot be created, record the precise installation/auth blocker and produce an actionable setup packet; do not pretend it is running.
5. Launch one **safe, immediately useful** task in the current session: review the GSC Merchant listings invalid items and validate actual non-brand opportunity pages or GA4 instrumentation, prioritizing verified business impact. Use dated source evidence and preserve commerce HOLDs.
6. Run tests; create a focused reviewable PR only when justified; record changed files, URLs, exact SHA, CI, source dates, permissions used, blocked actions, and next unblocked work.
7. At session end update existing accurate checkpoint/task records, not stale reports, and leave a resumption packet. Reconcile fresh Git/PR/CI/live truth on every new run.

## Execution contract

- Each scheduled run should produce **one independently useful unit of verified work**, or a clearly evidenced BLOCKED result and proceed to another authorized task, rather than merely reporting status.
- Workstreams: PROTECT → MEASURE → FIX → ENRICH → TEST → REVIEW → REPEAT.
- Prefer page cohorts already earning credible impressions or qualified leads; prioritize product truth, mobile conversion and search quality over publishing large numbers of speculative pages.
- Share an exact status: `SCHEDULED_VERIFIED`, `WORK_DONE_TESTED`, `PR_READY`, `BLOCKED_NEEDS_APPROVAL`, `UNKNOWN`. Never call draft work live.
- Don't repeatedly contact the CEO about routine decisions; respect the small set of real hard stops in GOVERNANCE.md.
- There is no unlimited context, guaranteed ranking, unlimited usage, PC wakefulness, or actual background execution without a real scheduler. Achieve continuity through verified code, tests, repository state, and durable checkpoints, not model memory.

**Immediate operator direction:** If the requester asks to “do everything,” interpret it as permission for safe research, local reversible development and reviewable PR preparation; not as permission for production release, financial actions, provider-account access, disallowed shared offers, private exports or unrestricted publishing.
