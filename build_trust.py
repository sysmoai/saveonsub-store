#!/usr/bin/env python3
"""SAVEONSUB build step 3: trust pages (faq/warranty/refund/privacy/terms/about/how-to-order/404).
Run locally: python3 build_trust.py"""
import json, html
from templates import nav_en, nav_bn, footer_en, footer_bn

def esc(s): return html.escape(str(s), quote=True)

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://saveonsub.com/{slug}.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/{slug}.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/{slug}.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/{slug}.html">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/{slug}.html">
<meta name="theme-color" content="#06181a">{robots}
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="manifest" href="assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="assets/style.css">
{schema}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{{nav_en()}}
<main id="main"><div class="wrap" style="max-width:820px">
  <div class="crumbs"><a href="index.html">Home</a> › {crumb}</div>
  {body}
</div></main>
<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="WhatsApp">💬 WhatsApp</button>
{{footer_en()}}
<script src="assets/app.js"></script>
</body>
</html>"""

def faq_schema(qas):
    return '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]
    }, ensure_ascii=False) + '</script>'

def details(qas, open_first=True):
    out = ""
    for i, (q, a) in enumerate(qas):
        out += f"<details{' open' if i==0 and open_first else ''}><summary>{esc(q)}</summary><p>{a}</p></details>"
    return out

pages = {}

# ---------- FAQ (22 questions — every playbook objection) ----------
FAQS = [
 ("Is SAVEONSUB legit? How do I know you're not a scam?", "Fair question — BD is full of subscription scams. Proof: Bangladesh's Subscription OS trusted in Bangladesh, part of the verifiable SYSmoAI family (sysmoai.com, aipremiumshop.com), public WhatsApp with a human reply, and a <b>pay-after-testing</b> option where we send access BEFORE you pay. Scammers can't afford to do that."),
 ("Why is it so cheap? What's the catch?", "Two honest reasons: (1) shared plans split one subscription's cost across several users — that's the discount, and it's also why providers' terms don't allow it (the 'catch', which we label on every product and cover with warranty); (2) personal plans use regional pricing and bulk activation. We show the official price next to ours so you always see what you're saving and why."),
 ("Will other people see my ChatGPT chats on a shared plan?", "No. ChatGPT keeps every user's conversations private — other seat-holders cannot see your chats, history or custom instructions. Only the subscription cost is shared, never your data."),
 ("What's the difference between Shared, Personal and Official?", "<b>Official</b> = you pay the provider directly, we just guide/activate (e.g. Spotify BD ৳219). <b>Personal</b> = a subscription on YOUR OWN email — full control, lowest risk. <b>Shared</b> = a seat on a multi-user plan — 70-85% cheaper, provider terms prohibit it, so seats occasionally reset; our warranty replaces them within 1 hour."),
 ("Can a shared account get banned? What happens then?", "Yes, it happens — that's the honest trade-off for the price. When it does: message us, replacement within 1 hour during support hours, 7-day guarantee on every shared seat. If we can't replace, you get a refund for unused days."),
 ("How fast is delivery?", "Instant products: 5–15 minutes on WhatsApp. Fast products: 1–2 hours. Managed personal accounts: 1–2 days. The SLA is printed on every product page — if we miss it badly, ask for a free extension."),
 ("How do I pay? I don't have a card.", "bKash, Nagad or Rocket send-money — that's the point. No card, no bank account, no international payment. At checkout you get our merchant number (+880 1305-869242) with a copy button and your order ID as reference."),
 ("What is pay-after-testing?", "For nervous first-timers: we send the access first, you verify it works, then you pay within an hour. Available on most instant products for first orders. No other BD store offers this — because they can't."),
 ("Do you auto-charge renewals?", "Never. There is no auto-charge — you pay manually each time. We send a WhatsApp reminder 3 days before expiry with a one-tap renewal link. Ignore it and the subscription simply lapses. Your money stays yours."),
 ("Can I get a refund?", "Yes — see the <a href='refund.html' style='color:var(--green2)'>refund policy</a>. Short version: not delivered in 24h → full refund; dead seat we can't replace → refund for unused days; you changed your mind before delivery → full refund; after successful delivery → replacement-first, refund if we fail."),
 ("Can I get a discount?", "Three honest ways: pay 3 months upfront (10% off), refer a friend (you both get ৳100 off), or students get ৳100 off ChatGPT personal plans with a student ID. Ask on WhatsApp."),
 ("Is my payment information safe?", "We never see your bKash PIN or account — you send money from YOUR app to our merchant number. We only receive the payment notification. We don't store card numbers because we never touch cards."),
 ("Which AI should I buy? I'm confused.", "Take the 60-second <a href='quiz.html' style='color:var(--green2)'>Find My AI quiz</a> — 4 questions, one honest recommendation. Or ask a human on WhatsApp. If a free tier fits your usage, we'll tell you to use that instead. Seriously."),
 ("I'm a student — what's the cheapest way to get AI tools?", "Real talk: GitHub Copilot is FREE with the Student Pack, Spotify BD student is ৳109 official, Canva Education is free for eligible institutions. For the rest: ChatGPT shared ৳350 or the Research Bundle ৳600 are the best student deals. We'll always point out the free path first."),
 ("Do you sell accounts with MY name on certificates (Coursera etc.)?", "Shared Coursera prints the account-holder's name on certificates — useless for your CV. If you need YOUR name, take the Personal plan. We say this on the product page before you pay, not after."),
 ("What devices/apps do these work on?", "Same as official — you're using the real service. Shared seats sometimes limit simultaneous devices (shown on the product). Personal plans have no restrictions."),
 ("Can I upgrade from shared to personal later?", "Yes — pay the difference any time and we migrate you. Many customers start shared at ৳350, then upgrade to personal once the tool starts earning them money."),
 ("Do you offer team/business plans?", "Yes — ChatGPT Business seats, bulk Canva, and custom team setups. Message WhatsApp with your team size; bulk pricing starts at 3+ seats (10-15% off)."),
 ("What happens when my subscription expires?", "It just stops — no auto-charge, no debt. You'll have gotten a WhatsApp reminder 3 days before. Renew with one tap or walk away; your choice, no pressure."),
 ("Why should I trust you over Facebook/Telegram sellers?", "FB/Telegram sellers vanish when a seat dies — no brand, no website, no recourse. We have a public brand (SYSmoAI family), a written warranty, a refund policy, this store, and a 2-year track record. When something breaks, we're still here at the same number."),
 ("Is buying shared subscriptions legal in Bangladesh?", "It's not illegal for you — it's a violation of the provider's terms of service (their contract with the account holder), not BD law. Worst case for you: the seat gets reset and we replace it. We label this honestly so you decide with full information."),
 ("Do you have a physical office?", "We operate online-first from Dhaka with registered company paperwork in progress (SYSmoAI). All support runs through WhatsApp with real humans — usually the founder's team directly."),
 ("What is the official ChatGPT price in Bangladesh and why can't I pay with bKash?",
  "ChatGPT Plus costs $20/month (~৳2,200 as of July 2026). OpenAI only accepts international Visa/Mastercard — no bKash, no Nagad. Bangladesh has roughly 3 million credit cards for 170 million people. Resellers are the only path for the other 167 million. We sell shared from ৳350 (84% cheaper, warranty) and personal from ৳2,990."),
 ("Is Spotify available officially in Bangladesh?",
  "Yes — Spotify launched BD pricing in 2024: Individual ৳219/mo, Student ৳109, Duo ৳299, Family ৳379. Pay with local methods including bKash. We recommend official for zero risk. We also offer family slots at ৳129 — but official is the right answer for most people, and we say that."),
 ("What happens if I get scammed by a Facebook seller?",
  "The seller blocks you and disappears. No brand, no website, no recourse. This happens thousands of times daily across BD subscription groups. Buy only from sellers with a real website, a written warranty, a refund policy, and a public WhatsApp number active for over a year. Scammers cannot sustain those."),
 ("Which AI tools are actually worth it for Bangladeshi freelancers?",
  "Fiverr thumbnails → Midjourney ৳1,199 or Leonardo ৳599. Copywriting → ChatGPT Plus ৳350 or Jasper ৳1,520. Video editing → CapCut Pro ৳399. Web dev → GitHub Copilot FREE for students, Cursor ৳590. The Research Bundle (ChatGPT+Perplexity ৳600) covers 80% of use. Start free, buy one tool when free stops you, stack slowly."),
 ("How big is the Bangladesh subscription market?",
  "BD ecommerce crossed $4 billion in 2026. Mobile money (bKash 70M users, Nagad, Rocket) processes more transactions than cards by far. Digital subscriptions are one of the fastest-growing segments because every global service assumes credit card access. Honest resellers disclose the mechanism; dishonest ones sell 'lifetime Netflix ৳999' — impossible since Netflix charges monthly."),
 ("Can I resell subscriptions to others?",
  "Legally in Bangladesh: yes — no law prohibits reselling digital access. Practically: only if you understand provider ToS and can absorb seat-reset risk. We have helped 50+ people start small reseller operations — message WhatsApp for honest advice. But reselling without telling customers about shared-seat reality is scamming. Do not do it."),
 ("Why publish competitor prices?",
  "Because hiding them is how dishonest sellers win. FanFlix sells ChatGPT at ৳500, we sell at ৳350 with warranty. BD Subscription lists 250+ products. We publish the full picture because trust earns repeat customers, and repeat customers are the only business model that survives in BD."),
]
body = f"""<span class="pill">FAQ</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Every question. <span class="grad-text">Straight answers.</span></h1>
<p class="sub">30 real questions from Bangladesh's Subscription OS — answered the way we'd want to be answered.</p>
<div class="mt3">{details(FAQS)}</div>
<div class="notice green mt3">Didn't find yours? <a href="https://wa.me/8801305869242?text=Question:" style="color:var(--green2);font-weight:800">Ask on WhatsApp</a> — human reply, usually in minutes.</div>"""
pages['faq'] = dict(title="FAQ — 22 Straight Answers | SAVEONSUB", desc="Is it safe? Will others see my chats? Refunds? Ban risk? Every question about buying subscriptions in Bangladesh — answered honestly.", crumb="FAQ", body=body, schema=faq_schema([(q, html.unescape(a).replace('<b>','').replace('</b>','')) for q,a in FAQS[:10]]), robots="")

