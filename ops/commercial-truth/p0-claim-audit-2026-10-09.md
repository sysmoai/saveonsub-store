# SOS Commercial Truth — Source-Backed P0 Audit (09 October 2026)

**Classification:** Public, sanitised GitHub research. **Status:** DRAFT/REVIEW. Neither price approval nor deployment permission. **Owners:** Emon (CEO), Ripon (operator research), scoped to SaveOnSub only.

## Grounding / reconciliation method
On 09 Oct 2026, sampled the served site with a freshness-tolerance-zero fetch for [home](https://saveonsub.com/), [ChatGPT Plus](https://saveonsub.com/p/chatgpt-plus.html), [Google AI Pro](https://saveonsub.com/p/google-ai-pro.html), [warranty](https://saveonsub.com/warranty), and [refunds](https://saveonsub.com/refund). A fresh-ish targeted fetch can still be affected by origin caching; this is not a full crawl or Cloudflare deployed-SHA proof. Cross-checked repo main source catalog.json, the [Sep 17 pricing baseline](https://github.com/sysmoai/saveonsub-store/blob/main/ops/PRICING-V2-2026-09-17.json), build_site.py, commercial_truth_v2.py, and sanitize_pricing_v2_legacy.py. Official external control: [OpenAI Consumer Terms effective Jan 1 2026](https://openai.com/policies/terms-of-use/) and [ChatGPT Business membership rules](https://help.openai.com/en/articles/8542216).

Public pages establish marketing *claims*, not the reality of provider eligibility, settled sales, supplier invoicing, active support capacity or actual net profit. Historical internal pricing is not proof of today's billable price or entitlement. Build script presence is not Cloudflare deployment evidence.

## The 14 P0 findings and exact next decision

| ID | Surface | Observed condition / evidence gap | CEO treatment | Proof / owner |
|---|---|---|---|---|
| CT01 | Plus product page | From BDT 499; shared access. OpenAI consumer Terms prohibit making an individual account available to others. | **HOLD** shared personal-account resale / new activations, pending adequate written authorization; maintain existing customer remedies. | Emon provider authorization |
| CT02 | Plus product page | Shared "LOW RISK" and "WARRANTY COVERED" variants imply a permissible product. | **REVISE** misleading access classification; no "low risk" workaround for a forbidden model. | Emon approval + Ripon source |
| CT03 | Plus price source | Legacy personal approx BDT 2,990; Sep 17 baseline BDT 3,390. | **INQUIRY**: neither date is a current supplier invoice or CEO reapproval. | Emon real cost/fees + product ownership |
| CT04 | Google AI Pro product | Public from BDT 500 personal; baseline BDT 3,390. No current landed cost/activation source. | **INQUIRY / HOLD fixed-price promotion** until eligibility, rights, cost and duration verified. | Emon/Ripon |
| CT05 | Google AI Pro claims | "211+ orders" and "#1 seller" appear on the product page, sometimes referencing AIPS. | **REMOVE OR SUBSTANTIATE** after SOS-only audited settlement evidence; no inherited sibling-store statistics. | Owner order ledger |
| CT06 | Home bundles | Shared ChatGPT subscription bundles are still marketed, despite revised high-level disclaimers. | **HOLD** linked unauthorized shared access and audit bundle checkout/copy. | Ripon + Emon |
| CT07 | Warranty | One-hour replacement, 7-day shared and 30-day personal coverage advertised. | **LEGAL / OPERATIONS REVIEW**: capacity, reserve and legacy liabilities must be verified. No retroactive loss of existing commitments. | CEO service/finance |
| CT08 | Refund | Same-day/one-hour refund promises and no-fee payment refunds. | **LEGAL / OPERATIONS REVIEW**: actual funding, refunds processor and support evidence; preserve legal rights and past agreements. | CEO finance |
| CT09 | Plus and Google product metadata | Search titles and OG descriptions still price-anchor old offers. | **P0 preview correction** after pricing and rights review; update product, basket, EN/BN, metadata, JSON-LD together. | Release owner |
| CT10 | Product competitor snapshot | Several Jul 2026 "market leader" and feature comparisons presented inside current sales copy. | **DATE-LABEL and REVERIFY**; do not treat historic survey as current. | Ripon editorial |
| CT11 | Home page currently | Fresh extract has more cautious plan-specific delivery/warranty copy; prior cached home result still had blanket claims. | **PRESERVE current truthful improvements**; first capture actual release SHA and exact current served HTML. | CEO engineering |
| CT12 | Payments | Fresh home describes "payment number shown at checkout"; prior "merchant number" issue remains for historic sources. | **VERIFY actual account type and settlement**, do not claim merchant status without documentary proof. | Emon finance |
| CT13 | Build-vs-live gap | Repo main contains pricing-v2 projection/sanitizer, but served product pages still show legacy prices/shared tiers. | **INVESTIGATE deployed SHA / build-output parity**; script intent != currently deployed revision. | Cloudflare owner |
| CT14 | Corporate/brand claims | SYSmoAI company registration not verified; other-brand histories are separate. | **BRAND-ONLY and cross-tenant separation**. No unregistered Private Limited representations. | Corporate SSOT |

## Top 10 product-level operational gates (not sellable approvals)

| Model | Current operating status | Shortest required proof |
|---|---|---|
| ChatGPT Plus shared personal credentials | **HOLD** | Provider authority allowing identical access model; otherwise no new sales |
| ChatGPT Plus customer-owned setup service | **INQUIRY_ONLY** | Customer-controlled provider plan, no password custody, service scope and actual cost |
| ChatGPT Go customer-owned setup | **INQUIRY_ONLY** | Region, current plan price, permitted setup workflow |
| ChatGPT Business / workspace seat | **INQUIRY_ONLY** | Legitimate organization member relationship or explicit resale authority; not ad-hoc seat flipping |
| Google AI Pro own Gmail | **INQUIRY_ONLY** | Exact account entitlement, promo limits, landed cost and customer rights |
| Claude Pro own account | **INQUIRY_ONLY** | Official tier, terms, local checkout and implementation method |
| Perplexity Pro | **INQUIRY_ONLY** | Discount/grant transfer eligibility and real pricing |
| Midjourney shared access | **HOLD PENDING REVIEW** | Provider license and account rules |
| Cursor or Replit own workspace | **INQUIRY_ONLY** | Plan/credit limits, owner-billed method, support scope |
| ElevenLabs | **INQUIRY_ONLY** | Tier, allowed rights, credit expiry and authentic checkout |

Do not sell promotional, student, nonprofit or charity-funded benefit accounts through transfer unless their terms expressly allow commercial transfer. Do not automatically convert a team seat or family slot into a "reseller license".

## Execution owners / measurable proof
1. **Ripon / today:** 7-field sanitized daily aggregate (paid verified, payment review pending, pending delivery, P0/P1, renewals, leads, blockers), and five provider source cards. UNKNOWN when evidence missing. No credentials or personal transaction evidence in public GitHub.
2. **Emon / today:** verify current customer support liabilities, true bank/MFS settled receipts and correct payment destination in restricted SOS finance evidence. No screenshot-only paid verification.
3. **Emon / 48h:** calculate true contribution (settled revenue minus supplier cost minus transaction/FX/support/refund reserve) and separate overhead; missing costs = **PROFIT UNKNOWN**.
4. **Engineer / 48h:** confirm Cloudflare Pages production SHA, exact preview artifact, rollback; run build_site.py and tests on isolated preview, no silent main merge or deployment.
5. **CEO:** quote or publish only after real rights, price, cost, delivery, refund policy and release signoffs. Existing customer rights unchanged.

## Source and issue relationships
[CEO #62](https://github.com/sysmoai/saveonsub-store/issues/62) · [Claims #60](https://github.com/sysmoai/saveonsub-store/issues/60) · [Orders/COGS #55](https://github.com/sysmoai/saveonsub-store/issues/55) · [Access #54](https://github.com/sysmoai/saveonsub-store/issues/54) · [Ripon workboard](https://docs.google.com/document/d/1eSum4PwTr67Z1Sg79DveRyN8t4XmfvqGbKNfPlM_MiQ/edit).

**Privacy:** This GitHub repo is public. NO customer names, phone lists, NIDs, bills, banking details, supplier credentials/cost secrets, OTP, private profits or access tokens may be added here.

**Completion:** audit documented; remediation NOT MERGED, NOT LIVE; SKU costs/order profit UNKNOWN; owner/cloud deployment authorization BLOCKED pending proper verification.
