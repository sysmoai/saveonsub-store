# SaveOnSub Product & Price Control
**Revision:** 2026-09-18  
**Owner:** Emon Hossain  
**Customer-service operator:** Shorif Ahmmed Ripon  
**Applies to:** SaveOnSub only

## 1. Purpose
This is the commercial source-of-truth control for every subscription quoted or sold by SaveOnSub. The objective is to prevent stale pricing, accidental loss-making sales, unsupported access claims, unauthorized discounts, and provider-policy mistakes.

## 2. Source-of-truth hierarchy
When two sources conflict, use this order:

1. **Current CEO-approved pricing register** — `ops/PRICING-V2-2026-09-17.json` or its later approved successor.
2. **Provider official pricing/checkout, product page and terms** — used to reconfirm current tier, billing unit, taxes, access model and availability.
3. **Current SaveOnSub product page only when its commercial revision matches the approved pricing register.**
4. Customer-service notes, old screenshots, old Facebook posts and the legacy raw `catalog.json` are **not pricing authority**.

A stale public page must never override the approved pricing register.

## 3. Access-type classification
Every offer must be classified before payment:

- **Customer-specific / Personal:** activated for the customer's own account where the provider supports the method.
- **Team / Workspace / Family / Extra Member:** multi-user access explicitly supported by the provider's plan/rules for the intended use.
- **Bundle:** SaveOnSub combines separately valid products/services; each component must pass its own provider/access check.
- **Setup / Service:** SaveOnSub charges for setup, payment assistance, migration, onboarding or related service.
- **Credential-shared / unclear multi-user access:** fail closed. Do not present it as provider-supported personal/team access. It may only be offered after the exact provider authorization, access method, privacy implications, continuity risk, unit economics and written customer disclosure are approved by Emon.

## 4. Pricing rule
Never quote from memory when a current approved price is not available.

### 4.1 Personal/customer-specific product
Determine:
- exact provider tier and billing unit;
- actual provider checkout amount/currency;
- tax/VAT actually charged or legally applicable;
- FX/card/payment cost;
- any irrecoverable activation cost;
- required SaveOnSub contribution/profit.

**Price floor = real landed cost + required approved contribution.**

For ordinary paid subscription activations, the business must not deliberately price below the approved true-profit floor. The existing pricing register governs the exact approved BDT selling price. A product with unclear economics remains **INQUIRY / PRICE REVIEW REQUIRED**.

### 4.2 Provider-supported multi-user/team/family product
Do not divide the provider cost by the theoretical maximum seat count. Use conservative, actually sellable seats.

**Minimum cohort revenue must cover:**
1. provider/checkout cost;
2. tax/FX/payment cost;
3. support/admin cost;
4. interruption/risk reserve where relevant;
5. required cohort profit.

If the resulting per-seat price cannot meet the approved profitability requirement, the offer is not sellable at that price.

### 4.3 Important legacy-price rule
Historical/shared prices in the raw catalog or old live pages are not automatically approved. For example, a low shared price that does not cover the cohort cost plus required profit is blocked even if it previously appeared on the website.

## 5. Current governed examples
Use the current pricing register, not this section, if a later revision exists. As of the 2026-09-17 register:

- ChatGPT Go — Personal, 1 month — **৳1,299**
- ChatGPT Plus — Personal, 1 month — **৳3,390**
- ChatGPT Business — Team/Workspace seat — **৳4,290/user/month**
- Claude Pro — Personal — **৳3,390**
- Google AI Pro — Personal — **৳3,390**
- Perplexity Pro — Personal — **৳3,390**
- Cursor Pro — Personal — **৳3,390**
- Replit Core — Personal — **৳3,390**
- Products marked `inquiry` require fresh verification before any fixed quote.

## 6. Quote rule
- Approved fixed price: quote the register price.
- Dynamic/unapproved product: research first; do not invent a price.
- A dynamic quote is normally valid for **30 minutes** unless Emon approves a longer lock.
- Before taking payment, reconfirm availability, access method and final BDT amount.
- Ripon has **no discount authority**.
- Any discount, custom bundle, credit, compensation or below-register quote requires Emon approval in writing.

## 7. New/unknown subscription workflow
When a customer asks for a product not already approved:

1. Identify exact product, tier, duration and customer use case.
2. Open the provider's official pricing page and official terms/help page.
3. Confirm country/region availability and billing currency.
4. Confirm whether access is personal, team/family or another provider-supported model.
5. Capture current checkout/official price and applicable tax/fees.
6. Calculate landed cost and proposed BDT price using the pricing rule.
7. Check for restrictions on sharing, resale, seat transfer, commercial use, age, region or refunds.
8. If any rule/economic point is unclear, mark **HOLD — EMON APPROVAL**.
9. After approval, add the product/tier to the pricing register before repeated selling.

## 8. Mandatory price-review triggers
Recheck an offer whenever any of these happens:
- provider price/tier/package changes;
- provider terms/access rules change;
- VAT/tax treatment changes;
- FX/card/payment cost materially changes;
- payment route changes;
- provider introduces/removes regional pricing;
- unusual activation failures/refunds occur;
- a product has not been verified recently enough for a reliable quote.

## 9. Customer-facing rule
Never describe SaveOnSub as the provider or imply official affiliation unless a documented relationship exists. Product names/trademarks belong to their owners. Explain the exact access method before payment.

## 10. Profit-control gate
No activation starts until the order record contains:
- approved selling price;
- collected amount;
- expected landed cost;
- expected contribution/profit;
- payment verification;
- approved access model.

If expected contribution is below the approved floor, stop and escalate before purchase/activation.
