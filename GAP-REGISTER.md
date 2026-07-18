---
date: 2026-07-13
type: gap-register
status: fixing
tags: [store, audit, gaps]
---

# Store Gap Register — Adversarial Audit (beyond audit_all.py)

> Found by attacking my own build. Grouped into fix steps; each ends with extended-harness audit.

## 🔴 F1 — INTEGRITY GAPS (brand-critical — the store's whole edge is honesty)

| # | Gap | Why it's serious |
|---|---|---|
| 1 | **Fabricated testimonials** on homepage — invented names/cities/quotes ("Rakib H., Dhaka") | Fake reviews = the exact sin we accuse competitors of. Violates our own honesty invariant. |
| 2 | **Fake live-order ticker** — simulated "Dhaka ordered X · 7 min ago" timestamps | Manufactured social proof. Must become real-facts rotation (real lifetime order counts). |
| 3 | Warranty page claims "median resolution 40 minutes" — invented statistic | Unverifiable claim; align to the real written promise (1 hour). |

## 🟠 F2 — MISSING ASSETS

4. No favicon (any format) · 5. Organization schema references `/assets/logo.png` which **doesn't exist** · 6. No `og:image` anywhere → ugly social shares · 7. No apple-touch-icon · 8. No web manifest.

## 🟡 F3 — DISCOVERABILITY GAPS

9. **Blog posts are orphaned** — no blog index page, no links from homepage/footer → crawl-depth problem for the 6 traffic pages. 10. Product pages don't link to relevant guides (internal-link equity wasted).

## 🟡 F4 — DRIFT & MAINTAINABILITY GAPS

11. Homepage is hand-written: bestseller prices/official-strikes/counts ("49", "৳1,320") will silently drift from catalog.json. 12. Bundle cards on homepage hardcoded. 13. No single build orchestrator (`build_all.sh`) or store README. 14. `audit_all.py` doesn't check: homepage-vs-catalog price consistency, favicon/og presence, fake-testimonial patterns, ticker honesty.

## 🟢 F5 — DEPLOY HARDENING

15. No `_headers` (security headers for CF Pages) · 16. No `_redirects` · 17. No self-referencing hreflang · 18. Launch-checklist lacks 404-routing note per host.

## Fix order
**F1 now** (integrity first, always) → F2 assets → F3 blog index + linking → F4 generate homepage + extend harness → F5 deploy files → final full audit.
