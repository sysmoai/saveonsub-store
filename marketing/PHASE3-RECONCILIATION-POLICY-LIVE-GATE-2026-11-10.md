# SaveOnSub Phase 3 — Evidence Reconciliation, Rights and Launch Gate

**Date:** 2026-11-10 (Asia/Dhaka)  
**Scope:** SaveOnSub ONLY. All checks are read-only except this review-only GitHub file.  
**Decision:** **NO-GO** for new paid Meta campaigns pending rights, margin, live measurement and sales attribution verification.  
**Approval:** No merge, deploy, billing changes, campaign creation/activation or advertising spend authorized.

## 1. First Meta test reconciliation — observed vs unknown

| Metric / source | Evidence at review | Status |
| --- | --- | --- |
| Original Meta ad | CEO/screenshot reports 46 started conversations, USD 14.85 spend, 8,866 impressions, 6,406 reach | SELF-REPORTED / SCREENSHOT |
| SaveOnSub profit tracker ADS | One test row: 2026-10-29, USD 14.85, BDT 1,930.5, 46 chats; Paid_Orders and Revenue_BDT blank | SOURCE-READ; no sale linkage |
| SaveOnSub profit tracker ORDERS | Header only | NO RECORDS |
| SaveOnSub Operator Work Register LEADS, INTERACTIONS, ORDERS, APPROVED_OFFERS, METRICS | Header only for every inspected tab | NO RECORDS |
| SOS CEO Private Finance SETTLEMENTS, SUPPLIER_COSTS, ORDER_PROFIT, APPROVALS, TOP10_COSTS | Header only | NO VERIFIED RECORDS |
| SOS CEO Private Payment & Approval Verification | PAYMENT CHECK two rows, both Data Class DEMO and not verified; FINANCE CHECK one DEMO, APPROVALS one DEMO HOLD | DEMO ONLY |
| SOS synthetic CRM | Three DEMO leads and two DEMO orders | EXCLUDED |
| Supermetrics Facebook Ads (FA) | Data source configured but NOT_AUTHENTICATED; accounts_discovery returned no Facebook Ads connection for connected team | NO LIVE META DETAIL |

**Conclusion:** Zero **verifiable linked** paid orders among 46 **reported** started conversations with currently accessible evidence. **This is not proof of zero actual sales, nor proof that all 46 were unique customers.** Actual paid count, qualified share, conversion rate, first-sale CAC, order ROAS and profitable campaigns are **UNKNOWN**. Do not report them as zero or invent 46 conversation records.

**Next reconciliation operation (private, authorized channel only):**
1. Export permitted aggregate message outcomes and source campaign/ad metadata from the actual SaveOnSub-owned Meta inbox/Ads account; do not place raw customer messages or identifiers in public GitHub.
2. Under controlled access, match each permitted unique conversation ID to only SaveOnSub-specific operator lead IDs, approved quotes and merchant-verified settled order IDs. Capture outcome as QUALIFIED_A, QUALIFIED_B, LOW_INTENT, INELIGIBLE, DUPLICATE, UNKNOWN.
3. For joined paid orders only, use private ledger reference, actual supplier invoice and fees to compute pre-ad and post-ad contribution. Preserve unmatched, duplicate, organic, and missing-source groups as explicit counts. No sister-unit sales or synthetic payments.
4. Cross-check Meta reporting window, message destination (the old tracker labels this test Messenger), billing currency, attribution setting, ad status and actual delivery date before comparing.

## 2. Fresh public-site verification

Fresh website text and asset fetch (cache freshness tolerance=0) from the public domain, 2026-11-10:
- https://saveonsub.com/ available. Newer, truth-safe homepage content compared with old search crawler copy; do not quote an older crawl as the current site.
- https://saveonsub.com/p/chatgpt-plus available; publicly advertises Starter Shared at BDT 499 / month and Premium Shared at BDT 999 / month; discloses shared accounts and risk.
- https://saveonsub.com/assets/measurement.js available; text reflects older UTM/WhatsApp handoff and is missing current GitHub's order-submit/Purchase attribution changes.
- https://saveonsub.com/assets/meta-pixel.js returned **HTTP 404**.
- https://saveonsub.com/assets/ga4.js returned **HTTP 404**.
- GitHub main merge #114 contains new Meta Pixel/GA4 source; source exists ≠ canonical live. PR #116 opt-in fix remains DRAFT.
- Live HTML-to-script inclusion, browser-level consent, real event delivery, CAPI matching and exact Cloudflare deployment SHA remain **UNVERIFIED**.

**Critical P0:** Review/resolve public display of shared ChatGPT/Claude/Grok/Perplexity subscriptions under provider terms before paid ads. Making risks visible does not grant resale or credential-sharing rights. Use a separate, SEO-preserving controlled content plan; do not unilaterally remove pages or change production prices.

## 3. Official provider rights — category gate, not permission to resell