# ---------- Warranty ----------
body = """<span class="pill">🛡️ WARRANTY</span>
<h1 style="font-size:clamp(26px,4vw,38px)">A warranty that <span class="grad-text">actually means something</span>.</h1>
<p class="sub">In writing, on every product, trusted in Bangladesh.</p>
<div class="tbl mt3"><table>
<tr><th>Plan type</th><th>Coverage</th><th>Replacement time</th><th>If we can't fix it</th></tr>
<tr><td><span class="tos shared-med">Shared</span></td><td>7 days from delivery</td><td>Within 1 hour (support hours 9am–12am)</td><td>Refund for unused days</td></tr>
<tr><td><span class="tos personal">Personal</span></td><td>30 days from delivery</td><td>Within 1 hour</td><td>Full refund</td></tr>
<tr><td><span class="tos official">Official</span></td><td>Provider's own guarantee</td><td>We assist with provider support</td><td>—</td></tr>
</table></div>
<h2 class="mt3" style="font-size:21px">What's covered</h2>
<p class="sub" style="font-size:15px">Seat stops working, password reset by provider, account banned, plan downgraded by provider, activation failed. Basically: if what you paid for stops existing, we fix it or refund it.</p>
<h2 class="mt3" style="font-size:21px">What's not covered</h2>
<p class="sub" style="font-size:15px">You broke the seat rules we told you at delivery (changing the password on a shared account, adding extra devices beyond the limit, reselling your seat), or provider-side feature changes that affect ALL users including official ones (e.g. a model being retired).</p>
<h2 class="mt3" style="font-size:21px">How to claim</h2>
<p class="sub" style="font-size:15px">WhatsApp <b>+880 1305-869242</b> with your order ID and a screenshot. That's the whole process — resolved within the 1-hour promise during support hours.</p>
<div class="notice mt3">⏱️ Claims outside support hours (12am–9am) are handled first thing next morning — the warranty clock pauses, you lose nothing.</div>"""
pages['warranty'] = dict(title="Warranty — 1-Hour Replacement | SAVEONSUB", desc="7-day guarantee on shared seats, 30-day on personal plans, replacement within 1 hour. What's covered, what's not, and how to claim in one WhatsApp message.", crumb="Warranty", body=body, schema="", robots="")

# ---------- Refund ----------
body = """<span class="pill">↩️ REFUND POLICY</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Clear refunds. <span class="grad-text">No fine-print games.</span></h1>
<div class="tbl mt3"><table>
<tr><th>Situation</th><th>What you get</th><th>Timeline</th></tr>
<tr><td>Not delivered within 24h of payment</td><td><b>Full refund</b></td><td>Same day, to your bKash/Nagad</td></tr>
<tr><td>Cancelled before delivery</td><td><b>Full refund</b></td><td>Same day</td></tr>
<tr><td>Seat died in warranty, replacement failed</td><td><b>Refund for unused days</b></td><td>Within 24h of failed replacement</td></tr>
<tr><td>Wrong product delivered</td><td>Correct product or <b>full refund</b> — your choice</td><td>Within 1 hour</td></tr>
<tr><td>Changed mind after successful delivery</td><td>Replacement-first policy; refund case-by-case</td><td>Within 48h</td></tr>
</table></div>
<h2 class="mt3" style="font-size:21px">How refunds are paid</h2>
<p class="sub" style="font-size:15px">Back to the same bKash/Nagad/Rocket number you paid from — send-money, no fees deducted. We don't do store-credit-only games.</p>
<h2 class="mt3" style="font-size:21px">How to request</h2>
<p class="sub" style="font-size:15px">WhatsApp your order ID + reason. Refunds are approved by a human (usually within the hour), not a bot maze.</p>
<div class="notice green mt3">🤝 Still deciding? Use <b>pay-after-testing</b> on your first order and you'll never need this page.</div>"""
pages['refund'] = dict(title="Refund Policy — Same-Day, No Games | SAVEONSUB", desc="Full refund if not delivered in 24h. Unused-days refund on warranty failures. Paid back to your bKash same day. The whole policy in one table.", crumb="Refund Policy", body=body, schema="", robots="")

# ---------- Privacy ----------
body = """<span class="pill">🔒 PRIVACY</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Your data: <span class="grad-text">we barely want it.</span></h1>
<h2 class="mt3" style="font-size:21px">What we collect</h2>
<p class="sub" style="font-size:15px">Your WhatsApp number and name (because you message us), your order history (to honor warranties), and the email you want subscriptions activated on. That's it.</p>
<h2 class="mt3" style="font-size:21px">What we never collect</h2>
<p class="sub" style="font-size:15px">Your bKash PIN (impossible — you pay from your own app), card numbers (we don't take cards), passwords to your personal accounts (personal plans are activated ON your email — you set the password), browsing data (no invasive trackers; the cart lives in YOUR browser's localStorage, not our servers).</p>
<h2 class="mt3" style="font-size:21px">What we do with it</h2>
<p class="sub" style="font-size:15px">Deliver your order, honor your warranty, and send ONE renewal reminder 3 days before expiry. No spam lists, no data selling, no sharing with third parties except the provider activation itself.</p>
<h2 class="mt3" style="font-size:21px">Deletion</h2>
<p class="sub" style="font-size:15px">Message "delete my data" on WhatsApp — order history and contact gone within 72 hours (ends warranty coverage, which needs the records).</p>
<h2 class="mt3" style="font-size:21px">Shared-plan privacy</h2>
<p class="sub" style="font-size:15px">On shared subscriptions, other seat-holders can never see your usage: ChatGPT chats, Midjourney galleries (private mode), Spotify listening (family slots are separate accounts) are all per-user private. Where a product has a real privacy limitation, it's stated on that product's page.</p>"""
pages['privacy'] = dict(title="Privacy — We Barely Want Your Data | SAVEONSUB", desc="No PINs, no cards, no passwords, no tracking. What we collect (almost nothing), why, and how to delete it with one WhatsApp message.", crumb="Privacy", body=body, schema="", robots="")

