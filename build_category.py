#!/usr/bin/env python3
"""SAVEONSUB build step 7: static category landing pages c/<slug>.html.
Each is a real crawlable page (server-rendered product list + unique SEO copy + ItemList schema)
targeting category-level BD keywords — not a JS-filtered query-param view.
Run: python3 build_category.py"""
import json, os, html, re
from templates import nav_en, nav_bn, footer_en, footer_bn

cat = json.load(open('catalog.json'))
rate = cat['meta']['usd_anchor_rate']
os.makedirs('c', exist_ok=True)
def esc(s): return html.escape(str(s), quote=True)

TOS_CLASS = {"official":"official","personal":"personal","shared-low":"shared-low","shared-med":"shared-med","bundle":"shared-low"}

def slug(c): return re.sub(r'[^a-z0-9]+','-',c.lower()).strip('-')

# per-category SEO copy + intent
META = {
 "AI Assistants": ("AI Chatbot Subscriptions in Bangladesh — ChatGPT, Claude, Gemini",
   "ChatGPT, Claude, Google AI Pro, Grok, Perplexity at BD prices with bKash. Honest labels, warranty, from ৳199. The AI assistant a Bangladeshi actually needs.",
   "AI assistants (ChatGPT, Claude, Gemini, Grok) are the tools most Bangladeshis ask us about. Official plans need an international card at ~৳2,200/mo — we deliver the same tools from ৳199 via bKash, with honest risk labels on every plan."),
 "AI Image & Design": ("AI Image & Design Tools in Bangladesh — Midjourney, Canva",
   "Midjourney, Leonardo, Canva Pro, Adobe Firefly, Ideogram, Freepik at BD prices with bKash. From ৳190. For BD designers, thumbnail sellers and marketers.",
   "AI image and design tools power the BD freelance economy — Fiverr thumbnails, Facebook ad creatives, brand design. From Adobe Firefly at ৳190 to the full Midjourney ladder, all with bKash and honest labels."),
 "AI Video": ("AI Video Tools in Bangladesh — Kling, Runway, CapCut, HeyGen",
   "Kling ৳270, CapCut ৳399, Invideo, Runway, HeyGen, Synthesia at BD prices with bKash. The Reels/Shorts creator stack — far below other BD shops on Kling.",
   "AI video is the fastest-growing category for BD Reels/Shorts/TikTok creators. Kling at ৳270 (vs a ৳1,299+ market), CapCut Pro at ৳399, and the full avatar/editing stack — bKash, warranty, honest market comparisons on every page."),
 "AI Voice & Music": ("AI Voice and Music in Bangladesh — ElevenLabs, Suno",
   "ElevenLabs, Suno, Udio, Murf, Otter at BD prices with bKash. From ৳499. Bangla voiceovers for faceless YouTube, AI music, meeting transcription.",
   "AI voice and music tools for BD content creators — ElevenLabs makes Bangla voiceovers for faceless YouTube channels, Suno/Udio generate songs, Otter transcribes meetings. From ৳499 via bKash."),
 "AI Code & Dev": ("AI Coding Tools in Bangladesh — Cursor, Copilot, Windsurf",
   "GitHub Copilot, Cursor, Windsurf, Replit, v0.dev at BD prices with bKash. From ৳590. For BD developers — and students, Copilot is FREE (we'll show you).",
   "AI coding tools for Bangladeshi developers — Cursor, Copilot, Windsurf, Replit. Students: GitHub Copilot is FREE via the Student Pack and we help you claim it instead of selling it. Paid plans from ৳590 via bKash."),
 "AI Writing": ("AI Writing Tools in Bangladesh — Grammarly, QuillBot, Jasper",
   "Grammarly, QuillBot, Jasper, Writesonic at BD prices with bKash. From ৳299. IELTS writing, thesis, SEO copy — the BD student & freelancer stack.",
   "AI writing tools for BD students and freelancers — Grammarly for IELTS and assignments, QuillBot for thesis paraphrasing, Jasper/Writesonic for marketing copy. From ৳299 via bKash."),
 "Workspace & Productivity": ("Productivity Tool Subscriptions in Bangladesh — Notion, Gamma",
   "Notion ৳299, Gamma ৳399, Otter ৳799, Manus ৳2,500 at BD prices with bKash. AI workspaces, instant presentations and autonomous agents for BD teams and students.",
   "Productivity and workspace tools for Bangladeshi teams and students. Notion replaces Google Docs + Trello + a wiki in one collaborative workspace — the free tier already covers most personal use. Gamma generates entire presentations from a one-line prompt (useful for university defenses and client pitches). Otter transcribes meetings and classes in real-time with speaker identification. Manus is an autonomous AI agent that completes multi-step research tasks on its own. From ৳399 via bKash — and if the free tier fits, we will say so honestly."),
 "Entertainment": ("Streaming Subscriptions in Bangladesh — Netflix, Spotify, YouTube",
   "Netflix ৳349, Spotify, YouTube Premium, Prime, Hoichoi at BD prices with bKash. No credit card needed — the honest way to stream in Bangladesh.",
   "Streaming subscriptions for Bangladesh — Netflix without a credit card, Spotify (we'll tell you the official ৳219 too), YouTube Premium, Hoichoi. Where official BD pricing exists we say so; where it doesn't, a warranted option beats a Facebook seller."),
 "Education & Career": ("Learning Subscriptions in Bangladesh — Coursera, LinkedIn",
   "Coursera Plus ৳1,199, LinkedIn Premium ৳1,999 at BD prices with bKash. For certificates, career skills and job hunting — with advice on when free wins.",
   "Learning and career subscriptions for Bangladeshi professionals and students. Coursera Plus gives unlimited access to 7,000+ courses from Yale, Stanford, Google and IBM with verifiable certificates — essential for CV-building and visa applications. LinkedIn Premium unlocks InMail to recruiters, salary insights and LinkedIn Learning. But honestly: for casual learning, free YouTube + Coursera financial aid covers most needs. Buy only when certificates or job-search tools genuinely advance your career. From ৳1,199 via bKash."),
 "VPN & Security": ("VPN Subscriptions in Bangladesh — NordVPN, Surfshark",
   "NordVPN ৳299, Surfshark ৳249 at BD prices with bKash. For streaming, privacy and lower gaming ping. Honest warnings about renewal-price jumps included.",
   "VPN subscriptions for Bangladesh — NordVPN and Surfshark let you access geo-blocked streaming (US Netflix, Hulu, BBC iPlayer), secure your connection on public WiFi, and reduce gaming ping to international servers. NordVPN has 6,000+ servers across 110+ countries; Surfshark offers unlimited simultaneous devices on one account. Both charge less for the first term then renew at a higher rate — we flag this on every plan so you are not surprised. From ৳249 via bKash with warranty."),
 "Bundles": ("AI Tool Bundles in Bangladesh — Student, Creator, Business",
   "AI bundles at BD prices with bKash: Student ৳449, Creator, Research ৳600, Business ৳15,000. Save vs buying separately — the fastest way to a full stack.",
   "Bundles package the right tools together at a discount — Student Essentials, University Pro, Freelancer, and the Business AI stack with hands-on setup. Save up to ৳199 vs buying separately."),
}

