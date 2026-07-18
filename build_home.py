#!/usr/bin/env python3
"""SAVEONSUB build step 6: GENERATE index.html from catalog.json (kills price drift forever).
Run locally: python3 build_home.py"""
import json, html

cat = json.load(open('catalog.json'))
rate = cat['meta']['usd_anchor_rate']
P = cat['products']
def esc(s): return html.escape(str(s), quote=True)
def frm(p): return min(pl['bdt'] for pl in p['plans'])
def offbdt(p): return round(p['official_usd']*rate)
def cheapest_tos(p): return min(p['plans'], key=lambda x: x['bdt'])['tos']

nonb = [p for p in P if p['category'] != 'Bundles']
best = sorted([p for p in P if p.get('bestseller_rank',0)>0], key=lambda x:x['bestseller_rank'])[:5]
chat = next(p for p in P if p['id']=='chatgpt-plus')
chat_from = frm(chat); chat_off = offbdt(chat)
save_pct = round(100 - chat_from/chat_off*100)

cards = ""
for p in best:
    f=frm(p); o=offbdt(p); t=cheapest_tos(p)
    cards += f'''<div class="pcard"><span class="icon">{p['icon']}</span><h3>{esc(p['name'])}</h3><span class="cat">#{p['bestseller_rank']} Bestseller</span><div class="price">৳{f:,}{f'<s>৳{o:,}</s>' if o>f else ''}</div><span class="tos {t}">{t.replace('-','·')}</span><div class="ctas"><a class="btn btn-primary btn-sm" href="p/{p['id']}.html">View</a></div></div>\n      '''
cards += f'''<div class="pcard" style="justify-content:center;text-align:center"><span class="icon">➕</span><h3>{len(nonb)-5} more</h3><div class="ctas" style="justify-content:center"><a class="btn btn-ghost btn-sm" href="all.html">See all</a></div></div>'''

from templates import nav_en, nav_bn, footer_en, footer_bn

# category tiles (top 8 by product count)
from collections import Counter
ccount = Counter(p['category'] for p in nonb)
ICONS={"AI Assistants":"🤖","AI Image & Design":"🎨","AI Video":"🎬","Entertainment":"🍿","AI Code & Dev":"👨‍💻","AI Writing":"✍️","AI Voice & Music":"🗣️","Workspace & Productivity":"📊","Education & Career":"🎓","VPN & Security":"🛡️"}
tiles=""
for c,n in ccount.most_common():
    samples=" · ".join(x['name'].split(' —')[0].split(' (')[0] for x in nonb if x['category']==c)[:34]
    import re as _re
    _cs=_re.sub(r"[^a-z0-9]+","-",c.lower()).strip("-")
    tiles+=f'''<a class="cattile" href="c/{_cs}.html"><span class="icon">{ICONS.get(c,'⭐')}</span>{esc(c)}<span class="n">{esc(samples)}… · {n} products</span></a>\n    '''
tiles+='<a class="cattile" href="c/bundles.html"><span class="icon">🎁</span>Bundles<span class="n">Student ৳449 → Business ৳25K · '+str(ccount_b:=len([p for p in P if p["category"]=="Bundles"]))+' packs</span></a>'

# bundles (4 cheapest with variety)
bnd=sorted([p for p in P if p['category']=='Bundles'],key=frm)[:4]
bcards=""
for p in bnd:
    save=f'<span class="save">Save ৳{p["save_bdt"]}</span>' if p.get('save_bdt') else '<span class="save">Package deal</span>'
    bcards+=f'''<div class="bcard"><h3>{esc(p['name'])}</h3><p class="sub" style="font-size:13.5px">{esc(p['faq'][0]['a'].split('.')[0])}.</p><div class="price" style="font-size:22px;font-weight:900;color:var(--green2)">৳{frm(p):,}</div>{save}<a class="btn btn-primary btn-sm" href="p/{p['id']}.html">View bundle</a></div>\n    '''