# ---------- Terms ----------
body = """<span class="pill">📜 TERMS</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Terms of service — <span class="grad-text">readable edition.</span></h1>
<div class="mt3">
<details open><summary>1. Who we are</summary><p>SAVEONSUB is a subscription reseller and activation service operated by the SYSmoAI group, Dhaka, Bangladesh. We are independent — not affiliated with OpenAI, Netflix, Google or any provider whose products we resell/activate.</p></details>
<details><summary>2. What you're buying</summary><p>Exactly what the product page says: an <b>official</b> guided activation, a <b>personal</b> subscription on your own account, or a <b>shared</b> seat on a multi-user plan. Each label's meaning and risk is defined on every product page. Prices are per stated duration; no auto-renewal exists.</p></details>
<details><summary>3. Shared-plan reality (read this one)</summary><p>Shared seats violate most providers' terms of service. That's why they're cheap. The risk to you is seat interruption — covered by our warranty (replacement in 1 hour, 7-day guarantee). By buying a shared plan you accept this trade-off, which we disclose before purchase, not after.</p></details>
<details><summary>4. Your responsibilities</summary><p>Follow the seat rules given at delivery (don't change shared passwords, respect device limits, don't resell seats). Provide a working email/WhatsApp for delivery. Use your own bKash/Nagad for payment so refunds can find their way back.</p></details>
<details><summary>5. Warranty & refunds</summary><p>As per the <a href="warranty.html" style="color:var(--green2)">warranty</a> and <a href="refund.html" style="color:var(--green2)">refund</a> pages — those pages are part of these terms.</p></details>
<details><summary>6. What we're not liable for</summary><p>Provider-side changes affecting all users (feature removals, model retirements, price changes), your violation of provider terms beyond the shared-seat arrangement itself, and indirect losses. Our maximum liability is what you paid us for the affected order.</p></details>
<details><summary>7. Disputes</summary><p>Talk to us first — WhatsApp, human, usually fixed in an hour. Formal disputes fall under the laws of Bangladesh, courts of Dhaka.</p></details>
<details><summary>8. Changes</summary><p>Terms may change; the version on this page at your order time applies to that order.</p></details>
</div>"""
pages['terms'] = dict(title="Terms of Service — Readable Edition | SAVEONSUB", desc="Terms you can actually read: what you're buying, shared-plan reality, warranty, refunds, and liability — in plain language, 8 short sections.", crumb="Terms", body=body, schema="", robots="")

# ---------- About ----------
body = """<span class="pill">ABOUT US</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Built in Bangladesh, <span class="grad-text">for how Bangladesh actually pays.</span></h1>
<p class="sub mt2" style="font-size:16px">239 million mobile-money accounts. 3 million credit cards. Every global subscription assumes the card. SAVEONSUB exists for everyone else.</p>
<h2 class="mt3" style="font-size:21px">The story</h2>
<p class="sub" style="font-size:15px">We started in 2024 as AI Premium Shop — a WhatsApp-first store helping students and freelancers get ChatGPT without an international card. Bangladesh's Subscription OS and ~1,600 orders later, we learned two things: (1) BD buyers are the world's most price-aware customers, and (2) they've been burned so often that honesty is the only durable advantage. SAVEONSUB is the store rebuilt around those lessons — every plan labeled, every risk disclosed, official prices linked for verification.</p>
<h2 class="mt3" style="font-size:21px">The family</h2>
<div class="tbl mt2"><table>
<tr><th>Brand</th><th>What it does</th></tr>
<tr><td><a href="https://sysmoai.com" style="color:var(--green2)" rel="noopener">SYSmoAI</a></td><td>Parent company — AI consulting & systems (incorporating as SYSmoAI Private Limited)</td></tr>
<tr><td><a href="https://aipremiumshop.com" style="color:var(--green2)" rel="noopener">AI Premium Shop</a></td><td>Where it started — the original WhatsApp AI store</td></tr>
<tr><td><a href="https://aipremium.tools" style="color:var(--green2)" rel="noopener">AI Premium Tools</a></td><td>Sister store</td></tr>
<tr><td><a href="https://emonhossain.pro" style="color:var(--green2)" rel="noopener">Emon Hossain</a></td><td>Founder — AI systems strategist</td></tr>
</table></div>
<h2 class="mt3" style="font-size:21px">The promises</h2>
<p class="sub" style="font-size:15px">1) Honest labels on every plan — even when it costs us a sale. 2) A human answers WhatsApp — in Bangla or English. 3) If the free tier fits you, we'll say so. 4) Warranty in writing, refunds same-day. 5) Prices verified against official — check them yourself, the links are right there.</p>
<div class="heroctas mt3"><a class="btn btn-primary" href="all.html">Browse the store →</a><a class="btn btn-wa" href="https://wa.me/8801305869242?text=Hi!">💬 Say hello</a></div>"""
pages['about'] = dict(title="About — Built for How BD Actually Pays | SAVEONSUB", desc="Started 2024 as AI Premium Shop, Bangladesh's Subscription OS later rebuilt as SAVEONSUB: honest labels, bKash-first, human support. A SYSmoAI venture from Dhaka.", crumb="About", body=body, schema='<script type="application/ld+json">{"@context":"https://schema.org","@type":"AboutPage","name":"About SAVEONSUB","url":"https://saveonsub.com/about.html"}</script>', robots="")

# ---------- How to order ----------
howto_ld = {"@context":"https://schema.org","@type":"HowTo","name":"How to buy a subscription with bKash on SAVEONSUB","totalTime":"PT3M",
 "step":[{"@type":"HowToStep","position":1,"name":"Pick your product","text":"Browse all.html or take the Find My AI quiz. Add to cart — prices in taka, honest labels on every plan."},
 {"@type":"HowToStep","position":2,"name":"Send money via bKash/Nagad/Rocket","text":"At checkout, copy the merchant number +880 1305-869242 and send the total with your order ID as reference."},
 {"@type":"HowToStep","position":3,"name":"Confirm on WhatsApp","text":"Tap Confirm — a prefilled WhatsApp message with your order opens. Send it."},
 {"@type":"HowToStep","position":4,"name":"Receive in 5–15 minutes","text":"Credentials or invite arrive on WhatsApp. Warranty active from minute one."}]}
