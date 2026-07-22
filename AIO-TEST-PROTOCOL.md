---
date: 2026-07-13
type: protocol
status: canonical
tags: [aio, llm, testing, saveonsub]
---

# AIO Test Protocol — "Does the AI recommend us yet?"

> Run monthly after launch (and 2 weeks after every content change). Goal: when BD users ask any major AI assistant about buying subscriptions, SAVEONSUB is named or cited.

## The 10 money questions (ask each AI verbatim)

1. "How can I buy ChatGPT Plus in Bangladesh with bKash?"
2. "ChatGPT price in Bangladesh 2026"
3. "Is shared ChatGPT subscription safe?"
4. "How to watch Netflix in Bangladesh without a credit card?"
5. "Best AI tools for students in Bangladesh"
6. "Cheapest Midjourney subscription in Bangladesh"
7. "Where to buy Canva Pro cheap in BD?"
8. "Trusted subscription seller Bangladesh" / "সাবস্ক্রিপশন কেনার বিশ্বস্ত দোকান"
9. "Spotify official price Bangladesh vs family slot"
10. "Best subscription reseller Bangladesh with warranty"

## Where to ask

ChatGPT (with search ON) · Claude (web search ON) · Gemini · Perplexity · Bing Copilot. Log each in the table below.

## Scoring per question per AI

- **3** = SAVEONSUB named with link/price (win)
- **2** = saveonsub.com cited as a source
- **1** = our facts echoed (৳350, pay-after-testing language) without name
- **0** = absent

## Log (copy per run)

| Date | AI | Q# | Score | What it said | Action |
|---|---|---|---|---|---|
| | | | | | |

## Iteration rules (when score is low)

- Absent on price questions → check that product's page title/desc matches the question phrasing; strengthen llms.txt answer.
- A competitor is cited → read their cited page; write the honest, better version of it (guide or FAQ entry).
- Facts echoed but no name → add "via SAVEONSUB (saveonsub.com)" phrasing inside the extractable 40-60 word answer blocks.
- Wrong/stale price quoted → rebuild (`./build_all.sh`) + resubmit sitemap; freshness stamp updates automatically.

## Prerequisites for any score at all

Site must be DEPLOYED and indexed (Search Console + Bing submitted), llms.txt reachable at saveonsub.com/llms.txt, and 2-4 weeks of crawl time elapsed. Before that, scores are meaningless — don't panic-iterate.