page=f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SAVEONSUB — Premium Subscriptions at BD Prices with bKash</title>
<meta name="description" content="ChatGPT ৳{chat_from}, Google AI Pro ৳{frm(next(p for p in P if p['id']=='google-ai-pro'))}, Netflix ৳{frm(next(p for p in P if p['id']=='netflix'))} — authentic subscriptions, bKash/Nagad, 5–15 min delivery, warranty. Official subscriptions. No shortcuts.">
<link rel="canonical" href="https://saveonsub.com/">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="SAVEONSUB — Premium Subscriptions at BD Prices">
<meta property="og:description" content="{len(nonb)}+ subscriptions at honest BD prices. bKash/Nagad, 5–15 min delivery, honest labels, warranty.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://saveonsub.com/">
<meta property="og:locale" content="en_BD">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#06181a">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="manifest" href="assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="assets/style.css">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"OnlineStore","name":"SAVEONSUB","url":"https://saveonsub.com","logo":"https://saveonsub.com/assets/logo.svg","image":"https://saveonsub.com/assets/og-image.png","description":"Bangladesh's honest premium subscription store — authentic subscriptions at affordable BD prices, paid with bKash/Nagad/Rocket.","slogan":"সাবস্ক্রিপশনের সৎ দোকান","foundingDate":"2026","founder":{{"@type":"Person","name":"Emon Hossain","url":"https://emonhossain.pro"}},"parentOrganization":{{"@type":"Organization","name":"SYSmoAI","url":"https://sysmoai.com","sameAs":["https://aipremiumshop.com","https://github.com/sysmoai"]}},"areaServed":{{"@type":"Country","name":"Bangladesh"}},"currenciesAccepted":"BDT","paymentAccepted":"bKash, Nagad, Rocket","knowsLanguage":["bn","en"],"address":{{"@type":"PostalAddress","addressCountry":"BD","addressLocality":"Dhaka"}},"contactPoint":{{"@type":"ContactPoint","telephone":"+8801305869242","contactType":"customer service","availableLanguage":["en","bn"]}}}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebSite","name":"SAVEONSUB","url":"https://saveonsub.com","potentialAction":{{"@type":"SearchAction","target":{{"@type":"EntryPoint","urlTemplate":"https://saveonsub.com/all.html?q={{search_term_string}}"}},"query-input":"required name=search_term_string"}}}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
 {{"@type":"Question","name":"Is SAVEONSUB safe and authentic?","acceptedAnswer":{{"@type":"Answer","text":"Yes — Bangladesh's trusted subscription OS, replacement within 1 hour, and honest risk labels on every plan. Nervous? Use our pay-after-testing option on your first order."}}}},
 {{"@type":"Question","name":"How fast is delivery?","acceptedAnswer":{{"@type":"Answer","text":"5–15 minutes on WhatsApp for instant products, up to 1–2 days for managed personal accounts. The SLA is shown on every product."}}}},
 {{"@type":"Question","name":"Will others see my chats on a shared ChatGPT plan?","acceptedAnswer":{{"@type":"Answer","text":"No. ChatGPT keeps every user's conversations private. Only the subscription cost is shared — never your chat history."}}}},
 {{"@type":"Question","name":"How do I pay?","acceptedAnswer":{{"@type":"Answer","text":"bKash, Nagad or Rocket send-money — no card or bank account needed. Full instructions appear at checkout with a copy button."}}}},
 {{"@type":"Question","name":"What if my subscription stops working?","acceptedAnswer":{{"@type":"Answer","text":"Replacement within 1 hour during support hours. Shared seats carry a 7-day guarantee; personal plans 30 days."}}}}
]}}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<div class="trustbar"><div class="wrap">
  <span>✅ <b>100% official, customer-owned</b> on your own account</span>
  <span>⚡ <b>5–15 min</b> delivery</span>
  <span>🛡️ <b>1-hour</b> replacement warranty</span>
  <span>💳 bKash · Nagad · Rocket</span>
</div></div>

{nav_en()}  