body = """<span class="pill">📖 HOW TO ORDER</span>
<h1 style="font-size:clamp(26px,4vw,38px)">First time? <span class="grad-text">3 minutes, start to delivered.</span></h1>
<div class="steps mt3" style="grid-template-columns:repeat(2,1fr)">
  <div class="step"><h3>Pick your product</h3><p>Browse <a href="all.html" style="color:var(--green2)">all products</a> or take the <a href="quiz.html" style="color:var(--green2)">quiz</a>. Every plan shows the price, the honest risk label and the delivery time. Tap <b>Add to cart</b>.</p></div>
  <div class="step"><h3>Send the money</h3><p>Open bKash/Nagad/Rocket → <b>Send Money</b> → paste our number <b>+880 1305-869242</b> (copy button at checkout) → amount = your cart total → reference = your order ID.</p></div>
  <div class="step"><h3>Confirm on WhatsApp</h3><p>Tap the big green button. A WhatsApp message opens with your whole order pre-written. Just press send. Add your TxnID if you have it — it speeds things up.</p></div>
  <div class="step"><h3>Get delivered</h3><p>Instant products arrive in <b>5–15 minutes</b> with setup instructions. Read the seat rules (shared plans), enjoy, and save our number — warranty claims are one message away.</p></div>
</div>
<h2 class="mt3" style="font-size:21px">Nervous about paying first?</h2>
<p class="sub" style="font-size:15px">Use <b style="color:var(--green2)">Pay-After-Testing</b> at checkout — we send access before you pay on eligible first orders. You verify, then you pay. That's how confident we are.</p>
<h2 class="mt3" style="font-size:21px">Common first-order mistakes (avoid these)</h2>
<p class="sub" style="font-size:15px">Forgetting the order ID in the reference (we'll still find you, but slower) · sending to a number from ANY other website (only trust the number shown at OUR checkout) · changing the password on a shared seat (kills the seat for everyone — warranty won't cover it).</p>
<div class="heroctas mt3"><a class="btn btn-primary" href="all.html">Start shopping →</a></div>"""
pages['how-to-order'] = dict(title="How to Order with bKash — 3-Minute Guide | SAVEONSUB", desc="Pick product → send money via bKash/Nagad → confirm on WhatsApp → delivered in 5–15 min. Full first-timer guide including pay-after-testing.", crumb="How to Order", body=body, schema='<script type="application/ld+json">'+json.dumps(howto_ld,ensure_ascii=False)+'</script>', robots="")

# ---------- 404 (recovery-optimised: search + popular products + smart path) ----------
_cat404 = json.load(open('catalog.json'))
_ncount = len(_cat404['products'])
_pop = sorted([p for p in _cat404['products'] if p.get('bestseller_rank',0)>0], key=lambda x: x['bestseller_rank'])[:6]
_popcards = "".join(f'<a class="pcard" href="p/{p["id"]}.html"><span class="icon">{p["icon"]}</span><h3>{esc(p["name"].replace("🎁 ",""))}</h3><div class="price">৳{min(pl["bdt"] for pl in p["plans"]):,}</div></a>' for p in _pop)
body = f"""<div class="center" style="padding:36px 0">
<span style="font-size:64px">🔍</span>
<h1 style="font-size:clamp(26px,4vw,40px)">Page not found — <span class="grad-text">but the deals are.</span></h1>
<p class="sub" style="margin:12px auto 20px">The link may be old. Search {_ncount} subscriptions, or grab a bestseller below.</p>
<form onsubmit="event.preventDefault();var q=document.getElementById('q404').value.trim();location.href='all.html'+(q?('?q='+encodeURIComponent(q)):'')" style="max-width:460px;margin:0 auto;display:flex;gap:8px">
  <input id="q404" placeholder="Search ChatGPT, Netflix, Canva…" autocomplete="off" aria-label="Search products" style="flex:1">
  <button class="btn btn-primary" type="submit">Search</button>
</form>
<div class="heroctas" style="justify-content:center;margin-top:18px">
  <a class="btn btn-ghost" href="all.html">Browse all {_ncount} →</a>
  <a class="btn btn-ghost" href="quiz.html">🧭 Find My AI</a>
  <a class="btn btn-wa" id="ask404" href="https://wa.me/8801305869242?text=Hi!%20I%20was%20looking%20for%20something%20on%20the%20site">💬 Ask us</a>
</div>
</div>
<h2 style="font-size:20px;text-align:center;margin-top:10px">Popular right now</h2>
<div class="grid g3 mt2">{_popcards}</div>
<script>
// Smart recovery: tell WhatsApp what URL the visitor tried to reach
(function(){{
  var el=document.getElementById('ask404'); if(!el) return;
  var path=location.pathname+location.search;
  el.href='https://wa.me/8801305869242?text='+encodeURIComponent('Hi! I hit a broken link on your site: '+path+' — what were you offering there?');
}})();
</script>"""
pages['404'] = dict(title="Page Not Found | SAVEONSUB", desc=f"That page moved — the deals didn't. Search or browse {_ncount} subscriptions at honest BD prices with bKash.", crumb="404", body=body, schema="", robots='\n<meta name="robots" content="noindex">')

# ---------- Contact / Support (BD trust builder) ----------
contact_ld = {"@context":"https://schema.org","@type":"ContactPage","name":"Contact SAVEONSUB","url":"https://saveonsub.com/contact.html",
 "mainEntity":{"@type":"Organization","name":"SAVEONSUB","telephone":"+8801305869242","email":"support@saveonsub.com","areaServed":"BD",
 "contactPoint":{"@type":"ContactPoint","telephone":"+8801305869242","contactType":"customer service","availableLanguage":["bn","en"],"areaServed":"BD"}}}
body = """<span class="pill">📞 CONTACT & SUPPORT</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Talk to a <span class="grad-text">real human</span> — fast.</h1>
<p class="sub mt2">No bots, no ticket maze. A person answers, usually in minutes, in Bangla or English.</p>
<div class="grid g3 mt3">
  <div class="tcard"><b style="color:var(--green2)">💬 WhatsApp (fastest)</b><p class="sub" style="font-size:14px;margin-top:8px">Orders, support, warranty — everything runs here.</p><a class="btn btn-wa btn-sm mt2" href="https://wa.me/8801305869242">+880 1305-869242</a></div>
  <div class="tcard"><b style="color:var(--green2)">📧 Email</b><p class="sub" style="font-size:14px;margin-top:8px">For records, invoices, business enquiries.</p><a class="btn btn-ghost btn-sm mt2" href="mailto:support@saveonsub.com">support@saveonsub.com</a></div>
  <div class="tcard"><b style="color:var(--green2)">💳 Payment number</b><p class="sub" style="font-size:14px;margin-top:8px">bKash/Nagad/Rocket merchant (send-money at checkout).</p><div style="font-weight:900;color:var(--gold);margin-top:8px">+880 1305-869242</div></div>
</div>
<h2 class="mt3" style="font-size:21px">Support hours &amp; response</h2>
<div class="tbl mt2"><table>
<tr><th>Channel</th><th>Hours (BST)</th><th>Typical reply</th></tr>
<tr><td>WhatsApp</td><td>9:00 AM – 12:00 AM daily</td><td>Within minutes</td></tr>
<tr><td>Warranty claims</td><td>9:00 AM – 12:00 AM</td><td>Replacement within 1 hour</td></tr>
<tr><td>Email</td><td>Checked daily</td><td>Within 24 hours</td></tr>
</table></div>
<p class="sub mt2" style="font-size:14px">Outside hours (12 AM–9 AM)? Message anyway — we reply first thing, and your warranty clock pauses, so you lose nothing.</p>
<h2 class="mt3" style="font-size:21px">Where we serve</h2>
<p class="sub" style="font-size:15px">🇧🇩 <b>All of Bangladesh.</b> Everything we sell is digital and delivered on WhatsApp — Dhaka, Chattogram, Sylhet, Khulna, Rajshahi, a village in Sirajganj, anywhere with internet. No courier, no address needed, no delivery charge.</p>
<div class="notice green mt3">🤝 Nervous first order? Ask about <a href="how-to-order.html" style="color:var(--green2);font-weight:700">pay-after-testing</a> — we send access before you pay.</div>"""
pages['contact'] = dict(title="Contact & Support — Real Human, Fast | SAVEONSUB", desc="WhatsApp +880 1305-869242, email, support hours, all-Bangladesh coverage. A real person replies in minutes, Bangla or English. Warranty in 1 hour.", crumb="Contact", body=body, schema='<script type="application/ld+json">'+json.dumps(contact_ld,ensure_ascii=False)+'</script>', robots="")

