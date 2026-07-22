---
date: 2026-07-13
type: launch-kit
status: ready-for-emon
bu: SOS
tags: [store, launch, deploy]
---

# 🚀 SAVEONSUB Store — Launch Kit

> Site status: **BUILT & AUDIT-CLEAN** (67 pages, 49 products, 0 gaps via `audit_all.py`). Everything below is Emon-gated.

## The build (what exists, all local in `12_SOS/store/`)

| Layer | Files | Status |
|---|---|---|
| Data SSOT | `catalog.json` (49 products, 77 plans) | ✅ |
| Build pipeline | `build_catalog.py` → `build_pages.py` → `build_trust.py` → `build_seo.py` | ✅ rerun after any catalog edit |
| Quality harness | `audit_all.py` — run after EVERY change; exit 0 = launch-clean | ✅ 0 gaps |
| Pages | index, all, quiz, checkout, 8 trust, 49 product, 6 blog = 67 | ✅ |
| SEO/AIO/GEO | sitemap (65 URLs), robots, llms.txt, schema everywhere | ✅ |
| A11y/Perf | WCAG AA computed, 64KB heaviest page, zero images | ✅ |

## Emon-gated launch steps (in order)

1. **Kill-rule decision** — publishing = officially unfreezing SOS as the store brand. One sentence in the Decision Log.
2. **Confirm the 30 `proposed-new` prices** in catalog.json (search `"price_source": "proposed-new"`). Edit → rerun 4 build scripts → `audit_all.py`.
3. **Domain**: check/buy **saveonsub.com** (+ .com.bd?). If taken, decide alternative before any promotion.
4. **Deploy** (free, ~10 min): Cloudflare Pages (drag the `store/` folder, or connect repo) or Replit static. Set custom domain. NO server needed.
5. **DNS/Email**: DMARC+DKIM on the domain BEFORE outreach (same Zoho flow as blind-spots audit).
6. **Search Console + Bing Webmaster**: submit sitemap.xml day one. IndexNow optional.
7. **Analytics**: Cloudflare Web Analytics (free, no cookie banner needed) — add one script tag to the 4 build templates.
8. **First-week ops**: win-back message to ~1,600 past buyers pointing at the new store (playbook exists: [[AIPS-WINBACK-CAMPAIGN-PLAYBOOK]]); post the 6 blog guides to FB/LinkedIn; monitor WhatsApp.

## Standing maintenance rules

- **Add/edit product** → edit `catalog.json` only → run 4 builds → `audit_all.py` → commit. Never hand-edit generated pages.
- **Price re-verification**: monthly, re-check `verified-jul26` items + official links (prices drift).
- **Renewal engine**: WhatsApp reminder T-3 days (manual until automation; spec: [[aips-renewal-automation-spec]]).
- **Honesty invariants (never break)**: no fake ratings (auditor enforces), no "lifetime" claims, official links stay on every product, free-tier advice stays even when it costs sales.

## Open items inherited from the business (not the site)

AIPS↔SAVEONSUB brand relationship statement · Payoneer/gateway for future card payments · renewal automation build · catalog expansion beyond 49 (competitor sites list 70-100 SKUs — pipeline in demand-gap analysis).