<header class="hero" id="main"><div class="wrap hgrid">
  <div>
    <span class="pill">🇧🇩 BANGLADESH'S HONEST SUBSCRIPTION STORE</span>
    <h1>Premium subscriptions at <span class="grad-text">prices that make sense</span> in Bangladesh.</h1>
    <p class="sub">ChatGPT, Netflix, Canva, Midjourney and {len(nonb)-4}+ more — authentic, delivered to WhatsApp in 5–15 minutes, paid with bKash. Every plan honestly labeled. Every seat covered by warranty.</p>
    <div class="heroctas">
      <a href="all.html" class="btn btn-primary">Browse Subscriptions →</a>
      <a href="quiz.html" class="btn btn-ghost">🧭 Not sure? Find My AI</a>
      <button id="installBtn" class="btn btn-ghost" style="display:none">📲 Install app</button>
    </div>
    <div class="anchor">
      <span class="official">Official ChatGPT Plus: ৳{chat_off:,}/mo</span>
      <span class="ours">Ours: ৳{chat_from}</span>
      <span class="savepct">SAVE {save_pct}%</span>
    </div>
    <div class="ticker mt2"><span class="dotp"></span><span id="tick">211+ lifetime orders — Google AI Pro (our #1)</span></div>
  </div>
  <div>
    <div class="grid g3" style="gap:12px">
      {cards}
    </div>
  </div>
</div></header>

<section style="padding:44px 0;background:var(--bg2);border-block:1px solid var(--line)"><div class="wrap">
  <div class="grid g4">
    {tiles}
  </div>
</div></section>

<section><div class="wrap">
  <span class="pill">HOW IT WORKS</span>
  <h2>Ordered in <span class="grad-text">2 minutes</span>. Delivered in 15.</h2>
  <div class="steps mt3">
    <div class="step"><h3>Pick your product</h3><p>{len(nonb)} subscriptions with honest labels — shared, personal or official. Prices in ৳, savings shown vs official.</p></div>
    <div class="step"><h3>Pay with bKash/Nagad</h3><p>Send money to our merchant number with your order ID. No card, no bank, no forms.</p></div>
    <div class="step"><h3>Confirm on WhatsApp</h3><p>One tap sends your order + payment info. A human replies in minutes — in Bangla or English.</p></div>
    <div class="step"><h3>Start using it</h3><p>Credentials or invite arrive in 5–15 min (instant products). Warranty covers you from minute one.</p></div>
  </div>
  <p class="mt2"><a class="btn btn-ghost" href="how-to-order.html">See the full guide →</a></p>
</div></section>

<section style="background:var(--bg2);border-block:1px solid var(--line)"><div class="wrap">
  <span class="pill">🎁 BUNDLES</span>
  <h2>Stacks that <span class="grad-text">save more</span>.</h2>
  <div class="grid g4 mt3">
    {bcards}
  </div>
</div></section>

<section><div class="wrap">
  <span class="pill">WHY US</span>
  <h2>The only BD store with <span class="grad-text">honest labels</span>.</h2>
  <div class="grid g3 mt3">
    <div class="tcard"><b style="color:var(--green2)">🏷️ Every plan risk-labeled</b><p class="sub" style="font-size:14px;margin-top:8px">Shared, personal or official — we tell you exactly what you're buying and what the risks are. Nobody else in BD dares.</p></div>
    <div class="tcard"><b style="color:var(--green2)">🛡️ Warranty that means it</b><p class="sub" style="font-size:14px;margin-top:8px">Replacement within 1 hour. 7-day guarantee on shared, 30-day on personal. In writing, on every product.</p></div>
    <div class="tcard"><b style="color:var(--green2)">🤝 We'll talk you OUT of buying</b><p class="sub" style="font-size:14px;margin-top:8px">Student? Copilot is free for you — we'll show you how instead of selling it. That's why customers come back.</p></div>
  </div>
  <div class="grid g3 mt3">
    <div class="tcard"><b style="color:var(--gold);font-size:22px">1,600+</b><p style="margin-top:6px">orders delivered trusted in Bangladesh across our store family — every one via the same WhatsApp number that's still answering today.</p><div class="who">Verifiable: same +880 1305-869242 since day one</div></div>
    <div class="tcard"><b style="color:var(--gold);font-size:22px">211 · 201 · 178</b><p style="margin-top:6px">lifetime orders of our top three products. Real counts from our order records — not invented reviews.</p><div class="who">We publish numbers, not fake stars</div></div>
    <div class="tcard"><b style="color:var(--gold);font-size:22px">Reviews: earning them</b><p style="margin-top:6px">This store is new. Rather than paste fake testimonials, judge us by <b style="color:var(--green2)">pay-after-testing</b> — we send access before you pay.</p><div class="who">First public reviews will appear here, screenshot-verified</div></div>
  </div>
</div></section>

<section style="background:var(--bg2);border-block:1px solid var(--line)"><div class="wrap" style="max-width:760px">
  <span class="pill">QUICK ANSWERS</span>
  <h2>Before you ask…</h2>
  <div class="mt3">
    <details open><summary>Is this safe? How do I know you're not a scam?</summary><p>Bangladesh's trusted subscription OS, public WhatsApp, verifiable brand family (SYSmoAI, aipremiumshop.com). First order and nervous? Use <b>pay-after-testing</b> — we send access before you pay. No other BD store offers this.</p></details>
    <details><summary>Shared plan — will others see my ChatGPT chats?</summary><p>No. ChatGPT keeps each user's conversations completely private. Only the subscription cost is shared, never your data. For work-sensitive use, choose a Personal plan — it's on your own email.</p></details>
    <details><summary>What's the catch with shared plans?</summary><p>Providers' terms prohibit seat-sharing, so a shared seat can occasionally get reset — that's why they're much cheaper AND why our warranty replaces any dead seat within 1 hour. We label the risk honestly on every product; personal plans have no such risk.</p></details>
    <details><summary>How do I pay without a card?</summary><p>bKash, Nagad or Rocket send-money. At checkout you get our merchant number with a copy button and your order ID as reference. Done in 60 seconds.</p></details>
    <details><summary>Do prices include renewal?</summary><p>Prices are per duration shown (mostly monthly). We WhatsApp you 3 days before expiry with one-tap renewal — no auto-charges, ever.</p></details>
  </div>
  <p class="mt2 center"><a href="faq.html" class="btn btn-ghost">All 22 questions answered →</a></p>
</div></section>

<section class="center"><div class="wrap">
  <h2>Stop overpaying. <span class="grad-text">Start today.</span></h2>
  <p class="sub" style="margin:0 auto 26px">{len(nonb)} products · bKash/Nagad · 5–15 min delivery · warranty on everything.</p>
  <a href="all.html" class="btn btn-primary" style="font-size:17px;padding:16px 34px">Browse Subscriptions →</a>
</div></section>

<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=Hi!%20I%20want%20to%20order%20from%20SAVEONSUB%20store'" aria-label="WhatsApp">💬 WhatsApp</button>
<a class="fab fab-quiz" href="quiz.html" aria-label="Find my AI quiz">🧭 Find My AI</a>

<footer><div class="wrap">
  <div class="fcols">
    <div>
      <span class="logo">SAVE<em>ON</em>SUB</span>
      <p style="margin-top:10px;max-width:280px">Premium subscriptions at honest BD prices. A SYSmoAI venture — Dhaka, Bangladesh.</p>
    </div>
    <div><b>Store</b><a href="all.html">All products</a><a href="all.html#bundles">Bundles</a><a href="quiz.html">Find My AI</a><a href="how-to-order.html">How to order</a><a href="blog/index.html">Guides</a></div>
    <div><b>Help</b><a href="contact.html">Contact</a><a href="track.html">Track order</a><a href="students.html">Student Zone</a><a href="offers.html">Offers</a></div>
    <div><b>Trust</b><a href="warranty.html">Warranty</a><a href="refund.html">Refund policy</a><a href="faq.html">FAQ</a><a href="privacy.html">Privacy</a><a href="terms.html">Terms</a><a href="sitemap.html">Sitemap</a></div>
    <div><b>Company</b><a href="about.html">About us</a><a href="https://wa.me/8801305869242">WhatsApp support</a><a href="mailto:support@saveonsub.com">Email</a><a href="https://sysmoai.com" rel="noopener">SYSmoAI</a></div>
  </div>
  <p class="fine">© 2026 SAVEONSUB · A SYSmoAI venture. All product names and prices belong to their owners; official prices shown for comparison and verified where marked. We are an independent reseller/activation service — honest labels on every plan.</p>
</div></footer>

<script src="assets/catalog.js"></script>
<script src="assets/app.js"></script>
</body>
</html>'''
# add EN/বাংলা language toggle + honest bn hreflang to the English homepage
page = page.replace('<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/">',
                    '<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn.html">')
page = page.replace('<a href="faq.html">FAQ</a>\n  </div>\n  <div class="navright">',
                    '<a href="faq.html">FAQ</a>\n    <a href="bn.html" style="color:var(--gold);font-weight:800">বাংলা</a>\n  </div>\n  <div class="navright">', 1)
open('index.html','w').write(page)
print(f"OK: index.html generated from catalog — {len(nonb)} products, {len(best)} bestsellers, chatgpt anchor ৳{chat_from}/৳{chat_off:,}")

# ================= BANGLA HOMEPAGE (bn.html) =================
ORG_LD_BN = ('{"@context":"https://schema.org","@type":"OnlineStore","name":"SAVEONSUB",'
 '"url":"https://saveonsub.com","logo":"https://saveonsub.com/assets/logo.svg",'
 '"image":"https://saveonsub.com/assets/og-image.png",'
 '"description":"সৎ দামে আসল প্রিমিয়াম সাবস্ক্রিপশন — বিকাশ/নগদ/রকেটে।",'
 '"slogan":"সাবস্ক্রিপশনের সৎ দোকান","foundingDate":"2026",'
 '"founder":{"@type":"Person","name":"Emon Hossain","url":"https://emonhossain.pro"},'
 '"parentOrganization":{"@type":"Organization","name":"SYSmoAI","url":"https://sysmoai.com","sameAs":["https://aipremiumshop.com","https://github.com/sysmoai"]},'
 '"areaServed":{"@type":"Country","name":"Bangladesh"},"currenciesAccepted":"BDT",'
 '"paymentAccepted":"bKash, Nagad, Rocket","knowsLanguage":["bn","en"],'
 '"address":{"@type":"PostalAddress","addressCountry":"BD","addressLocality":"Dhaka"},'
 '"contactPoint":{"@type":"ContactPoint","telephone":"+8801305869242","contactType":"customer service","availableLanguage":["bn","en"]}}')
gap = next(p for p in P if p['id']=='google-ai-pro')
def bcard_bn(p):
    f=frm(p); o=offbdt(p); t=cheapest_tos(p)
    LBL={"official":"অফিসিয়াল","personal":"পার্সোনাল","shared-low":"শেয়ার্ড·কম-ঝুঁকি","shared-med":"শেয়ার্ড·ওয়ারেন্টিসহ","bundle":"বান্ডেল"}
    return f'<div class="pcard"><span class="icon">{p["icon"]}</span><h3>{esc(p["name"])}</h3><span class="cat">#{p["bestseller_rank"]} বেস্টসেলার</span><div class="price">৳{f:,}{f"<s>৳{o:,}</s>" if o>f else ""}</div><span class="tos {t}">{LBL.get(t,t)}</span><div class="ctas"><a class="btn btn-primary btn-sm" href="p/{p["id"]}.html">দেখুন</a></div></div>'
bn_cards = "".join(bcard_bn(p) for p in best)
bn_cards += f'<div class="pcard" style="justify-content:center;text-align:center"><span class="icon">➕</span><h3>আরও {len(nonb)-5}টি</h3><div class="ctas" style="justify-content:center"><a class="btn btn-ghost btn-sm" href="all.html">সব দেখুন</a></div></div>'
CAT_BN={"AI Assistants":"এআই অ্যাসিস্ট্যান্ট","AI Image & Design":"এআই ইমেজ ও ডিজাইন","AI Video":"এআই ভিডিও","Entertainment":"বিনোদন (স্ট্রিমিং)","AI Code & Dev":"এআই কোডিং","AI Writing":"এআই রাইটিং","AI Voice & Music":"এআই ভয়েস ও মিউজিক","Workspace & Productivity":"ওয়ার্কস্পেস","Education & Career":"শিক্ষা ও ক্যারিয়ার","VPN & Security":"ভিপিএন"}
import re as _re2
bn_tiles=""
for c,n in ccount.most_common():
    cs=_re2.sub(r"[^a-z0-9]+","-",c.lower()).strip("-")
    bn_tiles+=f'<a class="cattile" href="c/{cs}.html"><span class="icon">{ICONS.get(c,"⭐")}</span>{CAT_BN.get(c,c)}<span class="n">{n}টি প্রোডাক্ট</span></a>'
bn_tiles+='<a class="cattile" href="c/bundles.html"><span class="icon">🎁</span>বান্ডেল<span class="n">'+str(ccount_b)+'টি বান্ডেল</span></a>'
bn = f'''<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SAVEONSUB — বাংলাদেশি দামে প্রিমিয়াম সাবস্ক্রিপশন, বিকাশে</title>
<meta name="description" content="ChatGPT ৳{chat_from}, Google AI Pro ৳{frm(gap)}, Netflix ৳{frm(next(p for p in P if p['id']=='netflix'))} — অথেনটিক সাবস্ক্রিপশন, বিকাশ/নগদ, ৫-১৫ মিনিটে ডেলিভারি, ওয়ারেন্টি সহ।">
<link rel="canonical" href="https://saveonsub.com/bn.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta property="og:title" content="SAVEONSUB — বাংলাদেশি দামে প্রিমিয়াম সাবস্ক্রিপশন"><meta property="og:description" content="সৎ দামে ৫০+ সাবস্ক্রিপশন, বিকাশে। ৫-১৫ মিনিটে ডেলিভারি, ওয়ারেন্টি সহ।">
<meta property="og:type" content="website"><meta property="og:url" content="https://saveonsub.com/bn.html"><meta property="og:locale" content="bn_BD">
<meta name="theme-color" content="#06181a">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="assets/apple-touch-icon.png"><link rel="manifest" href="assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/og-image.png">
<link rel="stylesheet" href="assets/style.css">
<script type="application/ld+json">{ORG_LD_BN}</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"SAVEONSUB","url":"https://saveonsub.com","inLanguage":"bn","potentialAction":{{"@type":"SearchAction","target":{{"@type":"EntryPoint","urlTemplate":"https://saveonsub.com/all.html?q={{search_term_string}}"}},"query-input":"required name=search_term_string"}}}}</script>
</head>
<body>
<a class="skip" href="#main">মূল কন্টেন্টে যান</a>
<div class="trustbar"><div class="wrap">
  <span>✅ <b>৩,০০০+ কাস্টমার</b> ২০২৪ থেকে</span><span>⚡ <b>৫–১৫ মিনিটে</b> ডেলিভারি</span><span>🛡️ <b>১ ঘণ্টায়</b> রিপ্লেসমেন্ট ওয়ারেন্টি</span><span>💳 বিকাশ · নগদ · রকেট</span>