# ---------- Track Order (BD order-anxiety reducer) ----------
body = """<span class="pill">📦 TRACK YOUR ORDER</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Where's my order? <span class="grad-text">One tap to find out.</span></h1>
<p class="sub mt2">Every order has an ID like <b style="color:var(--gold);font-family:ui-monospace">SOS-260713-4821</b> (shown at checkout and in your WhatsApp confirmation).</p>
<div class="box" style="background:var(--card);border:1px solid var(--line);border-radius:18px;padding:26px;max-width:520px;margin:22px 0">
  <label for="oid">Your order ID</label>
  <input id="oid" placeholder="SOS-260713-4821" autocomplete="off" style="text-transform:uppercase">
  <button class="btn btn-wa mt2" style="width:100%" onclick="var v=document.getElementById('oid').value.trim();location.href='https://wa.me/8801305869242?text='+encodeURIComponent('📦 Order status check: '+(v||'(my order)')+' — koto dur?')">💬 Check status on WhatsApp →</button>
</div>
<div id="myorders" style="max-width:520px"></div>
<script>
(function(){
  var box=document.getElementById('myorders'); if(!box) return;
  var h; try{h=JSON.parse(localStorage.getItem('sos_orders')||'[]')}catch(e){h=[]}
  if(!h.length) return;
  function esc(s){return String(s).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}
  function fmt(iso){try{return new Date(iso).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}catch(e){return ''}}
  var rows=h.map(function(o){
    var items=(o.items||[]).map(function(i){return esc(i.name)+' ('+esc(i.plan)+' ×'+i.qty+')'}).join(', ');
    var wa='https://wa.me/8801305869242?text='+encodeURIComponent('📦 Order status check: '+o.oid+' — koto dur?');
    return '<div style=\"background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px\">'
      +'<div style=\"display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap\"><span style=\"font-family:ui-monospace;color:var(--gold);font-weight:800\">'+esc(o.oid)+'</span>'
      +'<span style=\"color:var(--muted);font-size:12.5px\">'+fmt(o.at)+'</span></div>'
      +'<div style=\"font-size:13.5px;color:var(--muted);margin:8px 0\">'+items+'</div>'
      +'<div style=\"display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap\">'
      +'<b style=\"color:var(--green2)\">৳'+(o.total||0).toLocaleString()+' · '+esc(o.method||'')+'</b>'
      +'<a href=\"'+wa+'\" style=\"color:var(--green2);font-weight:700;font-size:13px\">Check status →</a></div></div>';
  }).join('');
  box.innerHTML='<h2 class=\"mt3\" style=\"font-size:21px\">Your recent orders <span style=\"color:var(--muted);font-weight:500;font-size:14px\">(on this device)</span></h2>'
    +'<p class=\"sub\" style=\"font-size:13.5px;margin:6px 0 14px\">Saved privately in your browser — no login, never on our servers.</p>'+rows;
})();
</script>
<h2 class="mt3" style="font-size:21px">What the statuses mean</h2>
<div class="tbl mt2"><table>
<tr><th>Status</th><th>Meaning</th></tr>
<tr><td>⏳ Payment received</td><td>We got your bKash/Nagad — preparing your access now</td></tr>
<tr><td>🚀 Delivered</td><td>Login/invite sent to your WhatsApp — warranty active</td></tr>
<tr><td>🛡️ Under warranty</td><td>7 days (shared) / 30 days (personal) — one message replaces any issue</td></tr>
</table></div>
<p class="sub mt2" style="font-size:14px">Instant products deliver in 5–15 minutes. If it's been longer, tap the button above — we'll sort it immediately.</p>"""
pages['track'] = dict(title="Track Your Order — SAVEONSUB", desc="Enter your order ID and check status instantly on WhatsApp. Instant products deliver in 5–15 minutes with warranty.", crumb="Track Order", body=body, schema="", robots='\n<meta name="robots" content="noindex,follow">')

# ---------- Student Zone (huge BD segment) ----------
body = """<span class="pill">🎓 STUDENT ZONE</span>
<h1 style="font-size:clamp(26px,4vw,38px)">For BD students — <span class="grad-text">free first, cheap second.</span></h1>
<p class="sub mt2">We sell subscriptions and we'll still tell you what to get for ৳0. That's the deal.</p>
<h2 class="mt3" style="font-size:21px">Claim these FREE (do this first)</h2>
<div class="tbl mt2"><table>
<tr><th>Tool</th><th>How it's free</th></tr>
<tr><td>GitHub Copilot Pro</td><td>Free via GitHub Student Developer Pack — we'll walk you through it</td></tr>
<tr><td>Canva Education</td><td>Free Pro for eligible institutions</td></tr>
<tr><td>ChatGPT / Gemini / Claude</td><td>Free tiers cover most study use</td></tr>
<tr><td>Notion</td><td>Free Plus for students with a .edu email</td></tr>
</table></div>
<h2 class="mt3" style="font-size:21px">Worth paying for (thesis &amp; skills)</h2>
<div class="grid g3 mt2">
  <div class="tcard"><b>📚 Research Bundle</b><p class="sub" style="font-size:13.5px">ChatGPT + Perplexity — cited sources + drafting</p><a class="btn btn-primary btn-sm mt2" href="p/bundle-research.html">From ৳600</a></div>
  <div class="tcard"><b>✍️ Grammarly</b><p class="sub" style="font-size:13.5px">IELTS &amp; assignment writing</p><a class="btn btn-primary btn-sm mt2" href="p/grammarly.html">From ৳470</a></div>
  <div class="tcard"><b>💎 Google AI Pro</b><p class="sub" style="font-size:13.5px">Gemini + 2TB storage on your Gmail</p><a class="btn btn-primary btn-sm mt2" href="p/google-ai-pro.html">৳500</a></div>
</div>
<h2 class="mt3" style="font-size:21px">Student discount</h2>
<p class="sub" style="font-size:15px">Show a valid student ID on WhatsApp and get <b>৳100 off</b> ChatGPT/Claude personal plans. And if the free path covers you, we'll say so before you spend a taka.</p>
<div class="heroctas mt3"><a class="btn btn-wa" href="https://wa.me/8801305869242?text=Hi!%20I'm%20a%20student%20—%20what%20should%20I%20get%3F">💬 Ask for student advice</a><a class="btn btn-ghost" href="blog/best-ai-tools-for-students-bangladesh.html">Full student guide →</a></div>"""
pages['students'] = dict(title="Student Zone — Free & Cheap AI Tools BD | SAVEONSUB", desc="BD students: claim free GitHub Copilot, Canva Edu, ChatGPT free tier first — then Research Bundle ৳600, Grammarly ৳470. Student discount included.", crumb="Student Zone", body=body, schema="", robots="")

