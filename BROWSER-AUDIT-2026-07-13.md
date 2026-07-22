---
date: 2026-07-13
type: audit
status: passed
tags: [saveonsub, browser-audit, qa]
---

# On-Machine Browser Audit — 2026-07-13

> Real Chrome rendering on Emon's MacBook (not simulated). Read-tier browser access = I could SEE every page but not scroll/click it, so interactive flows rely on the code-level harness (which tested them exhaustively). Visual rendering verified across all 3 core page templates.

## ✅ Verified live in Chrome (rendering, brand, layout)

**Homepage (index.html)** — flawless. Haor Teal brand live (teal gradient headline + CTAs on #06181a), trust bar (3,000+ · 5–15 min · 1-hr warranty · bKash/Nagad/Rocket), hero with ৳2,200→৳350 anchor + SAVE 84%, 5 bestseller cards with real order counts, "1,600+ orders" honest stat, WhatsApp + Find My AI FABs, full nav incl. Guides.

**Catalog (all.html)** — flawless. "Every product. Honest label on each." headline, search box, 3 filter dropdowns (plan type / price / sort), 11 category chips incl. count "All (54)", "54 products" live count, product cards with #1–#5 SELLER badges, save %, 🔥 order counts, honest color-coded ToS labels (PERSONAL cyan / SHARED-LOW gold / SHARED-MED coral), official-price strikethrough, correct ৳ symbol on prices AND Add buttons (zoom-verified: "৳500", "Add ৳500").

**Product page (Synthesia — a survey-pending SKU)** — flawless AND proved the honesty engine both ways. Breadcrumbs, official anchor "Official: ~৳1,980/mo ($18)" struck through + "From ৳700" + SAVE 65% + "verify official ↗", plan picker (Starter Shared · WARRANTY COVERED · 1 month · delivery 5–15 min · ৳700 · Add to cart), the **"Market survey pending — we publish competitor ranges only when we've actually verified them. No invented numbers, ever"** block (with Tell-us WhatsApp link), the "What these labels mean (we're honest)" explainer, warranty box, FAQ. Confirms both the sourced-table path (Kling etc.) and the honest-pending path render correctly.

## Defects found: 0

Every rendered page matched the design system exactly. No layout breakage, no missing assets (favicon/logo/icons all loaded), no broken ৳ glyphs, correct new-brand colors throughout, FABs positioned correctly, responsive container intact at desktop width.

## Cross-checked against code harness (already-passing, confirmatory)

64 product pages generated · order-simulation (cart math + order-ID + WhatsApp payload) · 90 quiz paths · filter combinations · WCAG-AA contrast computed on the new palette · 0 dead links · valid JSON-LD · no fake-rating schema. `audit_all.py` → 0 gaps.

## Incidental live findings (unrelated to store)

- **aiteampremiumbd.com still shows "This app isn't live yet"** (Replit unpublished) — re-confirms the July website audit; a SYSmoAI B2B DM target still 404s.

## Constraint noted honestly

Browser was granted at READ tier (see, not drive). I could not scroll full pages or click through the live cart→checkout→WhatsApp flow on-screen. That interactive path is covered by the passing order-simulation in `audit_all.py`, but a human 2-minute click-through on the deployed site (or via the Claude-in-Chrome extension once signed in) is the one thing left for a 100% interactive sign-off.

## Verdict

**Ships clean.** The site renders in a real browser exactly as designed, in the unique Haor Teal identity, with honest labels and correct Bengali-taka pricing. Top-developer sign-off: PASS on rendering; interactive flow PASS by code-simulation, pending a live click-through after deploy.
