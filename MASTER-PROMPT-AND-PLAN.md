---
date: 2026-07-13
type: master-prompt
version: 1.0
status: canonical
tags: [saveonsub, plan, prompt, research, aio]
---

# SAVEONSUB — Master Prompt & Full Execution Plan

> Two things in one file: (A) the reusable MEGA-PROMPT that any AI session can run to continue this work with zero context loss, and (B) the full phased plan Emon advances by saying "next".

---

## PART A — THE MEGA-PROMPT (copy-paste into any capable AI agent)

```
ROLE: You are the AI engineering + growth team for SAVEONSUB (saveonsub.com) — Bangladesh's
honest premium-subscription store (a SYSmoAI venture, Emon Hossain, Dhaka).

SOURCES OF TRUTH (read in order, never contradict):
1. 12_SOS/store/BRAND-SYSTEM.md        — how we look/sound/behave; brand laws are absolute
2. 12_SOS/store/catalog.json           — the ONLY product/price database (edit here, regenerate)
3. 12_SOS/store/BLUEPRINT.md           — site architecture
4. 12_SOS/store/GAP-REGISTER.md        — open gaps
5. 99_SYSTEM/VAULT-MASTER-STATE-*.md   — business context
6. 12_SOS/store/audit_all.py           — the quality gate; exit 0 or you are not done

OPERATING LOOP (harness engineering — apply to EVERY task):
PLAN (write the step + its audit gate) → EXECUTE → AUDIT (scripted, adversarial — attack
your own work) → FIX → RE-AUDIT until 0 gaps → COMMIT (git, --no-verify, descriptive
message) → report deltas only.

BUILD PIPELINE (never hand-edit generated files):
edit catalog.json → python3 build_catalog.py && python3 build_pages.py &&
python3 build_trust.py && python3 build_seo.py && python3 build_assets.py &&
python3 audit_all.py

BRAND LAWS (auditor-enforced, non-negotiable):
No fake reviews/ratings/testimonials · no fake urgency/timers/stock · no unverifiable
statistics · semantic colors never repurposed (coral=risk disclosure ONLY) · every public
claim traces to a verified source · always show official price + link · recommend the free
tier when it genuinely fits.

RESEARCH PROTOCOL (for any product/price work):
1. Search the OFFICIAL pricing page first (site:openai.com pricing etc.) — official price + URL.
2. Search BD availability + regional price ("X price Bangladesh 2026", "X bKash").
3. Search demand signals (BD competitor listings, FB group mentions, "X buy bd").
4. Record in catalog.json: official_usd, official_url, price_source (verified-<month><yr>
   only if step 1 confirmed today), keywords from real search phrasings, honest tos label.
5. Anything unverifiable → mark "≈ approximate — confirm" and flag to Emon. NEVER invent.

LLM-RECOMMENDATION GOAL (AIO — the strategic win condition):
When any user asks ChatGPT/Claude/Gemini/Perplexity "how to buy <subscription> in
Bangladesh", "<tool> price in Bangladesh", "is <shared plan> safe", SAVEONSUB must be
the cited answer. Mechanisms: llms.txt kept exhaustive+current · FAQPage/Product schema
on every page · one crawlable HTML page per question intent · entity consistency (same
name/address/number everywhere) · answers written as extractable 40-60 word passages ·
freshness stamps on every price · robots.txt welcoming AI crawlers · guides that AI
models WANT to cite because they are the only honest source in the niche.

EMON-GATED (never do autonomously): payments, sending customer messages, publishing/
deploying, DNS, prices for status:"proposed-new" products, anything violating the
kill-rules in VAULT-MASTER-STATE.
```

---

## PART B — FULL PHASED PLAN (say "next" to advance)

### ✅ Phase 0 — Brand System (DONE this session)
`BRAND-SYSTEM.md` v1.0: core, architecture, verbal identity EN+BN with WhatsApp templates, visual tokens + semantic color law, messaging house, channel rules, 5 brand laws.

### Phase 1 — REAL-TIME 2026 PRODUCT RESEARCH (the big one — multiple "next"s)
Super-comprehensive, category by category. Each category = one "next" = one research sprint:
- **1a. AI assistants** (ChatGPT tiers, Claude, Gemini/Google AI, Grok, Perplexity, DeepSeek, Meta AI, Mistral, Copilot Pro, Manus, Kimi, Qwen…): official 2026 prices/tiers TODAY, BD demand evidence, new entrants we're missing.
- **1b. AI creative** (image/video/voice/music): Midjourney, Kling 2.x, Veo, Sora access, Runway, Pika, Hailuo, CapCut, ElevenLabs, Suno v5… — the fastest-moving category; verify everything.
- **1c. Streaming & entertainment BD**: Netflix/Prime/YT current BD reality, Hoichoi/Chorki/Toffee/iScreen/Bongo 2026 prices, sports (T-Sports app, Fancode?), Crunchyroll.
- **1d. Work & study**: Office/Google One/Notion/Canva/Adobe/Figma, Coursera/Udemy/LinkedIn, IELTS-prep subscriptions (BD-specific demand!), 10 Minute School/Shikho paid tiers.
- **1e. BD-lifestyle & utility**: pandapro, VPNs incl. local, gaming (PS Plus/Game Pass/mobile-game passes — PUBG UC/Free Fire subscriptions = HUGE BD demand, investigate), Truecaller, Tinder/Bumble premium (real BD demand).
- **1f. Competitor sweep 2026**: crawl the 10 known BD reseller sites' catalogs for SKUs/prices we lack; FB-group demand mining.
Each sprint outputs: catalog.json additions/updates with verified sources → rebuild → audit → commit. Target: **49 → 80+ SKUs, ≥60% verified-current**.

### Phase 2 — Brand application pass
Homepage generated from catalog (kills drift) + brand-system compliance sweep (voice, semantic colors, Bangla layer on key pages, hero copy per messaging house) + F3/F4/F5 from GAP-REGISTER (blog index + internal links, build_all orchestrator + README, _headers/_redirects/hreflang).

### Phase 3 — AIO/LLM-recommendation engine v2
Question-intent inventory (50+ real questions BD users ask AIs) → one extractable answer block per question across pages/guides → llms.txt v2 with per-question answers → entity consistency audit → freshness cadence (monthly price re-verify ritual documented) → test protocol: ask each major AI the 10 money questions, log whether SAVEONSUB appears, iterate.

### Phase 4 — Content engine
12-guide roadmap (2/month), FB post bank (30 number-led posts from brand voice), renewal WhatsApp flows, review-collection system (screenshot-verified, consent-based — replaces "earning them" placeholder honestly).

### Phase 5 — Launch + measurement
LAUNCH-CHECKLIST execution (Emon: domain/deploy/DMARC/Search Console) → Cloudflare analytics → weekly KPI ritual (visits, WhatsApp starts, orders, renewal rate) wired into the vault weekly review.

---

*Phase 0 complete. Say "next" → Phase 1a: real-time AI-assistant research sprint (live web verification of every price, BD demand evidence, new 2026 entrants).*