# ---------- Offers hub (festival-ready, honest) ----------
body = """<span class="pill">🎁 OFFERS</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Standing offers — <span class="grad-text">no fake countdowns.</span></h1>
<p class="sub mt2">Real, always-on ways to pay less. We don't do fake "24-hour only" timers.</p>
<div class="grid g3 mt3">
  <div class="tcard"><b style="color:var(--green2)">🧾 Bulk / duration</b><p class="sub" style="font-size:14px;margin-top:8px">3 months upfront = <b>10% off</b> · 6 months = <b>15% off</b> on eligible plans.</p></div>
  <div class="tcard"><b style="color:var(--green2)">👥 Refer a friend</b><p class="sub" style="font-size:14px;margin-top:8px">You both get <b>৳100 off</b> your next order. Just have them mention your number.</p></div>
  <div class="tcard"><b style="color:var(--green2)">🎓 Student</b><p class="sub" style="font-size:14px;margin-top:8px"><b>৳100 off</b> personal AI plans with a valid student ID. <a href="students.html" style="color:var(--green2)">Student Zone →</a></p></div>
  <div class="tcard"><b style="color:var(--green2)">🎁 Bundles</b><p class="sub" style="font-size:14px;margin-top:8px">Save up to ৳199 vs buying separately. <a href="all.html#bundles" style="color:var(--green2)">See bundles →</a></p></div>
  <div class="tcard"><b style="color:var(--green2)">🤝 Pay-after-testing</b><p class="sub" style="font-size:14px;margin-top:8px">First order: access before payment. The best "offer" is trust.</p></div>
  <div class="tcard"><b style="color:var(--gold)">🌙 Festival offers</b><p class="sub" style="font-size:14px;margin-top:8px">Eid / Pohela Boishakh / back-to-school specials appear here when live — follow us on WhatsApp to hear first.</p></div>
</div>
<div class="notice green mt3">All offers stack sensibly — ask on <a href="https://wa.me/8801305869242" style="color:var(--green2);font-weight:700">WhatsApp</a> and we'll apply the best combination honestly.</div>"""
pages['offers'] = dict(title="Offers — Bulk, Referral, Student Discounts | SAVEONSUB", desc="Real standing offers: 10-15% bulk discount, ৳100 refer-a-friend, ৳100 student discount, bundle savings, pay-after-testing. No fake countdowns.", crumb="Offers", body=body, schema="", robots="")

# ---------- HTML sitemap (human + SEO internal linking) ----------
prod_links = "".join(f'<a href="p/{p["id"]}.html" style="color:var(--green2);display:inline-block;margin:3px 10px 3px 0;font-size:13.5px">{esc(p["name"].replace("🎁 ",""))}</a>' for p in json.load(open('catalog.json'))['products'])
guide_slugs = ["chatgpt-plus-price-in-bangladesh","how-to-pay-for-ai-tools-with-bkash","shared-vs-personal-ai-subscriptions-honest-guide","best-ai-tools-for-students-bangladesh","midjourney-vs-leonardo-bangladesh","netflix-spotify-youtube-premium-price-bd","google-ai-pro-500-taka-explained","free-ai-tools-that-beat-paid-bangladesh","capcut-vs-invideo-vs-opus-clip","coursera-vs-youtube-learning-bd","ai-video-tools-price-comparison-bd-2026","how-we-source-subscriptions-transparency"]
guide_links = "".join(f'<a href="blog/{g}.html" style="color:var(--green2);display:block;padding:2px 0;font-size:13.5px">{g.replace("-"," ")}</a>' for g in guide_slugs)
body = f"""<span class="pill">🗺️ SITEMAP</span>
<h1 style="font-size:clamp(26px,4vw,38px)">Everything on <span class="grad-text">one page</span>.</h1>
<h2 class="mt3" style="font-size:20px">Main</h2>
<p><a href="index.html" style="color:var(--green2);margin-right:14px">Home</a><a href="all.html" style="color:var(--green2);margin-right:14px">All Products</a><a href="all.html#bundles" style="color:var(--green2);margin-right:14px">Bundles</a><a href="quiz.html" style="color:var(--green2);margin-right:14px">Find My AI</a><a href="offers.html" style="color:var(--green2);margin-right:14px">Offers</a><a href="students.html" style="color:var(--green2);margin-right:14px">Student Zone</a></p>
<h2 class="mt3" style="font-size:20px">Help &amp; Trust</h2>
<p><a href="how-to-order.html" style="color:var(--green2);margin-right:14px">How to Order</a><a href="contact.html" style="color:var(--green2);margin-right:14px">Contact</a><a href="track.html" style="color:var(--green2);margin-right:14px">Track Order</a><a href="faq.html" style="color:var(--green2);margin-right:14px">FAQ</a><a href="warranty.html" style="color:var(--green2);margin-right:14px">Warranty</a><a href="refund.html" style="color:var(--green2);margin-right:14px">Refund</a><a href="privacy.html" style="color:var(--green2);margin-right:14px">Privacy</a><a href="terms.html" style="color:var(--green2);margin-right:14px">Terms</a><a href="about.html" style="color:var(--green2);margin-right:14px">About</a></p>
<h2 class="mt3" style="font-size:20px">All products ({len(json.load(open('catalog.json'))['products'])})</h2>
<p style="line-height:2">{prod_links}</p>
<h2 class="mt3" style="font-size:20px">Guides</h2>
<div>{guide_links}</div>"""
pages['sitemap'] = dict(title="Sitemap — All Pages | SAVEONSUB", desc="Every SAVEONSUB page in one place: all products, guides, help and trust pages. Easy navigation.", crumb="Sitemap", body=body, schema="", robots="")

count = 0
for slug, p in pages.items():
    html_out = SHELL.format(slug=slug, title=p['title'], desc=p['desc'], crumb=p['crumb'], body=p['body'], schema=p['schema'], robots=p['robots']).replace('{nav_en()}', nav_en())
    open(f"{slug}.html", 'w').write(html_out)
    count += 1
print(f"OK: generated {count} trust pages")

