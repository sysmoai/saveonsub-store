---
date: 2026-07-11
type: blueprint
status: step-2
bu: SOS
tags: [store, ia, ux, blueprint]
---

# SAVEONSUB Store — IA + UX Blueprint (Step 2)

> Architecture: **statically generated multi-page site** (best SEO — real HTML per product), built LOCALLY by `build.py` from `catalog.json`. Zero backend; cart via localStorage; checkout via bKash/Nagad + WhatsApp deep-link. Deployable to any static host later (Replit/CF Pages) — but everything builds and runs on this device.

## 1. Architecture

```
12_SOS/store/
├── catalog.json          ← SSOT (Step 1 ✅)
├── build.py              ← generator: reads catalog.json → emits ALL pages
├── assets/style.css      ← design system (one file)
├── assets/app.js         ← cart, quiz, search, checkout
├── index.html            ← home
├── all.html              ← full catalog engine
├── p/<id>.html           ← 49 product pages (GENERATED — unique SEO per SKU)
├── quiz.html             ← "Find my AI" needs quiz
├── checkout.html         ← cart → payment → WhatsApp
├── faq.html · warranty.html · refund.html · privacy.html · terms.html
├── about.html · how-to-order.html · 404.html
├── blog/<slug>.html      ← 6 comparison landing pages (GENERATED)
├── sitemap.xml · robots.txt · llms.txt   (GENERATED)
```

## 2. Page specs (audit gate: every row complete)

| Page | Purpose | Primary CTA | Key modules | Schema.org | Target keywords |
|---|---|---|---|---|---|
| index.html | Convert + orient; brand trust | Browse catalog / Order on WhatsApp | Hero+trust bar, bestsellers(5), categories(11), how-it-works(4), bundles, testimonials, objection FAQ, ticker | Organization, WebSite+SearchAction, FAQPage | premium subscription bd, ai tools price bangladesh |
| all.html | Findability of all 49 SKUs | Add to cart / View product | Search, category chips, price+type filters, sort, ToS-risk legend | ItemList, BreadcrumbList | buy ai subscription bangladesh, [category] bd |
| p/&lt;id&gt;.html ×49 | Rank + convert per product | Add to cart / WhatsApp order | Official-price anchor bar, plan picker (shared/personal), ToS honesty box, delivery SLA, product FAQ, related+bundle upsell, reviews | Product+Offer+AggregateRating, FAQPage, BreadcrumbList | from catalog.json keywords (e.g. "chatgpt plus price in bangladesh") |
| quiz.html | Kill "which one?" indecision (4+ lost sales) | Get my recommendation | 4-question quiz → SKU/bundle rec + WhatsApp handoff | Quiz (educationalUse), BreadcrumbList | which ai tool should i buy bd |
| checkout.html | Zero-friction manual payment | Send order on WhatsApp | Cart review, order-ID generator (SOS-YYMMDD-####), bKash/Nagad/Rocket instructions + copy buttons, txn-ID field, prefilled WhatsApp message, pay-after-testing option | CheckoutPage (WebPage), BreadcrumbList | bkash payment subscription bd |
| faq.html | Objection killing at scale | WhatsApp support | 20+ Q&A from sales playbook (safety, shared privacy, refunds, delivery) | FAQPage | is shared chatgpt safe bd |
| warranty.html | Trust: replacement promise | Order confidently | 1-hour replace, 7-day shared / 30-day personal terms | WebPage | subscription warranty bd |
| refund.html | Trust + policy | Contact support | Eligibility table, process, timelines | WebPage | refund policy |
| privacy.html / terms.html | Legal trust | — | Data promise (no bank login), order data use | WebPage | — |
| about.html | Brand story | Follow / WhatsApp | SYSmoAI family, founder, 3,000+ customers since 2024, mission | AboutPage, Organization | saveonsub about |
| how-to-order.html | First-buyer hand-holding | Start order | 4-step visual + video placeholder + bKash walkthrough | HowTo | how to buy chatgpt in bangladesh |
| blog/×6 | Organic traffic magnets | Product page links | Comparison tables, FAQ, internal links | Article+FAQPage | see §5 |
| 404.html | Recover lost visitors | Go to catalog | Search box + bestsellers | — | — |

## 3. Conversion flows

**A. SEO visitor (60% target):** Google/AI-answer → p/&lt;id&gt;.html (official-price anchor shocks → our price delights) → plan picker → cart → checkout → WhatsApp. Exit ramps: quiz (unsure), FAQ (skeptic), pay-after-testing (distrustful).
**B. Social/WhatsApp visitor:** index → bestsellers or bundle → checkout. One-tap "Order on WhatsApp" skips cart entirely (proven behavior from 1,600 AIPS orders).
**C. Indecisive visitor:** any page → floating quiz button → 4 questions → 1 recommendation + reason + bundle alternative → checkout. (Fixes the ৳1,500+ lost-sale pattern.)
**Universal:** floating WhatsApp button every page; cart persists (localStorage); every dead-end links to bestsellers.

## 4. Needs-quiz logic (quiz.html)

Q1 Goal: content/study/business/code/entertainment · Q2 Budget: <৳500/৳500-1000/৳1000+ · Q3 Usage: daily-heavy/regular/occasional · Q4 Risk: "my own account only" vs "cheapest okay".
Mapping (examples): content+<500+any+cheap→chatgpt-plus shared ৳350; content+500-1000→bundle-creator ৳999; study+<500→bundle-research ৳600; code+1000+→bundle-dev; entertainment+<500→netflix ৳349 or spotify ৳129; own-account-only → always personal plan of matched SKU. Full matrix = 5×3×3×2 = 90 paths → resolver function in app.js (goal picks family, budget picks tier, risk forces personal, heavy-usage upsells personal).

## 5. Blog landing pages (organic magnets)

1. chatgpt-plus-price-in-bangladesh (anchor page — highest volume keyword)
2. midjourney-vs-leonardo-bangladesh (comparison intent)
3. best-ai-tools-for-students-bangladesh (persona)
4. how-to-pay-for-ai-tools-with-bkash (payment intent — zero competition)
5. shared-vs-personal-ai-subscriptions-honest-guide (trust builder — nobody else dares)
6. netflix-spotify-youtube-premium-price-bd (entertainment cluster)

## 6. Checkout design (manual-payment, automation-ready)

1. Cart review → 2. Auto order-ID `SOS-260711-4821` → 3. Pick bKash/Nagad/Rocket → shows merchant number **+8801714672094** with COPY button + amount + "use order ID as reference" → 4. Customer pays, enters TxnID (optional) → 5. Big button: **"Confirm on WhatsApp"** → opens wa.me/8801865385348 with prefilled: order ID, items, total, TxnID → 6. Delivery promise screen (5–15 min, warranty terms). Alt path: "😟 Nervous? Pay after testing" → WhatsApp with test-request template. Future hook: same flow POSTs to API when backend exists (form action swappable).

## 7. Design system

Tokens: bg #0a0e27 family, brand green #22c55e→cyan gradient, coral #fb7185 (risk), gold (deals); Inter/Noto Sans Bengali; radius 14-16; buttons/cards/chips/badge components identical to v2 site (reuse). Trust colors: ToS labels — official=green, personal=cyan, shared-low=gold, shared-med=coral. Every price shows **official anchor struck through** + our price + "save X%".

## 8. Audit gates for later steps

Every page: title<60ch, meta desc<160ch, 1 h1, canonical, OG+Twitter, schema validates, breadcrumbs, mobile 375px clean, every product reachable ≤2 clicks from home, every CTA→working target, cart math exact, WhatsApp links E.164 correct.
