# SaveOnSub — Founder-Confirmed Renewal & Support Safety Workflow

**CEO fact:** 2026-11-11 (Asia/Dhaka).  
**Scope:** SaveOnSub only. **DRAFT, SOURCE ONLY, not merged/deployed, not a live reminder system.**  
**Depends on:** Current main Order OS, private staff authentication, prior payment evidence SOP in draft PR #124.

## 1. What EMON actually does today

EMON says he currently checks the subscription expiry through **the WhatsApp customer conversation or his own notes**. That is the authoritative founder description of the present workflow. It does NOT prove that each written date was independently verified on the provider dashboard or that there is a complete CRM, provider integration, or automatic consent to contact a customer. Keep the original chats in their authorized channel unless a separate privacy-controlled import is approved.

Do not claim automatic renewal operations are live.

## 2. Decision rule: separating remembered and confirmed expiry

| Expiry source | Storage label | Renewal queue classification | Allowed action |
|---|---|---|---|
| Original chat / WhatsApp conversation | `whatsapp_note` | `needs_review` | Private manual audit of source; do not state date as confirmed |
| Owner's notes | `manual_note` | `needs_review` | Manual review; ask customer or verify via provider if warranted |
| No recorded evidence / legacy record | `unknown` | `needs_review` | Recover actual service period; no asserted date |
| Independently verified provider dashboard | `provider_dashboard` + private evidence pointer | `provider_confirmed` | Plan renewal, but still no contact without separate consent |
| Independently verified provider confirmation | `provider_confirmation` + private evidence pointer | `provider_confirmed` | Plan renewal, but still no contact without separate consent |

**Important:** A WhatsApp screenshot showing a claimed expiry is NOT sufficient for provider confirmation by itself. EMON must independently verify from the authorized provider/account or suitable authoritative evidence. The private reference is an operator attestation pointer, not proof that the backend queried the provider; verifying the referenced object's existence and authenticity remains an acceptance gate.

## 3. Minimal source-only code changes in this branch

- `service-period.ts` now accepts `expiry_source` (defaults to `unknown` so older clients cannot become verified accidentally). To mark `provider_dashboard` or `provider_confirmation`, only `owner` may submit a syntactically valid `r2:sos/private/...` evidence pointer. Provider checks remain a human responsibility.
- The API records the source, verified flag and private evidence pointer in the existing append-only `service_period_set` audit event. No new database or migration; historical events lacking provenance remain unverified. Raw WhatsApp chats, screenshots, phone numbers, OTPs and credentials are never captured by this endpoint.
- `GET /api/ops/renewals` uses the **most recent** `service_period_set` event and matches its dates to the current service-period row. If the event is missing, legacy, unverified or no longer matches the dates, the record appears in `needs_review`, not `renewals`.
- Both response lists intentionally exclude customer name, phone and email. Every returned record has `outreach_allowed:false` and `renewal_contact_consent:not_verified`. This is a staff *review list*, NOT an outbound sending list. This intentionally changes the old API response contract: update any staff clients and test compatibility before staging.
- Expiry date could be valid yet customer marketing consent absent. An additional consent workflow, safe contact retrieval, recipient approval and duplicate-send prevention are required before messages can be automated.

## 4. Manual renewal and support operating procedure — effective as CEO guidance now

**Case A — customer asks about expiry or renewal:**
1. Find original SaveOnSub WhatsApp conversation or notes, minimally identify the product and customer/order alias.
2. Review last activation/delivery record. Separate the original quote, payment screenshot and provider service term.
3. Check provider-permitted account/service status independently whenever possible. If verified, record start/end date and source privately; if not, mark `needs_review`. No fabricated 30-day assumption.
4. Reply to inbound support with what is known and what is pending. Do not falsely state a guaranteed expiry.
5. Before any promotional renewal reminder, verify the customer's channel-specific consent, approved offer and current eligibility. No auto send or scheduled job is created by this PR.

**Case B — customer reports lost access or activation failure:**
1. Create/reconcile a support case associated with an existing SaveOnSub order ID **if it exists**. If not, create a minimal private lead/case under authorized data policy. Avoid creating fictitious paid orders.
2. Categorize `activation_failure`, `access_issue`, `plan_question`, `expiry_dispute`, `refund_request` or `other`, assign urgency and responsible human.
3. Preserve a redacted summary, customer-reported issue, conversation locator and timestamps in an access-controlled system; do not paste entire chats or password/OTP details into AI memory or public documentation.
4. Check paid status from owner-verified receiving account evidence. Check service dates separately. If provider access is unauthorized, escalate to CEO: do not attempt credential sharing workarounds.
5. Document follow-up due time, customer update, resolution and refund/replacement decision. Never promise refund/replacement unless confirmed under approved policy.

**Case C — subscription is ending soon:**
1. Show internal provider-confirmed due worklist alongside `needs_review` items; owner checks exceptions.
2. Owner verifies renewal eligibility, authorized provider plan, approved price, service expiry and opt-in consent.
3. Only a verified approved message template in an authorized channel may be sent by an approved human or future bounded messaging integration.
4. Record customer's response, new verified payment (never a screenshot alone) and new provider-confirmed service period if purchased; do not overwrite history without the audit event.

## 5. Existing infrastructure and unsupported claims

- Existing `support_threads` / `support_events` tables appear in source schema. Live support-ticket creation, WhatsApp integration, and real populated support records have NOT been verified.
- Existing Business OS `business_records` supports lead/task/expense/price_review; this does not by itself establish a complete support-ticket UI or inbox.
- Existing `staff-ui/orders.*` offers protected order work; current expiry evidence form UI has not been updated by this branch. Human-only/manual procedure applies until staff UI and role tests pass.
- No new D1 migration is required for this proposed source change; still must verify authentic Access sessions, PII boundaries, concurrent writes, notification delivery and date semantics in staging.

## 6. Regression/acceptance checks before approval

- [ ] Historic legacy service periods go to `needs_review`, no contact fields.
- [ ] WhatsApp/manual/unknown sources never become provider-confirmed from date alone.
- [ ] Only owner can attest provider confirmation with private evidence ref; rejected fields create no side effects.
- [ ] Same dates re-saved as manual notes invalidate prior provider-confirmed status.
- [ ] Renewal API excludes expired/cancelled/refunded records per defined window; respects fulfillment assignment scopes.
- [ ] Support/viewer roles cannot access the renewal worklist.
- [ ] No customer phone/name/email present in API response without consent workflow.
- [ ] No automation, marketing send or expiry guarantee is activated by enabling the review endpoint.
- [ ] Synthetic tests, CI, staff-browser staging, rollback and full cloud release authorization must pass separately.

## 7. CEO next fact to reconcile

When EMON writes an expiry date in WhatsApp or personal notes, was the date **copied from the provider's displayed end date**, or **calculated from activation/purchase date and nominal duration**, or is it a mix by product? Collect one answer without customer IDs, logins, screenshots, OTPs or account secrets.

## Release authority

**No merge, no deployment, no live pricing/content/permission changes, no customer data import, no real messages, no schema change, and no automatic subscription actions** from this draft. Approval requires exact reviewed SHA, passing synthetic CI and acceptance tests, a staging source-to-deploy parity check, support/consent review, release rollback and explicit CEO decision.