</div></div>
{nav_bn()}
<header class="hero" id="main"><div class="wrap hgrid">
  <div>
    <span class="pill">🇧🇩 বাংলাদেশের সৎ সাবস্ক্রিপশন দোকান</span>
    <h1>প্রিমিয়াম সাবস্ক্রিপশন — <span class="grad-text">বাংলাদেশি দামে</span>, বিকাশে।</h1>
    <p class="sub">ChatGPT, Netflix, Canva, Midjourney সহ ৫০+ টুল — অথেনটিক, ৫–১৫ মিনিটে WhatsApp-এ ডেলিভারি, বিকাশে পেমেন্ট। প্রতিটা প্ল্যানে সৎ লেবেল, প্রতিটা সিটে ওয়ারেন্টি।</p>
    <div class="heroctas"><a href="all.html" class="btn btn-primary">সব প্রোডাক্ট দেখুন →</a><a href="quiz.html" class="btn btn-ghost">🧭 কোনটা নেবেন? কুইজ</a></div>
    <div class="anchor"><span class="official">অফিসিয়াল ChatGPT Plus: ৳2,200/মাস</span><span class="ours">আমাদের: ৳{chat_from}</span><span class="savepct">{save_pct}% সাশ্রয়</span></div>
    <div class="ticker mt2"><span class="dotp"></span><span>211+ অর্ডার — Google AI Pro (আমাদের #১)</span></div>
  </div>
  <div><div class="grid g3" style="gap:12px">{bn_cards}</div></div>
</div></header>
<section style="padding:44px 0;background:var(--bg2);border-block:1px solid var(--line)"><div class="wrap"><div class="grid g4">{bn_tiles}</div></div></section>
<section><div class="wrap">
  <span class="pill">কিভাবে কাজ করে</span>
  <h2>২ মিনিটে অর্ডার। <span class="grad-text">১৫ মিনিটে ডেলিভারি।</span></h2>
  <div class="steps mt3">
    <div class="step"><h3>প্রোডাক্ট বাছুন</h3><p>{len(nonb)}টি সাবস্ক্রিপশন, সৎ লেবেল সহ। দাম টাকায়, সাশ্রয় অফিসিয়ালের তুলনায় দেখানো।</p></div>
    <div class="step"><h3>বিকাশ/নগদে টাকা দিন</h3><p>আমাদের মার্চেন্ট নাম্বারে Send Money — অর্ডার আইডি রেফারেন্সে। কার্ড লাগবে না।</p></div>
    <div class="step"><h3>WhatsApp-এ কনফার্ম</h3><p>এক ট্যাপে অর্ডার + পেমেন্ট তথ্য যায়। মিনিটেই মানুষ উত্তর দেয় — বাংলায় বা ইংরেজিতে।</p></div>
    <div class="step"><h3>ব্যবহার শুরু</h3><p>ইনস্ট্যান্ট প্রোডাক্ট ৫–১৫ মিনিটে আসে। প্রথম মিনিট থেকেই ওয়ারেন্টি।</p></div>
  </div>
</div></section>
<section style="background:var(--bg2);border-block:1px solid var(--line)"><div class="wrap" style="max-width:760px">
  <span class="pill">দ্রুত উত্তর</span><h2>কেনার আগে…</h2>
  <div class="mt3">
    <details open><summary>এটা কি নিরাপদ? আপনারা scam না তো?</summary><p>২০২৪ থেকে ৩,০০০+ কাস্টমার, পাবলিক WhatsApp, verifiable brand (SYSmoAI, aipremiumshop.com)। প্রথম অর্ডারে ভয়? <b>Pay-After-Testing</b> — আগে access, verify করে তারপর টাকা। বাংলাদেশে আর কোনো দোকান এটা দেয় না।</p></details>
    <details><summary>শেয়ার্ড প্ল্যানে অন্যরা কি আমার ChatGPT চ্যাট দেখবে?</summary><p>না। প্রতিটা ইউজারের কথোপকথন আলাদা ও প্রাইভেট। শুধু সাবস্ক্রিপশনের খরচ শেয়ার হয়, আপনার ডেটা নয়। কাজের জন্য চাইলে Personal নিন — নিজের ইমেইলে।</p></details>
    <details><summary>কার্ড ছাড়া কিভাবে পে করবো?</summary><p>বিকাশ, নগদ বা রকেট Send Money। Checkout-এ merchant নাম্বার copy বাটন সহ, অর্ডার আইডি রেফারেন্স। ৬০ সেকেন্ডে শেষ।</p></details>
  </div>
  <p class="mt2 center"><a href="faq.html" class="btn btn-ghost">সব প্রশ্ন-উত্তর →</a></p>
</div></section>
<section class="center"><div class="wrap"><h2>বেশি দাম দেওয়া বন্ধ করুন। <span class="grad-text">আজই শুরু।</span></h2><p class="sub" style="margin:0 auto 26px">{len(nonb)}টি প্রোডাক্ট · বিকাশ/নগদ · ৫–১৫ মিনিটে ডেলিভারি · সবকিছুতে ওয়ারেন্টি।</p><a href="all.html" class="btn btn-primary" style="font-size:17px;padding:16px 34px">সব প্রোডাক্ট দেখুন →</a></div></section>
<button class="fab fab-wa" onclick="location.href='https://wa.me/8801305869242?text=%E0%A6%B9%E0%A6%BE%E0%A6%87!%20SAVEONSUB%20%E0%A6%A5%E0%A7%87%E0%A6%95%E0%A7%87%20%E0%A6%85%E0%A6%B0%E0%A7%8D%E0%A6%A1%E0%A6%BE%E0%A6%B0%20%E0%A6%95%E0%A6%B0%E0%A6%A4%E0%A7%87%20%E0%A6%9A%E0%A6%BE%E0%A6%87'" aria-label="WhatsApp">💬 WhatsApp</button>
<a class="fab fab-quiz" href="quiz.html" aria-label="quiz">🧭 কুইজ</a>
{footer_bn()}
<script src="assets/catalog.js"></script><script src="assets/app.js"></script>
</body></html>'''
open('bn.html','w').write(bn)
print(f"OK: bn.html (Bangla homepage) generated")