# ---------- Bangla FAQ (bn/faq.html) — completes the Bangla trust set ----------
import os as _os
_os.makedirs('bn', exist_ok=True)
FAQS_BN = [
 ("SAVEONSUB কি আসল? স্ক্যাম না তো?",
  "ন্যায্য প্রশ্ন — বাংলাদেশে সাবস্ক্রিপশন স্ক্যাম অনেক। প্রমাণ: ২০২৪ থেকে ৩,০০০+ কাস্টমার, যাচাইযোগ্য SYSmoAI পরিবার (sysmoai.com, aipremiumshop.com), পাবলিক হোয়াটসঅ্যাপে মানুষ উত্তর দেয়, আর <b>pay-after-testing</b> — আগে অ্যাক্সেস, যাচাই করে তারপর টাকা। স্ক্যামার এটা পারে না।"),
 ("এত সস্তা কেন? সমস্যা কোথায়?",
  "দুটি সৎ কারণ: (১) শেয়ার্ড প্ল্যানে একটি সাবস্ক্রিপশনের খরচ কয়েকজন ভাগ করে নেয় — এটাই ডিসকাউন্ট, আর এ কারণেই প্রোভাইডারের শর্তে এটা অনুমোদিত নয় (এই 'সমস্যা'টা আমরা প্রতিটি প্রোডাক্টে লিখে দিই ও ওয়ারেন্টিতে কভার করি); (২) পার্সোনাল প্ল্যানে রিজিওনাল প্রাইসিং। অফিসিয়াল দামটাও পাশে দেখাই, যাতে কী বাঁচছে বোঝেন।"),
 ("শেয়ার্ড প্ল্যানে আমার ChatGPT চ্যাট কি অন্যরা দেখবে?",
  "না। ChatGPT প্রত্যেকের কথোপকথন আলাদা ও প্রাইভেট রাখে — অন্য সিট-হোল্ডাররা আপনার চ্যাট, হিস্ট্রি বা কাস্টম ইনস্ট্রাকশন দেখতে পারে না। শুধু খরচটা শেয়ার হয়, ডেটা কখনো নয়।"),
 ("শেয়ার্ড, পার্সোনাল আর অফিসিয়াল — পার্থক্য কী?",
  "<b>অফিসিয়াল</b> = আপনি সরাসরি প্রোভাইডারকে দেন, আমরা শুধু সেটআপে সাহায্য করি। <b>পার্সোনাল</b> = আপনার নিজের ইমেইলে সাবস্ক্রিপশন — পূর্ণ নিয়ন্ত্রণ, সবচেয়ে কম ঝুঁকি। <b>শেয়ার্ড</b> = মাল্টি-ইউজার প্ল্যানে একটি সিট — ৭০–৮৫% সস্তা, শর্ত অনুযায়ী অনুমোদিত নয়, তাই মাঝে মাঝে রিসেট হয়; আমরা ১ ঘণ্টায় রিপ্লেস করি।"),
 ("শেয়ার্ড অ্যাকাউন্ট কি ব্যান হতে পারে? হলে কী হবে?",
  "হ্যাঁ, হতে পারে — সস্তা দামের সৎ ট্রেড-অফ এটাই। হলে: মেসেজ দিন, সাপোর্ট আওয়ারে ১ ঘণ্টার মধ্যে রিপ্লেসমেন্ট, প্রতিটি শেয়ার্ড সিটে ৭ দিন গ্যারান্টি। রিপ্লেস করতে না পারলে বাকি দিনের রিফান্ড।"),
 ("কীভাবে পেমেন্ট করব? আমার কার্ড নেই।",
  "বিকাশ, নগদ বা রকেটে সেন্ড মানি — এটাই মূল কথা। কার্ড, ব্যাংক অ্যাকাউন্ট বা ইন্টারন্যাশনাল পেমেন্ট লাগবে না। চেকআউটে মার্চেন্ট নম্বর (+৮৮০ ১৭১৪-৬৭২০৯৪) কপি বাটনসহ আর অর্ডার আইডি রেফারেন্সে দেওয়া থাকে।"),
 ("Pay-after-testing জিনিসটা কী?",
  "নার্ভাস নতুনদের জন্য: আগে অ্যাক্সেস পাঠাই, আপনি যাচাই করেন যে কাজ করছে, তারপর এক ঘণ্টার মধ্যে টাকা দেন। বেশিরভাগ ইনস্ট্যান্ট প্রোডাক্টে প্রথম অর্ডারে পাওয়া যায়। বাংলাদেশে আর কেউ এটা দেয় না।"),
 ("রিনিউয়ালে কি অটো-চার্জ হয়?",
  "কখনো না। কোনো অটো-চার্জ নেই — প্রতিবার আপনি ম্যানুয়ালি পে করেন। মেয়াদ শেষের ৩ দিন আগে হোয়াটসঅ্যাপে রিমাইন্ডার দিই; না চাইলে সাবস্ক্রিপশন এমনিই শেষ। আপনার টাকা আপনার নিয়ন্ত্রণে।"),
 ("রিফান্ড পাওয়া যাবে?",
  "হ্যাঁ — <a href='../refund.html' style='color:var(--green2)'>রিফান্ড পলিসি</a> দেখুন। সংক্ষেপে: ২৪ ঘণ্টায় ডেলিভারি না হলে পূর্ণ রিফান্ড; রিপ্লেস করা না গেলে বাকি দিনের রিফান্ড; ডেলিভারির আগে মত বদলালে পূর্ণ রিফান্ড।"),
 ("কোন AI কিনব বুঝতে পারছি না।",
  "৬০ সেকেন্ডের <a href='../quiz.html' style='color:var(--green2)'>Find My AI কুইজ</a> দিন — ৪টা প্রশ্ন, একটা সৎ পরামর্শ। বা হোয়াটসঅ্যাপে জিজ্ঞেস করুন। ফ্রি টিয়ার যথেষ্ট হলে সেটাই বলব — সত্যি।"),
 ("ফেসবুক/টেলিগ্রাম সেলারের বদলে আপনাদের বিশ্বাস করব কেন?",
  "সিট নষ্ট হলে FB/টেলিগ্রাম সেলার উধাও — ব্র্যান্ড নেই, ওয়েবসাইট নেই, রিকোর্স নেই। আমাদের পাবলিক ব্র্যান্ড (SYSmoAI), লিখিত ওয়ারেন্টি, রিফান্ড পলিসি, এই স্টোর আর ২ বছরের ট্র্যাক রেকর্ড আছে। সমস্যা হলে আমরা একই নম্বরে আছি।"),
 ("বাংলাদেশে শেয়ার্ড সাবস্ক্রিপশন কেনা কি বৈধ?",
  "আপনার জন্য এটা অবৈধ নয় — এটা প্রোভাইডারের শর্ত (তাদের সাথে অ্যাকাউন্ট হোল্ডারের চুক্তি) লঙ্ঘন, বাংলাদেশের আইন নয়। আপনার সবচেয়ে খারাপ পরিস্থিতি: সিট রিসেট হবে, আমরা রিপ্লেস করব। এটা আমরা সৎভাবে লিখে দিই যাতে পূর্ণ তথ্য নিয়ে সিদ্ধান্ত নেন।"),
]
_bn_faq_details = "".join(f"<details{' open' if i==0 else ''}><summary>{esc(q)}</summary><p>{a}</p></details>" for i,(q,a) in enumerate(FAQS_BN))
_bn_faq_schema = '<script type="application/ld+json">'+json.dumps({"@context":"https://schema.org","@type":"FAQPage",
  "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":html.unescape(a).replace('<b>','').replace('</b>','').replace("<a href='../refund.html' style='color:var(--green2)'>","").replace("<a href='../quiz.html' style='color:var(--green2)'>","").replace('</a>','')}} for q,a in FAQS_BN]}, ensure_ascii=False)+'</script>'
bn_faq = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>প্রশ্নোত্তর — সৎ উত্তর | SAVEONSUB</title>
<meta name="description" content="নিরাপদ? শেয়ার্ডে আমার চ্যাট কি অন্যরা দেখবে? রিফান্ড? বিকাশে কীভাবে? বাংলাদেশে সাবস্ক্রিপশন কেনার সব প্রশ্নের সৎ উত্তর।">
<link rel="canonical" href="https://saveonsub.com/bn/faq.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/faq.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/faq.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/faq.html">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="প্রশ্নোত্তর — সৎ উত্তর | SAVEONSUB"><meta property="og:description" content="বাংলাদেশে সাবস্ক্রিপশন কেনার সব প্রশ্নের সৎ উত্তর।">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/bn/faq.html">
<meta property="og:locale" content="bn_BD"><meta name="theme-color" content="#06181a">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="manifest" href="../assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="../assets/style.css">
{_bn_faq_schema}
</head>
<body>
<a class="skip" href="#main">মূল কন্টেন্টে যান</a>
{nav_bn("../")}
<main id="main"><div class="wrap" style="max-width:820px">
  <div class="crumbs"><a href="../bn.html">হোম</a> › প্রশ্নোত্তর</div>
  <span class="pill">প্রশ্নোত্তর</span>
  <h1 style="font-size:clamp(26px,4vw,38px)">সৎ উত্তর, <span class="grad-text">লুকোছাপা ছাড়া।</span></h1>
  <p class="sub mt2">যা জিজ্ঞেস করতে দ্বিধা করেন, সেগুলোরই সৎ উত্তর — কেনার আগে পুরোটা জানুন।</p>
  <div class="mt3">{_bn_faq_details}</div>
  <div class="notice green mt3">আরও প্রশ্ন? <a href="https://wa.me/8801305869242?text=Hi!" style="color:var(--green2);font-weight:800">হোয়াটসঅ্যাপে জিজ্ঞেস করুন</a> — বাংলা বা ইংরেজিতে, মানুষ উত্তর দেবে।</div>
