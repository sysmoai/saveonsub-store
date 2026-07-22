# SAVEONSUB Store

**Bangladesh's honest premium subscription store** — A [SYSmoAI](https://sysmoai.com) venture by [Emon Hossain](https://emonhossain.pro).

> 64 products · 214 pages · 0 audit gaps · Static HTML · bKash/Nagad · Dual EN/BN · AIO-optimized

---

## Quick Start

```bash
# Rebuild entire site from catalog.json
bash build_all.sh

# Run audit only (must return 0 GAPS before any push)
python3 audit_all.py

# Serve locally
python3 -m http.server 8765
# → http://localhost:8765
```

## Architecture

```
catalog.json          ← SINGLE SOURCE OF TRUTH (edit only this)
    │
    ├─ build_catalog.py   → assets/catalog.js (derived, never hand-edit)
    ├─ build_assets.py    → assets/*.png, favicon, social cards, PWA icons
    ├─ build_home.py      → index.html, bn.html
    ├─ build_pages.py     → p/<id>.html (EN+BN, 64×2)
    ├─ build_trust.py     → warranty, refund, privacy, terms, about, contact, etc.
    ├─ build_seo.py       → sitemap.xml, robots.txt, llms.txt
    ├─ build_category.py  → c/<cat>.html (EN+BN, 11×2)
    └─ audit_all.py       → adversarial QA gate (exit 0 = clean)
```

**Never hand-edit generated files.** Change catalog.json → run `bash build_all.sh` → audit passes → commit.

## Brand Laws (non-negotiable, enforced by audit)

1. No fake reviews, ratings, or testimonials
2. No fake urgency (countdown timers, limited stock, "X bought now")
3. No unverifiable statistics
4. Coral (#fb7185) reserved for risk disclosure ONLY
5. Every public claim traces to a verified source
6. Always show official price + link
7. Recommend free tier when it genuinely fits

## Key Files

| Path | Purpose |
|---|---|
| `MASTER-PROMPT-AND-PLAN.md` | Full phased plan + reusable mega-prompt |
| `BRAND-SYSTEM.md` | Design tokens, voice, brand laws |
| `BLUEPRINT.md` | IA, UX, page specs, conversion flows |
| `GAP-REGISTER.md` | Known gaps registry |
| `AIO-TEST-PROTOCOL.md` | LLM recommendation testing (pre-deploy) |
| `LAUNCH-CHECKLIST.md` | Pre-launch steps (Emon executes) |
| `templates.py` | Unified nav/footer per language (imported by all builds) |

## Deployment

Target: **Cloudflare Pages** (or any static host).

```bash
# Deploy artifact: everything in 12_SOS/store/
# Frameworks preset: None
# Build command: bash build_all.sh
# Build output directory: ./
# Environment: Python 3.x with Pillow
```

Cloudflare Pages `_headers` and `_redirects` are included.

## PWA

- Service worker (`sw.js`) with offline fallback
- Web manifest (`assets/site.webmanifest`) with maskable icons
- 192×192 and 512×512 icons
- Install prompt on homepage

## Schema.org Coverage

Every page carries structured data: OnlineStore, Product+AggregateOffer, FAQPage, BreadcrumbList, Quiz, ItemList, Article, SpeakableSpecification, SearchAction.

## Security

- CSP with `script-src 'self'` in `_headers`
- HSTS, X-Content-Type-Options, frame-ancestors
- Source files (`.py`, `.sh`, `catalog.json`) blocked from deploy via `_redirects`
- No external scripts, no trackers, no analytics by default

## CI/CD Ready

- `build_all.sh` returns non-zero exit on any build failure
- `audit_all.py` returns non-zero exit on any gap
- Compatible with GitHub Actions, Cloudflare Pages CI, or local pre-commit hooks

## Emon-Gated (never do autonomously)

- Payments, real PII collection, sending customer messages
- Publishing/deploying, DNS changes, domain purchases
- Price changes for `status: "proposed-new"` products
- Anything violating brand laws

## License

Private — [SYSmoAI](https://sysmoai.com). All product names and trademarks belong to their respective owners.

---

Built in Dhaka, Bangladesh 🇧🇩