| Tool / commercial model | Current official evidence | Phase 3 disposition |
| --- | --- | --- |
| ChatGPT individual | https://openai.com/policies/terms-of-use/ disallows sharing personal credentials and selling/distributing the service | HOLD for shared resale, managed account pools or unsupported reseller claim. Customer-owned paid setup/education may be assessed separately. |
| OpenAI Business/API | https://openai.com/policies/services-agreement/ prohibits reselling/leasing account or end-user account access and third-party API-key transfers | HOLD for unauthorized Business seat / API key resale; direct customer organization and authorized advisory services only after specific review. |
| Claude individual | https://www.anthropic.com/legal/consumer-terms bars sharing account and reselling service | HOLD for shared/personal subscription resale unless documented explicit permission. |
| Google AI Pro / Gemini | https://support.google.com/googleone/answer/9004015 and https://one.google.com/terms-of-service permit qualifying family benefits; that is not a commercial third-party seat resale license | HOLD for paid 'family seat' resale; investigate independent onboarding/training or formal distributor rights. |
| Perplexity consumer | https://www.perplexity.ai/en-GB/hub/legal/terms-of-service and https://www.perplexity.ai/en-GB/hub/legal/aup govern individual paid accounts and restrict distributing/licensing the service | HOLD for pooled or unsupported shared seats; written distributor authorization needed to claim resale. |
| Grok consumer | https://x.ai/legal/terms-of-service disallows sharing credentials or making account available to others | HOLD for consumer credentials pooling/resale; separately evaluate allowed advisory services. |
| DeepSeek consumer | https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html bars transferring/lending/renting accounts | HOLD for consumer account resale. |
| DeepSeek Open Platform | https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html expressly permits lawful downstream integrations serving end users, with no API key sharing | Candidate **custom application/integration/service**, subject to local legal, data-protection, invoice-backed usage costs, service scope, margin and explicit owner approval. Not proof that API-credit resale is authorized. |

Commercially relevant supported angle may be an independent **AI workflow diagnosis + onboarding/training + safe customer-owned-account setup** with truthful separation from providers. No SKU is approved until service-specific rights and economics are verified.

## 4. Verified unit-economics readiness

- SaveOnSub Profit Tracker MARGIN: 133 plan rows checked; **133/133 missing YOUR_Buy_Cost_BDT**. The displayed price, generated estimated cost and provisional gross profit are **not verified procurement economics**.
- Private CEO settlement and supplier cost sheets have no completed real order rows in inspected ranges.
- Other business units' supplier terms, sales and costs are prohibited as SaveOnSub proof.
- No subscription or service passes a complete rights + actual cost + verified positive after-ad contribution audit.
- If CEO confirms protected net contribution floor BDT 500 after ads, then max permissible CAC = verified pre-ad contribution minus BDT 500. If nonpositive, paid acquisition cannot be supported at that offer under that floor.
- Do not use estimated $15–$35 pilot budget as approval; **new ad spend remains zero**.

## 5. Launch gate, in dependency order

**NO-GO until ALL required items have reliable proof:**

1. **Provider / SKU:** one legitimate, explicitly approved SaveOnSub offer with exact plan, access path, duration, Bangladesh eligibility, legal/contractual rights, disclosure and customer-owned or authorized workspace conditions.
2. **Unit economics:** genuine supplier invoice/contract, BDT landed cost, variable fees/support/reserve, written approved sale price, conservative max CAC, refund and delivery handling.
3. **Tracking release:** Cloudflare exact-SHA, rollback, post-deployment smoke tests and website asset 200 responses; PR #116 browser and security QA, consent flow, Events Manager Test Events, GA4 DebugView and payment-confirmed order-to-Purchase CAPI (not checkout click).
4. **Meta actual account:** authenticate Facebook Ads in Supermetrics or provide a restricted export; verify page, Instagram, WhatsApp destination, campaign/adset/ad breakdown, status, currency, attribution and policy restrictions. Never confuse OpenAI's ChatGPT Ads Manager with Meta.
5. **Sales reconciliation:** join old 46 conversation outcomes (including UNKNOWN/unmatched) to qualified leads and verified orders using SaveOnSub-only private sources.
6. **CEO written cap:** exact total/daily budget, duration, stop-loss conditions, owner, account, approved creatives/claims and explicit spend authorization.

Then propose a new pilot or separately approve an authorized service-only test. **No launch recommendation** on current evidence.

## Source / reproducibility notes

- Read dates: 2026-11-10; inspected SaveOnSub-only Profit Tracker (ADS / ORDERS / MARGIN), Operator Work Register, CEO private finance and payment sheets, synthetic CRM with DEMO exclusions, Supermetrics FA discovery, GitHub main and PRs #114/#116/#118, fresh public URL reads.
- All private workbooks are source-referenced internally by their names but no private IDs, sensitive amounts, customer records or payment references are copied here.
- Store customer-level reconciliation, payment evidence, actual buy costs and supplier terms only in approved private SaveOnSub operations.
