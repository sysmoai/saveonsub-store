# SaveOnSub continuous operating schedule — Asia/Dhaka

**Target timezone:** Asia/Dhaka (UTC+06:00); verify actual host timezone and daylight behavior before scheduling. Schedules are recommendations to implement only once, with explicit owner and deduplication. Actual recurrence must be established in Desktop / Cloud Routines / Task Scheduler; writing this document does not schedule anything.

## Scheduled job matrix
- **SOS-GROWTH-MORNING** — Daily at 08:00 Dhaka: ingest current GSC and available GA4, recent CI/open PRs, conversion errors, customer journey, query movement. Produce an evidence-backed decision queue; execute one safe small fix where possible.
- **SOS-BUILD-AFTERNOON** — Daily at 14:00 Dhaka: independently pick highest expected-value approved code/SEO/CRO fix; work in isolated branch/worktree, run tests and prepare a PR. Avoid overlapping unresolved work in existing PRs.
- **SOS-QA-EVENING** — Daily at 20:00 Dhaka: inspect pending branches/PRs and CI, independent regression checks, canonical site smoke, build/source consistency, changed URL checks and approval blockers; do not deploy.
- **SOS-FACTS** — Monday and Thursday at 09:00 Dhaka: verify due provider-fact cohorts against official pages (all relevant fields; real source evidence, unverified exceptions), starting early enough to avoid 14-day freshness gate expiry. Never advance dates on inaccessible sources. This recurring job may prepare safe PRs but never update commercial offers without approval.
- **SOS-SEO-WEEKLY** — Every Sunday at 10:00 Dhaka: full GSC keyword/canonical/locale audit, search intent mapping, prioritize impression-bearing non-brand pages, merchant listing errors, source-grounded content enhancements, technical regressions, indexation. Run safe bounded changes.
- **SOS-CEO-BRIEF** — Every Friday at 18:00 Dhaka: summarize verified traffic, leads, confirmed paid outcomes, PR and release status, decisions/approval blockers, next week's top ROI work. If finance inaccessible, mark unknown instead of guessing.

If the scheduling platform cannot express Monday+Thursday in one recurring rule, create two separately named unique jobs or use a supported scheduler with weekday cron. Do not duplicate schedules across Desktop, Cloud and Windows for the same task.

## Contention / concurrency
- Maximum **one writer** touching SaveOnSub working copy or the same Git branch at a time. Research jobs may run concurrently only when tools/quotas and source isolation allow it.
- Give every run a unique ID, timestamp, branch/worktree, task ID, exact origin/main SHA, owner and lock key; check an active job lease and do not steal another running job's work. Use Windows OS-level process lock if implementing native Task Scheduler.
- Every run must inspect active PRs before creating another PR. Prefer updating a relevant approved work branch only when authorized.
- Budget wall-clock time and API/token use; a scheduled job can end with a reliable handoff and continue in next run. No infinite loops, forced retries or context exhaustion promises.
- Detect laptop sleep, disconnected browser, missing cloud connectors, token expiration and offline host as operational blockers. Schedule missed-run recovery rather than pretending execution occurred.
- Retries: at most 2 retries for transient network failures with backoff; never auto-retry permission denial, forbidden provider content, failing business gate, cost approval or production deploy. Avoid cron storms.
- All private raw logs remain outside public Git; sanitized checkpoints reference commits, tests and task IDs. Prevent accidental publishing of chat transcripts or auth tokens.

## Shared run contract
At start: inspect root instructions; fresh Git/PR/CI/live evidence; identify priority, safe permissions and task owner.
During: small verified change or useful audit, independent QA, no unrelated modifications.
At finish: completed work, exact SHA, branch/PR, tests, source dates, changed URLs, GA4/GSC evidence, open blockers, next safe action, next schedule and whether triggered by Desktop/cloud/Windows.
If no work possible, report BLOCKED with exact missing capability and other safe investigation completed.
