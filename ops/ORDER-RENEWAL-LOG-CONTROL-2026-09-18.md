# SaveOnSub Order & Renewal Log Control
**Revision:** 2026-09-18  
**Purpose:** One auditable record for sales, payment, activation, profit, support and renewal.

## 1. Rule
Every paid order must be logged **before activation**. If an order is not in the log, it is not treated as operationally complete.

## 2. Required fields
### Identity / lead
- Order ID
- Created timestamp
- Customer name
- Customer WhatsApp/phone
- Acquisition channel (website / Facebook / Instagram / WhatsApp / referral / other)
- Operator (Emon / Ripon)

### Product / pricing
- Provider
- Product
- Exact tier
- Duration/billing unit
- Access type: Personal / Team-Workspace-Family / Bundle / Setup-Service / Other-approved
- Approved price revision
- Quoted BDT price
- Quote timestamp/expiry when dynamic
- Official source URL
- Provider terms/help URL
- Last verified date

### Payment
- Collected amount
- Method: bKash / Nagad / Rocket / Upay / Bank / Other-approved
- TxnID/reference
- Payment verified by
- Payment verified timestamp
- Payer identifier sufficient for reconciliation (do not store unnecessary sensitive data)

### Unit economics
- Actual/expected provider checkout cost
- Tax/VAT/FX/payment costs actually relevant
- Other direct activation cost
- Total landed cost
- Expected/actual contribution
- Profit-control result: PASS / HOLD
- Reason for any variance

### Fulfillment
- Status
- Activation owner
- Activation method summary
- Activation timestamp
- Customer verification timestamp
- Expiry/renewal date
- Renewal consent/status
- Next reminder date

### Support / assurance
- Service-assurance terms attached to order
- Incident opened? Y/N
- Incident type
- Provider ticket/reference if any
- Replacement/re-activation action
- Refund amount/status
- Final resolution date
- Notes

## 3. Allowed status values
`NEW` → `QUALIFIED` → `QUOTED` → `PAYMENT-PENDING` → `PAID-VERIFIED` → `ACTIVATING` → `DELIVERED` → `CUSTOMER-VERIFIED` → `CLOSED`

Exception states:
- `HOLD-PRICE`
- `HOLD-PROVIDER-RULE`
- `PAYMENT-REVIEW`
- `INCIDENT`
- `REFUND-PENDING`
- `REFUNDED`
- `CANCELLED`

## 4. Renewal control
For renewable plans, create reminders:
- 7 days before expiry for higher-value/business plans when useful;
- 3 days before expiry;
- day of expiry if customer has not responded.

Do not purchase renewal until current price is reconfirmed and customer consent/payment is verified unless a documented recurring authorization exists.

## 5. Reconciliation
### Every operating day
Emon or Ripon must reconcile:
- total orders marked paid;
- actual bKash/Nagad/Rocket/Upay/bank receipts;
- total activations;
- unresolved payment mismatches;
- refunds;
- orders waiting for renewal.

### Weekly
Review:
- number of leads;
- response time trend;
- paid orders;
- conversion rate;
- revenue;
- landed cost;
- true contribution/profit;
- average order value;
- refunds/replacements/incidents;
- repeat customers;
- product-level margin;
- stale products/prices requiring review.

## 6. Security / privacy
Never store in the order log:
- full card number;
- CVV;
- OTP;
- bank/app PIN;
- recovery codes;
- unnecessary customer passwords;
- unneeded identity documents.

Use least data necessary for support, reconciliation and legitimate business records. Restrict access to Emon and specifically authorized operators.

## 7. Profit-control use
The log is not only CRM. It is the evidence base for profitability. A product that repeatedly misses the approved contribution floor must be repriced, re-sourced or paused.

## 8. Target metrics
Initial operating target:
- **300+ completed subscription sales/activations per month**
- maximize qualified-lead response speed;
- minimize unresolved incidents and avoidable refunds;
- maintain positive true contribution on every approved offer/cohort.

Traffic growth (50K–100K+ organic visits/month) is a separate acquisition target; success is measured by profitable completed orders, not traffic alone.
