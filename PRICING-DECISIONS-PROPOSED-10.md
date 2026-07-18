---
date: 2026-07-13
type: pricing-decision
status: awaiting-emon-confirmation
tags: [saveonsub, pricing, launch-blocker]
---

# SAVEONSUB — Confirm 10 Proposed Prices (launch blocker)

> These 10 SKUs carry `price_source: proposed-new` — Claude proposed them, but **brand law says no proposed price ships until you confirm it**. This is the *only* remaining launch blocker (deploy_preflight flags it every build). Confirm or adjust each, then I flip `price_source` to `verified-jul26` and we're green.
> USD→BDT anchor rate: **110**. "Official" = provider's monthly list price.

## ⚠️ 2 must-fix before launch — personal plan priced ABOVE official

On these two, the page shows "official ~৳X" right next to a higher "our" price — the shopper sees us as *more expensive*. Either reprice below official, or drop the official-anchor on managed-personal plans and reframe as "we handle the card/setup for you."

| SKU | Plan | Our price | Official | Problem | Recommend |
|---|---|---|---|---|---|
| **Netflix** | Personal (your email) | ৳1,099 | ~৳879 | +25% over official | Drop to **৳799**, or keep ৳1,099 but relabel "managed — we pay the card for you" & hide the official anchor on this plan |
| **Invideo AI** | Personal | ৳2,799 | ~৳2,750 | +2% over official | Drop to **৳2,499** (still healthy vs no-card reality) |

## 📊 1 to reconsider — priced at top of surveyed market

| SKU | Plan | Our price | BD market (surveyed) | Note | Recommend |
|---|---|---|---|---|---|
| **Coursera Plus** | Shared | ৳1,499 | ৳699–1,500 | We're at the ceiling; competitors as low as ৳699 | Lower shared to **৳1,199** to compete, or keep ৳1,499 and lean on the written warranty + certificate-name honesty |

## ✅ 7 that look right — confirm as-is (quick yes)

| SKU | From-price | Official | BD market | Why it's fine |
|---|---|---|---|---|
| **Mistral Le Chat Pro** | ৳1,299 personal | ~৳1,649 | not surveyed | ~21% under official for a personal account; low-volume SKU, fine to test |
| **Prime Video** | ৳249 shared / ৳899 personal | ~৳989 | not surveyed | Aggressive shared price; personal sits below official ✓ |
| **LinkedIn Premium** | ৳1,999 personal | ~৳3,299 | not surveyed | ~40% under official on your own profile |
| **NordVPN** | ৳299 shared / ৳3,499 personal-1yr | ~৳1,429/mo | ৳150–3,499 | Shared just above the ৳150 floor but warranty-backed; 1-yr personal is a full year |
| **Surfshark** | ৳249 shared | ~৳1,700 | ৳249–1,700 | Sitting exactly at the market floor — best-in-market ✓ |
| **Video Creator Bundle** (Invideo+CapCut) | ৳999 | ~৳3,850 | not surveyed | Strong bundle discount vs buying separately |
| **Dev Bundle** (Cursor+Copilot) | ৳1,799 | ~৳3,300 | not surveyed | ~45% under buying both official |

## How to confirm

Reply with any of:
- **"Confirm all as-is"** — I flip all 10 to verified (fastest; leaves the 3 flags above unchanged).
- **"Apply your recommendations"** — I set Netflix personal ৳799, Invideo personal ৳2,499, Coursera shared ৳1,199, confirm the rest, flip all to verified.
- **Line-by-line** — give me the numbers you want and I set exactly those.

After confirmation: I update `catalog.json` price_source → `verified-jul26`, rebuild (prices propagate to all EN+BN pages, schema, sitemap, social cards automatically), re-run the harness + preflight to 0 blockers, and commit. Then the only thing between the store and live customers is the ~45-minute deploy.