products = cat['products']
count = 0
for c in cat['categories']:
    items = [p for p in products if p['category'] == c]
    if not items: continue
    items = sorted(items, key=lambda x: (-(x.get('bestseller_rank',0)>0), min(pl['bdt'] for pl in x['plans'])))
    title, desc, intro = META.get(c, (f"{c} in Bangladesh", f"{c} at BD prices with bKash.", f"{c} at honest BD prices."))
    title = f"{title} | SAVEONSUB"
    if len(title) > 60: title = f"{c} in Bangladesh — bKash | SAVEONSUB"
    if len(title) > 60: title = f"{c} BD Prices | SAVEONSUB"
    if len(title) > 60: title = f"{c} | SAVEONSUB"
    s = slug(c)

    cards = ""
    for p in items:
        frm = min(pl['bdt'] for pl in p['plans']); off = round(p['official_usd']*rate)
        t = min(p['plans'], key=lambda x:x['bdt'])['tos']
        nm = esc(p['name'].replace('🎁 ',''))
        cards += f"""<a class="pcard" href="../p/{p['id']}.html"><span class="icon">{p['icon']}</span><h3>{nm}</h3><span class="cat">{esc(c)}</span><div class="price">৳{frm:,}{f'<s>৳{off:,}</s>' if off>frm else ''}</div><span class="tos {TOS_CLASS.get(t,'shared-low')}">{t.replace('-','·')}</span></a>"""

    item_ld = {"@context":"https://schema.org","@type":"ItemList","name":title,
      "itemListElement":[{"@type":"ListItem","position":i+1,"url":f"https://saveonsub.com/p/{p['id']}.html","name":p['name'].replace('🎁 ','')} for i,p in enumerate(items)]}
    crumb_ld = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"Home","item":"https://saveonsub.com/"},
      {"@type":"ListItem","position":2,"name":"All Products","item":"https://saveonsub.com/all.html"},
      {"@type":"ListItem","position":3,"name":c,"item":f"https://saveonsub.com/c/{s}.html"}]}

    en_nav = nav_en("../")
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://saveonsub.com/c/{s}.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/c/{s}.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/c/{s}.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/c/{s}.html">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/c/{s}.html">
<meta property="og:locale" content="en_BD"><meta name="theme-color" content="#06181a">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="manifest" href="../assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="../assets/style.css">
<script type="application/ld+json">{json.dumps(item_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{en_nav}
<main id="main"><div class="wrap">
  <div class="crumbs"><a href="../index.html">Home</a> › <a href="../all.html">All Products</a> › {esc(c)}</div>
  <h1 style="font-size:clamp(26px,4vw,38px)">{esc(c)} in <span class="grad-text">Bangladesh</span></h1>
  <p class="sub mt2">{esc(intro)}</p>
  <p class="sub" style="font-size:14px;margin-top:6px">🏷️ Honest labels: <span class="tos official">official</span> <span class="tos personal">personal</span> <span class="tos shared-low">shared·low</span> <span class="tos shared-med">shared·covered</span> · 💳 bKash/Nagad/Rocket · 🛡️ warranty on every plan</p>
  <div class="grid g4 mt3">{cards}</div>
  <div class="notice green mt3">🤝 Not sure which {esc(c.lower())} to pick? Take the <a href="../quiz.html" style="color:var(--green2);font-weight:700">60-second quiz</a> or <a href="https://wa.me/8801305869242?text=Hi!%20Help%20me%20pick%20a%20{esc(s)}%20subscription" style="color:var(--green2);font-weight:700">ask a human on WhatsApp</a> — we'll tell you honestly, even if the free tier is enough.</div>
</div></main>
<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="WhatsApp">💬 WhatsApp</button>
<a class="fab fab-quiz" href="../quiz.html" aria-label="Find my AI quiz">🧭 Find My AI</a>
{footer_en("../")}
<script src="../assets/app.js"></script>
</body>
</html>"""
    open(f"c/{s}.html", 'w').write(page)
    count += 1
print(f"OK: generated {count} category pages in c/")

# ===================== BANGLA CATEGORY PAGES (bn/c/<slug>.html) =====================
CAT_BN = {
 "AI Assistants":"এআই অ্যাসিস্ট্যান্ট","AI Image & Design":"এআই ইমেজ ও ডিজাইন","AI Video":"এআই ভিডিও",
 "AI Voice & Music":"এআই ভয়েস ও মিউজিক","AI Code & Dev":"এআই কোডিং ও ডেভেলপমেন্ট","AI Writing":"এআই রাইটিং",
 "Workspace & Productivity":"ওয়ার্কস্পেস ও প্রোডাক্টিভিটি","Entertainment":"স্ট্রিমিং ও বিনোদন",
 "Education & Career":"শিক্ষা ও ক্যারিয়ার","VPN & Security":"ভিপিএন ও সিকিউরিটি","Bundles":"বান্ডেল"}
INTRO_BN = {
 "AI Assistants":"ChatGPT, Claude, Google AI Pro, Perplexity — বাংলাদেশে সবচেয়ে বেশি খোঁজা এআই টুল। অফিসিয়ালে কার্ড লাগে (~৳২,২০০/মাস); আমরা একই টুল ৳১৯৯ থেকে বিকাশে দিই, প্রতিটি প্ল্যানে সৎ ঝুঁকির লেবেলসহ।",
 "AI Image & Design":"Midjourney, Leonardo, Canva Pro, Adobe Firefly — বাংলাদেশের ফ্রিল্যান্স ইকোনমির চালিকাশক্তি। Fiverr থাম্বনেইল, ফেসবুক অ্যাড, ব্র্যান্ড ডিজাইন — ৳১৯০ থেকে, বিকাশে, সৎ লেবেলসহ।",
 "AI Video":"Reels/Shorts/TikTok ক্রিয়েটরদের জন্য দ্রুততম বর্ধনশীল ক্যাটাগরি। Kling ৳২৭০ (বাজারে ৳১,২৯৯+), CapCut Pro ৳৩৯৯, পুরো এডিটিং/অ্যাভাটার স্ট্যাক — বিকাশে, ওয়ারেন্টিসহ।",
 "AI Voice & Music":"বাংলা ভয়েসওভার (ElevenLabs), এআই গান (Suno/Udio), মিটিং ট্রান্সক্রিপশন (Otter) — ফেসলেস ইউটিউব ও কনটেন্ট ক্রিয়েটরদের জন্য, ৳৪৯৯ থেকে বিকাশে।",
 "AI Code & Dev":"বাংলাদেশি ডেভেলপারদের জন্য Cursor, Copilot, Windsurf, Replit। স্টুডেন্ট? GitHub Copilot ফ্রি — Student Pack দিয়ে, আমরা দেখিয়ে দেব (বিক্রি না করে)। পেইড প্ল্যান ৳৫৯০ থেকে।",
 "AI Writing":"বাংলাদেশি স্টুডেন্ট ও ফ্রিল্যান্সারদের জন্য — IELTS রাইটিং ও অ্যাসাইনমেন্টে Grammarly, থিসিসে QuillBot, মার্কেটিং কপিতে Jasper। ৳২৯৯ থেকে বিকাশে।",
 "Workspace & Productivity":"নোট ও ডকে Notion, ইনস্ট্যান্ট প্রেজেন্টেশনে Gamma, রিসার্চে অটোনোমাস এজেন্ট। বাংলাদেশি টিম ও স্টুডেন্টদের জন্য ৳৩৯৯ থেকে, সৎ লেবেলসহ।",
 "Entertainment":"বাংলাদেশে স্ট্রিমিং — কার্ড ছাড়াই Netflix, Spotify (অফিসিয়াল ৳২১৯-ও বলে দিই), YouTube Premium, Hoichoi। যেখানে অফিসিয়াল দাম আছে সেটা বলি; যেখানে নেই, ওয়ারেন্টিসহ অপশন ফেসবুক সেলারের চেয়ে ভালো।",
 "Education & Career":"সার্টিফিকেটে Coursera Plus, চাকরি খোঁজায় LinkedIn Premium। ফ্রি YouTube বা Coursera financial aid ভালো হলে সৎভাবে সেটাই বলি। ৳১,৪৯৯ থেকে বিকাশে।",
 "VPN & Security":"স্ট্রিমিং, প্রাইভেসি ও গেমিং পিং-এর জন্য NordVPN ও Surfshark। ৳২৪৯ থেকে বিকাশে — রিনিউয়ালে দাম বেড়ে যাওয়ার সৎ সতর্কবার্তাসহ।",
 "Bundles":"সঠিক টুলগুলো একসাথে ছাড়ে — Student Essentials, University Pro, Freelancer, আর হাতে-কলমে সেটআপসহ Business AI স্ট্যাক। আলাদা কেনার চেয়ে ৳১৯৯ পর্যন্ত সাশ্রয়।"}

os.makedirs('bn/c', exist_ok=True)
bcount = 0
for c in cat['categories']:
    items = [p for p in products if p['category'] == c]
    if not items: continue
    items = sorted(items, key=lambda x: (-(x.get('bestseller_rank',0)>0), min(pl['bdt'] for pl in x['plans'])))
    s = slug(c)
    cbn = CAT_BN.get(c, c)
    intro = INTRO_BN.get(c, f"{cbn} — সৎ দামে বাংলাদেশে, বিকাশে।")
    title = f"{cbn} বাংলাদেশে দাম | SAVEONSUB"
    if len(title) > 60: title = f"{cbn} | SAVEONSUB"
    desc = f"{cbn} বাংলাদেশে বিকাশে — সৎ দামে আসল সাবস্ক্রিপশন, প্রতিটি প্ল্যানে ওয়ারেন্টি ও ঝুঁকির লেবেল।"
    if len(desc) > 158: desc = desc[:155] + "…"

    cards = ""
    for p in items:
        frm = min(pl['bdt'] for pl in p['plans']); off = round(p['official_usd']*rate)
        t = min(p['plans'], key=lambda x:x['bdt'])['tos']
        nm = esc(p['name'].replace('🎁 ',''))
        cards += f"""<a class="pcard" href="../p/{p['id']}.html"><span class="icon">{p['icon']}</span><h3>{nm}</h3><span class="cat">{esc(cbn)}</span><div class="price">৳{frm:,}{f'<s>৳{off:,}</s>' if off>frm else ''}</div><span class="tos {TOS_CLASS.get(t,'shared-low')}">{t.replace('-','·')}</span></a>"""

    item_ld = {"@context":"https://schema.org","@type":"ItemList","name":title,
      "itemListElement":[{"@type":"ListItem","position":i+1,"url":f"https://saveonsub.com/bn/p/{p['id']}.html","name":p['name'].replace('🎁 ','')} for i,p in enumerate(items)]}
    crumb_ld = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
      {"@type":"ListItem","position":1,"name":"হোম","item":"https://saveonsub.com/bn.html"},
      {"@type":"ListItem","position":2,"name":"সব প্রোডাক্ট","item":"https://saveonsub.com/all.html"},
      {"@type":"ListItem","position":3,"name":cbn,"item":f"https://saveonsub.com/bn/c/{s}.html"}]}

    bn_nav = nav_bn("../../")
    page = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://saveonsub.com/bn/c/{s}.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/c/{s}.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/c/{s}.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/c/{s}.html">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/bn/c/{s}.html">
<meta property="og:locale" content="bn_BD"><meta name="theme-color" content="#06181a">
<link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png">
<link rel="manifest" href="../../assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="../../assets/style.css">
<script type="application/ld+json">{json.dumps(item_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">মূল কন্টেন্টে যান</a>
{bn_nav}
<main id="main"><div class="wrap">
  <div class="crumbs"><a href="../../bn.html">হোম</a> › <a href="../../all.html">সাবস্ক্রিপশন</a> › {esc(cbn)}</div>
  <h1 style="font-size:clamp(26px,4vw,38px)">{esc(cbn)} — <span class="grad-text">বাংলাদেশে</span></h1>
  <p class="sub mt2">{esc(intro)}</p>
  <p class="sub" style="font-size:14px;margin-top:6px">🏷️ সৎ লেবেল · 💳 বিকাশ/নগদ/রকেট · 🛡️ প্রতিটি প্ল্যানে ওয়ারেন্টি</p>
  <div class="grid g4 mt3">{cards}</div>
  <div class="notice green mt3">🤝 কোন {esc(cbn)} নেবেন বুঝতে পারছেন না? <a href="../../quiz.html" style="color:var(--green2);font-weight:700">৬০ সেকেন্ডের কুইজ</a> দিন বা <a href="https://wa.me/8801305869242" style="color:var(--green2);font-weight:700">হোয়াটসঅ্যাপে জিজ্ঞেস করুন</a> — ফ্রি অপশন যথেষ্ট হলে সেটাও সৎভাবে বলব।</div>
</div></main>
<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!'" aria-label="হোয়াটসঅ্যাপ">💬 হোয়াটসঅ্যাপ</button>
<a class="fab fab-quiz" href="../../quiz.html" aria-label="কুইজ">🧭 কোনটা নেব</a>
<footer><div class="wrap">
  <div class="fcols">
    <div><span class="logo">SAVE<em>ON</em>SUB</span><p style="margin-top:10px;max-width:280px">সৎ দামে আসল প্রিমিয়াম সাবস্ক্রিপশন। একটি SYSmoAI উদ্যোগ।</p></div>
    <div><b>স্টোর</b><a href="../../all.html">সাবস্ক্রিপশন</a><a href="../../quiz.html">কোনটা নেব</a><a href="../../how-to-order.html">কীভাবে অর্ডার</a><a href="../../offers.html">অফার</a></div>
    <div><b>সাহায্য</b><a href="../../contact.html">যোগাযোগ</a><a href="../../track.html">অর্ডার ট্র্যাক</a><a href="../../students.html">স্টুডেন্ট</a></div>
    <div><b>ভরসা</b><a href="../../warranty.html">ওয়ারেন্টি</a><a href="../../refund.html">রিফান্ড</a><a href="../../faq.html">প্রশ্নোত্তর</a><a href="../../sitemap.html">সাইটম্যাপ</a></div>
  </div>
  <p class="fine">© 2026 SAVEONSUB · একটি SYSmoAI উদ্যোগ।</p>
</div></footer>
<script src="../../assets/app.js"></script>
</body>
</html>"""
    open(f"bn/c/{s}.html", 'w').write(page)
    bcount += 1
print(f"OK: generated {bcount} Bangla category pages in bn/c/")
