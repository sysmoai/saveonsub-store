# SaveOnSub STEP 3 — Measurement + Revenue-Weighted SEO Cohort

Date: 2026-09-04 (Asia/Dhaka)
Status: execution baseline; 50K qualified monthly organic visitors remains a target, not a guarantee.

## 1) Production truth

- GitHub `main`: source of truth.
- Vercel project `saveonsub`: production mirror successfully built merged commit `52eb0a749881519e20232bcd94bfe4760720a89a`.
- Canonical `saveonsub.com`: Cloudflare Pages and must be verified separately.
- Direct automatic GitHub -> Cloudflare workflow was retired on 2026-09-03 after credential/auth failures.
- STEP 3 restores a **manual-only, fail-closed** canonical deploy workflow. It requires a valid minimum-scope `CLOUDFLARE_API_TOKEN`; no DNS or secret changes are automated.

## 2) Measurement baseline

Connected Gmail search on 2026-09-04 found Search Console ownership/activity for other portfolio properties (`aipremium.tools`, `aipremiumshop.com`) but no `saveonsub.com` Search Console/GA4 ownership evidence in that connected account.

Repository audit found no active GA4/GTM/Plausible integration in the SaveOnSub storefront. Existing commerce behavior is localStorage + WhatsApp-first.

STEP 3 therefore adds a privacy-minimal first-party measurement bridge:

- session attribution: landing path, referrer host, UTM source/medium/campaign;
- `dataLayer` events for page-view-ready, add-to-cart, checkout-start and WhatsApp click;
- WhatsApp messages receive a compact `[SOS attribution: ...]` line so conversions can be attributed before GA4 is configured;
- no external tracker/network request is introduced by this layer.

Human/account boundary still required:

1. confirm whether a Search Console Domain property for `saveonsub.com` exists under another Google account;
2. if absent, create/verify the Domain property via DNS;
3. create or identify the correct GA4 property/data stream;
4. connect the existing `dataLayer` to GTM/GA4 only after the IDs/account ownership are confirmed.

## 3) Revenue/search priority cohort

### Tier A — immediate money pages

1. ChatGPT Plus
2. Google AI Pro / Gemini
3. Canva Pro
4. Midjourney
5. Claude Pro
6. SuperGrok
7. Perplexity Pro
8. Netflix
9. YouTube Premium
10. Spotify Premium

Selection logic: high Bangladesh purchase intent + high provider awareness + portfolio commercial relevance + existing SaveOnSub product pages.

## 4) Current provider fact findings

### Google AI — P0 freshness correction

Google's Bangladesh-localized Google One AI plan page currently exposes local BDT pricing rather than requiring a USD conversion:

- Google AI Plus: approximately **৳600/month** on the localized page.
- Google AI Pro: approximately **৳2,500/month** on the localized page.
- Current Pro page describes **5 TB storage** and **1,000 monthly AI credits** for Flow/Whisk in the surfaced Bangladesh result.

SaveOnSub source currently contains older July assumptions (`$19.99`, ~৳2,199/2,200, 2 TB copy). This is a P0 provider-freshness item for the next controlled source-data cohort. Do not continue publishing the old 2 TB / ~৳2,200 comparison as current Bangladesh provider truth.

Official source: https://one.google.com/about/google-ai-plans/

### ChatGPT Plus

OpenAI continues to list ChatGPT Plus at **$20/month** in official help/pricing material. Local checkout/tax/payment presentation can vary; do not claim a Bangladesh-localized BDT official price unless observed from an official Bangladesh checkout/source.

Official sources:
- https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus
- https://chatgpt.com/pricing/

### Midjourney

Official plan matrix surfaced during current research remains plan-based (Basic/Standard/Pro/Mega). Money page should reference the current official matrix directly rather than relying on historical market-copy claims.

Official source: https://www.midjourney.com/plans

## 5) SERP strategy — cohort rules

For each Tier-A page, the target is not keyword density. Each page should answer the purchase decision better than competing BD pages:

- exact current SaveOnSub price and duration;
- exact access type (personal/shared/invite/managed);
- current provider reference price from an official source with verification date;
- what is included / materially excluded;
- activation method and expected delivery class;
- privacy/account-control implications;
- warranty/refund terms specific to that offer;
- BDT payment methods actually supported;
- comparison against free/lower tier where useful;
- 3-6 decision FAQs based on real search intent;
- English + Bangla intent coverage through useful prose, not visible keyword lists;
- structured data must match visible content;
- internal links to one comparison/guide and 2-3 adjacent products;
- no unsupported #1/cheapest/best/only/order-count/review claims.

## 6) Portfolio cannibalization control

Before creating a new target page, search AIPS/AITP/AIPT/SOS for the same query intent. Assign one primary property/page per commercial query family. Sister properties should differentiate by audience/offer rather than cloning the same title/intention.

## 7) STEP 3 exit criteria

- [x] merged P0 hardened `main` has a READY Vercel production mirror;
- [x] Search Console/analytics evidence checked in connected Gmail;
- [x] first-party attribution layer added on branch;
- [x] manual fail-closed canonical Cloudflare deploy path restored on branch;
- [x] revenue-weighted money-page cohort defined;
- [x] current provider research identified Google AI P0 fact drift;
- [ ] Search Console property ownership confirmed/created (human Google-account/DNS boundary);
- [ ] GA4 property/stream ID confirmed before external tracker installation;
- [ ] Cloudflare token repaired and manual canonical workflow successfully run;
- [ ] Google AI source data/generator refreshed in controlled money-page cohort.
