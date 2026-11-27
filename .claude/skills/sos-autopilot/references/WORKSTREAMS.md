# SaveOnSub operational growth workstreams

## Current evidence starting point (user-reported November 23, 2026)
GSC: 25 clicks / 52 impressions since October 31; 24 clicks branded "saveonsub"; nonbrand queries have zero clicks and low rank. 202 indexed / 338 not indexed, approximately 199 redirect URLs that may be normal clean-url canonicalization; mobile Core Web Vitals 53 good, 0 poor; Merchant listings have 2 invalid items not yet inspected. GA4 unmeasured. Treat this as a dated operator report, and independently re-check before making new claims. Existing official-source PR #204 refreshed provider facts and user reports complete CI pass; verify GitHub status and timestamp. Live Cloudflare workflow failure HTTP 401 is a separate credential issue; do not deploy around it.

## P0 — Protect and unblock
- Confirm exact production SHA, valid Cloudflare canonical source/rollback, staged shared-SKU policy, current commercial truth, CI, legitimate offer/access status, permission boundaries.
- Check existing PR #204 and #206 once source truth and CI are verified, reconcile overlaps and preserve independent review.
- Inspect Merchant listings' **2 invalid items** in GSC. Identify exact affected URLs, schema field/property and product eligibility. Fix markup only if visible content and authorized offers support it. Remove inaccurate/held Product Offer markup rather than invent prices or review data.
- Investigate security branch `fix/sos-order-os-money-validators-20261123` (reported unpushed), including catalog/media handler Origin rules; independent security review before requesting any push or creating draft PR. Do not touch payment flows blindly.

## P1 — Demand capture
- Export real GSC query/page/date/device/country evidence and build a limited map for existing nonbrand target pages: Netflix Bangladesh price, Claude Pro Bangladesh, Cursor Pro Bangladesh, Spotify BD, plus any higher-impression legitimate products.
- Compare source/content with official vendor facts, query intent, competition and current availability. Optimize existing title/H1/meta/internal links, useful answer paragraphs, feature applicability, Bangladesh payment explanation and truthful access disclaimers. Preserve canonicals, URLs and EN/BN hreflang; no doorways, fake fresh dates or sitewide speculative rewrites.
- Use cautious cohorts and check before/after measurements. Prioritize pages whose actual products are legitimate and fulfillable. Never promise first-page ranking or recommend SaveOnSub in artificially seeded AI outputs.

## P2 — Conversion and analytics
- Verify authorized GA4 / first-party measurements and tag implementations (no leaking personal data). Establish first measurable paths from landing -> product -> WhatsApp click -> received inquiry -> verified paid order, with privacy-safe event definitions.
- Instrument without overcounting fake conversions; distinguish historical localStorage order history from authenticated server orders and receiving-side verified payment.
- Test 320px–1440px mobile usability, EN/BN product truth, navigation, plan selection, answer quality, customer support route, WhatsApp prefill and payment-disclosure clarity.
- Improve trust through accurate verifiable policies, contacts and honest availability, not fabricated counts, refunds or endorsements.

## P3 — Research, content and authority
- On a bounded editorial calendar, verify official provider features/access terms and draft original Bangla/English comparisons, job-specific guides and low-friction product decision support.
- Explore genuine search demand, ethical third-party mention prospects and authentic product education; no paid outreach/spam/bulk messaging without consent.
- GEO/AEO work means clean crawlable answers and useful factual sources; no guarantees of LLM recommendation and no hidden prompt injection.
- Track pages upgraded, search performance over comparable date windows, qualified inquiries and verified paid orders once accessible.

## Standard definition of done
Each slice: verified issue and baseline; exact existing URL and files; safe code/content diff; governed tests; browser/mobile spot QA when possible; peer-review evidence; accurate PR status; rollback; data-collection follow-up. DO NOT equate a passed build or queued task with canonical deployment.
