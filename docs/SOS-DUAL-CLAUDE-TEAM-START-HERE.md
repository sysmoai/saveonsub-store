# SaveOnSub — Emon + Ripon: One Repo, Two Claude Accounts
Status: DRAFT ONBOARDING; not permission grant, production launch or payment authorization.
Date: 2026-11-23. Canonical website: https://saveonsub.com. Code repo: https://github.com/sysmoai/saveonsub-store.

## Why this is simpler
The existing root CLAUDE.md imports AGENTS.md. The additional .claude/rules/sos-team-operating-model.md is a concise common rule loaded by Claude Code on both machines after this PR is APPROVED AND MERGED, rather than manually pasting a massive master prompt every day. A read-only independent QA subagent is also shared. Do not replace the existing business repo, current operator register, private finance or live site.

## Minimum human setup (each user once)
Emon:
1. Continue using his current authorized Windows/WSL Claude Code installation and existing local SaveOnSub clone. Verify own Claude and GitHub identities and do not overwrite worktree.
2. Review this PR and its effects. Only after exact approval/merge, git fetch/pull the approved branch at a clean safe state.
3. Start Claude Code at repo root, confirm that the root CLAUDE.md and .claude/rules/sos-team-operating-model.md load. Ask Claude to audit role/access and current repo/live site before edits.

Ripon:
1. Use his OWN MacBook OS user and Claude subscription. Verify Claude Code actually installed and authenticated; never sign in as Emon.
2. With permission, clone the canonical repo (or reuse existing checked-out copy). If the repo is public, clone alone does not grant write access, Drive access or private CRM access.
3. After reviewed rules land, start Claude Code at repo root. Ask for a role-scoped SaveOnSub Operations/UAT session, not unrestricted billing or admin privileges.
4. Open the already-existing authorized Operator Work Register with his Google account on MacBook and iPhone 13. Test only the approved synthetic QA_SANDBOX row; Emon confirms the same update.
5. For business data use a unique SOS task/order ID in the private operator register, not a Git commit. Redact screenshots for code review.

## The five-minute daily routine
- Ripon: Check permitted pending orders, unanswered leads and support; record update in private CRM with exact owner and next action; ask Claude for approved reply/content drafts; perform Mac/iPhone UAT on staging changes.
- Emon: Review escalations, provider rights and finance/settlements privately; own code review, security gates, release readiness and measured SEO priorities.
- Each Claude: Read current repo and relevant source, avoid duplicating an existing PR, complete a scoped change, record a short safe handoff and link evidence.
- Work can continue asynchronously via GitHub branches and the private operator register. CLAUDE.md or project sharing never synchronizes separate account chat memory.
- Run actual 24/7 automations only after secure hosted runtime, consent, cost control, alerting and human release approval are proven.

## Step-by-step acceptance test
- [ ] Emon and Ripon use distinct authenticated Claude identities.
- [ ] Each starts from a validated clone of sysmoai/saveonsub-store.
- [ ] Reviewed shared rule loads, existing CLAUDE.md and AGENTS.md preserved.
- [ ] Ripon's own approved Google identity can read/update only permitted operator data; CEO-only finance is denied.
- [ ] QA_SANDBOX synthetic update passes Mac -> Emon Windows -> Ripon iPhone 13, with timestamp and evidence.
- [ ] A draft task/PR links the originating task ID and safe tests; Ripon independently checks UI on Mac and iPhone if relevant.
- [ ] No production, money, pricing, sensitive data or permission change was made without scoped CEO approval.

## What this document cannot do
GitHub cannot create a Claude subscription, log Ripon into a Mac, invite Ripon's real Google/Cloudflare/WhatsApp identity, migrate private CRM, install an agent runtime or verify live site behavior by documenting it. Those need authenticated actions and logged acceptance tests.
