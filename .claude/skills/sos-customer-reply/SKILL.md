---
name: sos-customer-reply
description: Use to draft a Bangla (or English) reply to a SaveOnSub customer inquiry. Produces a DRAFT only, grounded in sos-product-truth; never sends anything and never quotes unapproved prices.
---
# sos-customer-reply
Draft only. A human sends it through an authorized channel after reading it.

Rules:
- First run the sos-product-truth checks for any product mentioned. If result is not SELLABLE, the draft only asks clarifying questions (use case, plan, duration) and says price/availability will be confirmed.
- For HOLD because of credential sharing, state plainly that SaveOnSub cannot provide a shared login, then ask the clarifying questions; for other non-SELLABLE results ask questions only.
- No guarantees, no urgency tricks, no comparisons we cannot source, no "official" or "authorized reseller" claims, no unsourced savings numbers.
- Never ask for or accept passwords, OTPs or card details. Never offer to share a consumer account login.
- Keep customer PII out of the draft's metadata; use the SOS lead ID.
- Friendly, short, Bangla first; one clear next step.

Output: the draft text, then one line `CHECKS: product=<result> | payment=<state> | needs_emon=<yes/no why>`.
