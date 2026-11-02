# SaveOnSub Customer → Payment → Activation SOP
**Revision:** 2026-09-18  
**Operators:** Emon Hossain + Shorif Ahmmed Ripon  
**Applies to:** SaveOnSub only

## 1. Service model
SaveOnSub targets continuous human coverage through Emon + Ripon. This is a **24/7 coverage target**, not a promise that every message will receive an instantaneous reply. When Emon is unavailable, Ripon is authorized to qualify leads, quote approved prices, receive/verify payment, complete permitted activations and provide after-sales support.

Ripon may operate during his 8:00 AM–8:00 PM primary-office schedule when practical.

## 2. Official customer/payment channel
**WhatsApp:** +8801305869242 / 01305869242

Current local payment options using that number:
- bKash
- Nagad
- Rocket
- Upay

For high-value or business orders, direct bank payment should be preferred after the approved bank details are supplied privately to the customer.

Current use of personal MFS accounts is an operational transition risk at scale. SaveOnSub should migrate recurring business collection to suitable merchant/business payment arrangements as volume grows. Never split payments or structure transactions to evade provider/MFS limits or compliance controls.

## 3. Lead-handling sequence
### Step A — Respond
Acknowledge promptly and ask the minimum necessary question:
- What do you want to do?
- Which tool/plan are you considering?
- Personal/customer-specific or lower-cost multi-user option, if a provider-supported option exists?
- Required duration and deadline?

### Step B — Recommend, do not oversell
Explain the best-fit plan using verified facts. Personal/customer-specific access should be recommended for privacy-sensitive, professional, long-term or account-history-dependent use.

### Step C — Verify before quoting
Check the Product & Price Control:
- approved plan?
- current price?
- access type?
- provider rules?
- availability?
If not approved, research official sources and escalate when unclear.

### Step D — Send the pre-payment summary
Before payment, the customer must receive:
1. product + exact tier;
2. duration/billing unit;
3. access type/method;
4. final BDT price;
5. expected delivery window if one can be reliably stated;
6. key provider restrictions;
7. SaveOnSub refund/replacement/service-assurance summary;
8. payment instructions.

For dynamic products, state that the quote is time-limited and subject to checkout reconfirmation before purchase.

## 4. Payment control
1. Ask customer to send payment to the approved channel.
2. Obtain TxnID/reference and payer name/number as necessary for reconciliation.
3. Verify transaction in the actual payment account/app — **a screenshot alone is not proof of payment**.
4. Record the order and payment before activation.
5. Mark `PAID-VERIFIED`.
6. Never expose bank/card credentials, CVV, OTP, recovery codes or internal payment credentials to customers.
7. Never ask a customer to send their full card number/CVV/OTP.

### High-value flag
Until Emon sets a different threshold:
- orders **৳10,000+**, corporate/multi-seat orders, or unusual payment patterns should be flagged for bank-payment preference and an extra verification step;
- orders **৳25,000+** require Emon review before fulfillment unless a pre-approved B2B procedure applies.

## 5. Activation control
After `PAID-VERIFIED`:
1. Reconfirm exact tier and checkout amount.
2. Reconfirm provider terms/access method if anything changed.
3. Activate using the approved method.
4. Do not save customer passwords in the order log.
5. If temporary credential access is unavoidable, minimize exposure, do not reuse credentials, and instruct the customer to change/revoke access immediately after setup when technically appropriate.
6. Verify with the customer that the correct plan is active.
7. Record activation timestamp, expiry/renewal date and activation owner.
8. Send the customer a concise completion message with:
   - activated product/tier;
   - activation date;
   - expected renewal/expiry date;
   - access/support notes;
   - provider-policy reminder;
   - SaveOnSub support contact.

## 6. Provider billing and renewal
- Do not promise auto-renewal unless the exact renewal method is documented.
- Keep international payment/card controls disabled when not required by the operational payment method.
- Before a renewal, reconfirm provider price and customer consent.
- Send renewal reminders before expiry; do not renew a customer without authorization unless there is a clearly documented recurring arrangement.

## 7. Escalate to Emon immediately when
- product/tier is not in the approved register;
- provider terms or sharing/resale rules are unclear;
- customer requests a discount;
- expected profit falls below the approved floor;
- payment is suspicious or cannot be verified;
- customer requests an exception refund/compensation;
- repeated activation/account failures occur;
- account/security incident occurs;
- customer threatens legal/regulatory action;
- order is high-value under the internal thresholds;
- customer asks for something that would require violating provider rules.

## 8. Support incident sequence
1. Identify order ID and exact issue.
2. Check whether access was originally delivered correctly.
3. Separate:
   - SaveOnSub fulfillment/admin issue;
   - provider outage/policy/feature change;
   - customer-caused security/misuse issue.
4. Apply the Refund/Replacement/Service Assurance Policy.
5. Log evidence, action, owner and resolution.
6. Never promise a refund/replacement before checking eligibility.

## 9. Shift/handover rule
When one operator becomes unavailable, unresolved items must be handed over with:
- customer/order ID;
- last customer message;
- payment status;
- activation status;
- exact next action;
- deadline or promised update time;
- risk/escalation note.

No customer should have to repeat the full story because Emon/Ripon changed shifts.
