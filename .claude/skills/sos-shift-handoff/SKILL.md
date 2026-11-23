---
name: sos-shift-handoff
description: Use at the end of a work session to produce a short, non-sensitive Bangla handoff for the other person (Emon or Ripon) with task IDs, evidence links, blockers and the exact decision needed.
---
# sos-shift-handoff
Format, one line per item, in Bangla (technical terms in English):
`DATE/TIME_DHAKA | ACTOR (human+AI) | TASK_ID | WORK_ACTUALLY_DONE | EVIDENCE_LINK | BLOCKER | EMON_APPROVAL_NEEDED | NEXT_OWNER | STATUS`

Rules:
- Only things actually done and verified. Drafts are labelled DRAFT; untested is NOT_TESTED.
- No customer name/phone/email, no payment details, no credentials, no finance figures.
- Procedural rehearsals are labelled PASS_PROCEDURAL, never "enforced".
- End with the top 3 next actions and who owns each.
