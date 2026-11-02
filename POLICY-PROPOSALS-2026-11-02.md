# Policy and copy proposals (2026-11-02): NOT APPLIED, CEO review required

Nothing in this file changes the live site. Each item quotes the exact current text found in this branch's source and staged `_site/` output, and the proposed replacement. Commercial terms (refund timing, warranty, renewal) apply to future orders only once the CEO approves them.

## P-01 Privacy: unconditional shared-plan claim (truth risk, highest priority)

- Where: `privacy.html` line 70 (generator `build_trust.py`); also present in staged `_site/privacy.html`.
- Current: "On shared subscriptions, other seat-holders can never see your usage: ChatGPT chats, Midjourney galleries (private mode), Spotify listening (family slots are separate accounts) are all per-user private."
- Problem: unconditional ("can never see"). The FAQ and product pages acknowledge that what other seat-holders can see depends on the access method. A shared login is not the same as a provider-supported team seat.
- Proposed (kit WEBSITE_FIX_PACK WEB-01a): "On shared plans, other seat-holders may be able to see chats, files, history or settings, depending on the product. Do not enter personal, financial or confidential information on a shared plan. The known risk for each product is stated on its page. If privacy matters, choose a personal plan."
- Bangla version: needs a native-speaker pass before publishing.

## P-02 Refund timing (commercial)

- Where: `refund.html` table rows: "Same day, to your bKash/Nagad", "Same day", "Within 1 hour".
- Conflict: `/warranty` says timing can vary.
- Proposed: "Refund timing depends on the case and is confirmed in writing for your order." Keep the eligibility rows unchanged.

## P-03 Renewal reminder (operational promise)

- Where: `privacy.html`: "renewal reminder 3 days before expiry".
- Keep only if operations confirm reminders are actually sent. Otherwise: "We may send a renewal reminder."

## P-04 Terms §3 shared seats vs provider terms (legal)

Per-SKU legal review needed. Provider-supported team/family seats and unsupported credential sharing must not be described the same way. No copy proposed.

## Safe copy items (kit WEB-05..08), proposed for a later copy PR

- WEB-05 `/warranty`: title "Support terms | SaveOnSub", H1 "Support terms by product".
- WEB-06 `/terms` §1: "SaveOnSub is an independent subscription reseller and activation service based in Dhaka, Bangladesh."
- WEB-07 footer: current source reads "© 2026 SAVEONSUB. … independent reseller/activation service". The empty "· ." reported on the live site was not found in this branch's build.
- WEB-08: running text "SaveOnSub" (not "SAVEONSUB"); titles "… | SaveOnSub".

## Already resolved on current main (verified in this branch's build)

- WEB-09 `/all` counts: chips are generated from `CATALOG.categories` and include Gaming and BD Lifestyle. Browser check: "All (62)" grid cards + 10 bundle cards = 72 catalog products. The live-site mismatch the kit reported came from an older deployment.
