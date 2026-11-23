# Automation bootstrap: inspect, select, configure, prove

## 1. Inspect live capabilities
From an isolated SOS worktree, execute read-only discovery appropriate for Windows PowerShell:
- `git status --short`, `git remote -v`, `git fetch --prune`, `git log -1 origin/main`, `gh pr list --repo sysmoai/saveonsub-store --state open`
- `claude --version`, `claude auth status` and `claude mcp list`; never reveal authentication tokens.
- Inspect Claude Desktop Local Scheduled Tasks, Cloud Routines eligibility and existing scheduler jobs to avoid duplicates.
- Verify connected capabilities for GitHub, authorized Chrome, GSC, GA4, Bing and Cloudflare and the correct SaveOnSub accounts. Do not assume all ChatGPT connectors are available in Claude.

## 2. Scheduling choices, in order
**Local Desktop Scheduled Tasks:** Best for authenticated PC/Chrome and local source. Create/choose a local schedule in Claude Desktop pointing to the verified SaveOnSub working folder and a dedicated isolated Git worktree, with descriptive names from SCHEDULE.md. Ensure Desktop is running and OS is awake for actual runs. It cannot run while the machine is off.

**Cloud Routines:** Prefer for PC-independent code review, GitHub work and read-only market scanning if the Claude account supports cloud routines. Must use a connected repository and available cloud connectors. No access to local browser profiles or private local working tree; verify exactly which remote MCP permissions are present. Never impersonate completion of local Chrome tasks.

**Windows Task Scheduler + Claude Code noninteractive CLI:** Fallback if native scheduling unavailable. Use actual installed CLI help to validate supported switches. Supported documented pattern: `claude -p "<task>" --output-format json` with narrowly selected `--allowedTools`, explicit project/worktree, safe permission mode and time/token/cost budgets. Never use `--dangerously-skip-permissions`, blanket network permissions or unrestricted tool approval. Only invoke from a reviewed local wrapper outside the public repo, with safe environment handling, process timeout, log redaction, non-overlapping lock and private state directory. Test as the exact Windows user/service account who will run it. Never put tokens or customer data into arguments, task descriptions or logs.

**Session /loop:** Only a short-lived supplement, not the persistent job engine; inspect expiry.

## 3. Mandatory activation tests
Before reporting ACTIVE:
1. Confirm schedule exists in the platform UI or scheduler, with the intended task text, working directory, local time zone and trigger.
2. Run one immediate manual invocation with minimal safe read-only task; check exact execution history and artifact.
3. Confirm can read current GitHub project and safely preserve other sessions' branch/worktree.
4. Confirm one instance only, safe time budget and retries without repeated identical PRs.
5. Confirm blocked permissions result in visible BLOCKED status rather than agent bypass.
6. Confirm logs/checkpoints are stored in an appropriate private location; public Git holds only sanitized durable code/task-state data.
7. Document time of last successful scheduler run and next trigger.

Never claim "24/7 enabled" until a real scheduler has been verified. If activation needs desktop UI interaction or credentials unavailable here, create a fully configured setup packet and mark NOT_ACTIVATED with precise missing step.

## 4. Safe handoff on startup failure
List failure reason, error class, attempted configuration, last known good SHA, affected scheduled job and recovery action. For repeated authentication failures, stop rather than hammer provider endpoints. For repeated CI failures, isolate and diagnose instead of re-running identical suites indefinitely. Keep rollback targets for any authorized production release separate from automation checkpoints.
