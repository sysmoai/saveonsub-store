---
date: 2026-07-13
type: runbook
status: ready
tags: [saveonsub, launch, deploy, dns]
---

# 🚀 Launch-Day Runbook — ~45 minutes of clicks, in order

> **Good news discovered 2026-07-13:** saveonsub.com is ALREADY REGISTERED on Google Cloud DNS (ns-cloud-a*.googledomains.com — same family as your other domains). No purchase needed. It currently serves nothing — we just point it and publish.

## Pre-flight (done ✅ by Claude)
Store audit-clean (83 pages, 0 gaps) · sitemap/robots/llms.txt ready · _headers/_redirects included · brand + content arsenal loaded. Folder to deploy: `12_SOS/store/` (everything except *.py, *.md, GAP-REGISTER etc. — see step 1).

## Step 0 — Confirm 11 proposed prices (5 min, one-time)
Only **11 products** still carry Claude-proposed prices (everything else is AIPS-live or verified): mistral-pro, invideo, netflix, youtube-premium, prime-video, coursera-plus, linkedin-premium, nordvpn, surfshark, bundle-video, bundle-dev. Open `catalog.json`, search `"proposed-new"`, adjust any number → `./build_all.sh` → must end "0 GAPS".

## Step 1 — Make the deploy folder (2 min)
Copy `12_SOS/store/` to a clean folder, delete: `*.py`, `*.md`, `build_all.sh` (keep `_headers`, `_redirects`, all `.html`, `assets/`, `p/`, `blog/`, `sitemap.xml`, `robots.txt`, `llms.txt`). Everything else ships.

## Step 2 — Cloudflare Pages deploy (10 min, free)
1. dash.cloudflare.com → Workers & Pages → **Create → Pages → Upload assets**
2. Project name: `saveonsub` → drag the deploy folder → Deploy
3. You get `saveonsub.pages.dev` — click through it once; test cart + checkout + quiz on your phone.
4. Custom domains → Add → `saveonsub.com` (+ `www`). Cloudflare shows the DNS records needed →

## Step 3 — DNS (5 min, in Google Cloud DNS console where the domain lives)
Add exactly what CF Pages asks (typically):
- `saveonsub.com` → CNAME/ALIAS → `saveonsub.pages.dev`
- `www` → CNAME → `saveonsub.pages.dev`
(SSL auto-provisions in ~15 min.)

## Step 4 — Email authentication BEFORE any outreach (5 min)
In the same DNS zone add:
- TXT `_dmarc.saveonsub.com` → `v=DMARC1; p=none; rua=mailto:sysmoai.com@gmail.com`
- If sending mail from this domain later: set up Zoho like the other domains + its SPF/DKIM records then.

## Step 5 — Get indexed (10 min)
1. search.google.com/search-console → Add property `saveonsub.com` (DNS TXT verification — paste record in the same zone) → Sitemaps → submit `https://saveonsub.com/sitemap.xml`
2. bing.com/webmasters → Import from Search Console (one click) 
3. Verify `https://saveonsub.com/llms.txt` and `/robots.txt` load in a browser.

## Step 6 — Analytics (3 min, no cookie banner needed)
Cloudflare Pages project → Web Analytics → enable. (JS snippet optional; CF measures at edge.)

## Step 7 — First-week ignition (the human part)
Day 1: FB post #1 from the bank + tell the story. Day 2: win-back batch 1 (20 msgs from AIPS list pointing to the store, WHATSAPP-FLOWS templates). Day 3-7: 3 more posts, answer every WhatsApp inside 15 min, log the first AIO test baseline (scores will be 0 — that's the "before" picture).

## Day-30 rituals (already documented)
Price re-verify (1st) · AIO test (15th) · review asks flowing automatically via T+7 · weekly KPI line in the vault weekly review.

## Rollback
CF Pages keeps every deployment — one click restores the previous version. The git repo + `_BACKUPS/` bundle hold everything else. Nothing about this launch is irreversible except the good kind.
