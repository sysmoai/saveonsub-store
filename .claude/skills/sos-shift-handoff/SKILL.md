---
name: sos-shift-handoff
description: Use at the end of a work session to produce a short, non-sensitive Bangla handoff for the other person (Emon or Ripon) with task IDs, evidence links, blockers and the exact decision needed.
---
# sos-shift-handoff
Format, one line per item, in Bangla (technical terms in English):
`DATE/TIME_DHAKA | ACTOR (human+AI) | TASK_ID | WORK_ACTUALLY_DONE | EVIDENCE_LINK | BLOCKER | EMON_APPROVAL_NEEDED | NEXT_OWNER | STATUS`

Rules:
- Use the real Dhaka time (`HH:MM`); never leave the placeholder. TASK_ID is the SOS task/QA ID or the PR/branch name. Partial work is `PARTIAL`; a commit is `COMMITTED_NOT_MERGED`, not "verified".
- Only things actually done and verified. Drafts are labelled DRAFT; untested is NOT_TESTED.
- No customer name/phone/email, no payment details, no credentials, no finance figures.
- Procedural rehearsals are labelled PASS_PROCEDURAL, never "enforced".
- End with the top 3 next actions and who owns each.