</div></main>
<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="হোয়াটসঅ্যাপ">💬 হোয়াটসঅ্যাপ</button>
{footer_bn("../")}
<script src="../assets/app.js"></script>
</body>
</html>"""
open('bn/faq.html', 'w').write(bn_faq)
# reciprocity: point English FAQ's bn-bd hreflang to the Bangla FAQ + add a বাংলা nav link
_ef = open('faq.html').read()
_ef = _ef.replace('<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/faq.html">',
                  '<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/faq.html">')
_ef = _ef.replace('<a href="how-to-order.html">How to Order</a><a href="faq.html">FAQ</a></div>',
                  '<a href="how-to-order.html">How to Order</a><a href="faq.html">FAQ</a><a href="bn/faq.html" style="color:var(--gold);font-weight:800">বাংলা</a></div>')
open('faq.html', 'w').write(_ef)
print("OK: generated bn/faq.html + linked English FAQ")

# ---------- Bangla How-to-Order (bn/how-to-order.html) — completes the Bangla conversion path ----------
_howto_ld_bn = {"@context":"https://schema.org","@type":"HowTo","name":"বিকাশে SAVEONSUB থেকে সাবস্ক্রিপশন কেনার নিয়ম","totalTime":"PT3M",
 "step":[{"@type":"HowToStep","position":1,"name":"প্রোডাক্ট বেছে নিন","text":"সব প্রোডাক্ট দেখুন বা Find My AI কুইজ দিন। কার্টে যোগ করুন — টাকায় দাম, প্রতিটি প্ল্যানে সৎ লেবেল।"},
 {"@type":"HowToStep","position":2,"name":"বিকাশ/নগদ/রকেটে টাকা পাঠান","text":"চেকআউটে মার্চেন্ট নম্বর +৮৮০ ১৭১৪-৬৭২০৯৪ কপি করে অর্ডার আইডি রেফারেন্সে দিয়ে মোট টাকা সেন্ড মানি করুন।"},
 {"@type":"HowToStep","position":3,"name":"হোয়াটসঅ্যাপে কনফার্ম করুন","text":"কনফার্ম বাটনে চাপ দিন — অর্ডারসহ একটি রেডি মেসেজ খুলবে, পাঠিয়ে দিন।"},
 {"@type":"HowToStep","position":4,"name":"৫–১৫ মিনিটে পান","text":"অ্যাক্সেস বা ইনভাইট হোয়াটসঅ্যাপে আসবে। প্রথম মিনিট থেকেই ওয়ারেন্টি চালু।"}]}
bn_howto = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>বিকাশে কীভাবে অর্ডার করবেন — ৩ মিনিটের গাইড | SAVEONSUB</title>
<meta name="description" content="প্রোডাক্ট বাছুন → বিকাশ/নগদে টাকা পাঠান → হোয়াটসঅ্যাপে কনফার্ম → ৫–১৫ মিনিটে ডেলিভারি। নতুনদের জন্য পূর্ণ গাইড, pay-after-testing সহ।">
<link rel="canonical" href="https://saveonsub.com/bn/how-to-order.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/how-to-order.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/how-to-order.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/how-to-order.html">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="বিকাশে কীভাবে অর্ডার করবেন | SAVEONSUB"><meta property="og:description" content="৩ মিনিটে অর্ডার — বিকাশ/নগদে, কার্ড ছাড়া।">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/bn/how-to-order.html">
<meta property="og:locale" content="bn_BD"><meta name="theme-color" content="#06181a">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="manifest" href="../assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="../assets/style.css">
<script type="application/ld+json">{json.dumps(_howto_ld_bn, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">মূল কন্টেন্টে যান</a>
{nav_bn("../")}
<main id="main"><div class="wrap" style="max-width:820px">
  <div class="crumbs"><a href="../bn.html">হোম</a> › কীভাবে অর্ডার</div>
  <span class="pill">📖 কীভাবে অর্ডার</span>
  <h1 style="font-size:clamp(26px,4vw,38px)">প্রথমবার? <span class="grad-text">৩ মিনিটে ডেলিভারি পর্যন্ত।</span></h1>
  <div class="steps mt3" style="grid-template-columns:repeat(2,1fr)">
    <div class="step"><h3>প্রোডাক্ট বেছে নিন</h3><p><a href="../all.html" style="color:var(--green2)">সব প্রোডাক্ট</a> দেখুন বা <a href="../quiz.html" style="color:var(--green2)">কুইজ</a> দিন। প্রতিটি প্ল্যানে দাম, সৎ ঝুঁকির লেবেল ও ডেলিভারির সময় লেখা। <b>কার্টে যোগ করুন</b>।</p></div>
    <div class="step"><h3>টাকা পাঠান</h3><p>বিকাশ/নগদ/রকেট খুলুন → <b>Send Money</b> → আমাদের নম্বর <b>+৮৮০ ১৭১৪-৬৭২০৯৪</b> (চেকআউটে কপি বাটন) → অ্যামাউন্ট = কার্টের মোট → রেফারেন্স = আপনার অর্ডার আইডি।</p></div>
    <div class="step"><h3>হোয়াটসঅ্যাপে কনফার্ম</h3><p>বড় সবুজ বাটনে চাপ দিন। অর্ডারসহ একটি মেসেজ রেডি হয়ে খুলবে — শুধু পাঠান। TxnID থাকলে দিন, দ্রুত হয়।</p></div>
    <div class="step"><h3>ডেলিভারি নিন</h3><p>ইনস্ট্যান্ট প্রোডাক্ট <b>৫–১৫ মিনিটে</b> সেটআপ নির্দেশনাসহ আসে। শেয়ার্ড সিটের নিয়ম পড়ুন, উপভোগ করুন, আর নম্বরটা সেভ রাখুন — ওয়ারেন্টি একটা মেসেজ দূরে।</p></div>
  </div>
  <h2 class="mt3" style="font-size:21px">আগে টাকা দিতে ভয়?</h2>
  <p class="sub" style="font-size:15px">চেকআউটে <b style="color:var(--green2)">Pay-After-Testing</b> ব্যবহার করুন — যোগ্য প্রথম অর্ডারে আগে অ্যাক্সেস পাঠাই, আপনি যাচাই করে তারপর টাকা দেন। এতটাই কনফিডেন্ট আমরা।</p>
  <h2 class="mt3" style="font-size:21px">নতুনদের সাধারণ ভুল (এড়িয়ে চলুন)</h2>
  <p class="sub" style="font-size:15px">রেফারেন্সে অর্ডার আইডি না দেওয়া (খুঁজে পাব, তবে দেরিতে) · অন্য কোনো ওয়েবসাইটের নম্বরে টাকা পাঠানো (শুধু আমাদের চেকআউটের নম্বরই বিশ্বাস করুন) · শেয়ার্ড সিটের পাসওয়ার্ড বদলানো (সবার জন্য সিট নষ্ট হয় — ওয়ারেন্টি কভার করবে না)।</p>
  <div class="heroctas mt3"><a class="btn btn-primary" href="../all.html">শপিং শুরু করুন →</a></div>
</div></main>
<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="হোয়াটসঅ্যাপ">💬 হোয়াটসঅ্যাপ</button>
{footer_bn("../")}
<script src="../assets/app.js"></script>
</body>
</html>"""
open('bn/how-to-order.html', 'w').write(bn_howto)
# reciprocity for English how-to-order
_eh = open('how-to-order.html').read()
_eh = _eh.replace('<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/how-to-order.html">',
                  '<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/how-to-order.html">')
_eh = _eh.replace('<a href="how-to-order.html">How to Order</a><a href="faq.html">FAQ</a></div>',
                  '<a href="how-to-order.html">How to Order</a><a href="faq.html">FAQ</a><a href="bn/how-to-order.html" style="color:var(--gold);font-weight:800">বাংলা</a></div>')
open('how-to-order.html', 'w').write(_eh)
print("OK: generated bn/how-to-order.html + linked English how-to-order")
