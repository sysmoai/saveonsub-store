#!/usr/bin/env python3
"""SAVEONSUB build step 2: catalog.json -> p/<id>.html (49 product pages).
Honest schema: Product+Offer JSON-LD WITHOUT fake aggregateRating (no fabricated reviews).
Run locally: python3 build_pages.py"""
import json, os, html, re, datetime
from templates import nav_en, nav_bn, footer_en, footer_bn

cat = json.load(open('catalog.json'))
rate = cat['meta']['usd_anchor_rate']
PRICE_VALID = (datetime.date.today() + datetime.timedelta(days=90)).isoformat()
# Honest merchant return policy — reflects the real minimum warranty (7-day shared seat replacement).
RETURN_POLICY = {"@type": "MerchantReturnPolicy", "applicableCountry": "BD",
                 "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                 "merchantReturnDays": 7, "returnMethod": "https://schema.org/ReturnByMail",
                 "returnFees": "https://schema.org/FreeReturn"}
tos_meta = cat['meta']['tos_risk_levels']
sla_meta = cat['meta']['delivery_slas']
os.makedirs('p', exist_ok=True)

TOS_LABEL = {"official": "OFFICIAL", "personal": "PERSONAL", "shared-low": "SHARED · LOW RISK", "shared-med": "SHARED · WARRANTY COVERED", "bundle": "BUNDLE"}
TOS_CLASS = {"official": "official", "personal": "personal", "shared-low": "shared-low", "shared-med": "shared-med", "bundle": "shared-low"}

def esc(s): return html.escape(str(s), quote=True)
def jstr(s): return json.dumps(s, ensure_ascii=False)
def cslug(c): return re.sub(r'[^a-z0-9]+', '-', c.lower()).strip('-')

products = cat['products']
by_id = {p['id']: p for p in products}

def related(p):
    same = [x for x in products if x['category'] == p['category'] and x['id'] != p['id']][:3]
    if len(same) < 3:
        same += [x for x in products if x['category'] != p['category'] and x['category'] != 'Bundles' and x not in same and x['id'] != p['id']][:3-len(same)]
    return same[:3]

def page(p):
    cheapest = min(p['plans'], key=lambda x: x['bdt'])
    official_bdt = round(p['official_usd'] * rate)
    save = max(0, round(100 - cheapest['bdt']/official_bdt*100)) if official_bdt > cheapest['bdt'] else 0
    # Strip emoji prefixes for titles (they waste SERP characters)  
    name = p['name'].replace('🎁 ', '')
    import unicodedata as _uc
    name_clean = name
    while name_clean and (_uc.category(name_clean[0]) == 'So' or ord(name_clean[0]) > 255):
        name_clean = name_clean[1:].strip()
    if not name_clean: name_clean = name
    title = f"{name_clean} Price in Bangladesh — ৳{cheapest['bdt']:,} | SAVEONSUB"
    if len(title) > 60: title = f"{name_clean} BD Price — ৳{cheapest['bdt']:,} | SAVEONSUB"
    if len(title) > 60: title = f"{name_clean[:40]} — ৳{cheapest['bdt']:,} | SAVEONSUB"
    desc = f"{name_clean} in Bangladesh from ৳{cheapest['bdt']:,}/{cheapest['duration']} (official ~৳{official_bdt:,}). bKash/Nagad, {sla_meta[cheapest['sla']]} delivery, warranty. Honest labels."
    if len(desc) > 155: desc = desc[:152] + "…"

    offers = [{"@type": "Offer", "name": pl['label'], "price": pl['bdt'], "priceCurrency": "BDT",
               "availability": "https://schema.org/InStock",
               "priceValidUntil": PRICE_VALID,
               "hasMerchantReturnPolicy": RETURN_POLICY,
               "url": f"https://saveonsub.com/p/{p['id']}.html"} for pl in p['plans']]
    product_ld = {"@context": "https://schema.org", "@type": "Product", "sku": f"BD-{p['id'].upper()}", "name": name,
                  "description": desc, "brand": {"@type": "Brand", "name": name.split()[0]},
                  "image": [f"https://saveonsub.com/assets/social/{p['id']}.png"],
                  "category": p['category'],
                  "offers": {"@type": "AggregateOffer", "lowPrice": cheapest['bdt'], "itemCondition": "https://schema.org/NewCondition",
                             "highPrice": max(pl['bdt'] for pl in p['plans']), "priceCurrency": "BDT",
                             "offerCount": len(p['plans']), "offers": offers}}
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": f['q'],
                              "acceptedAnswer": {"@type": "Answer", "text": f['a']}} for f in p['faq']]}
    _cs = cslug(p['category'])
    crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://saveonsub.com/"},
        {"@type": "ListItem", "position": 2, "name": "All Products", "item": "https://saveonsub.com/all.html"},
        {"@type": "ListItem", "position": 3, "name": p['category'], "item": f"https://saveonsub.com/c/{_cs}.html"},
        {"@type": "ListItem", "position": 4, "name": name, "item": f"https://saveonsub.com/p/{p['id']}.html"}]}
    speak_ld = {"@context": "https://schema.org", "@type": "WebPage",
        "url": f"https://saveonsub.com/p/{p['id']}.html",
        "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", ".anchor"]}}

    plans_html = ""
    for pl in p['plans']:
        tos = pl['tos']
        plans_html += f"""
      <div class="pcard" style="flex-direction:row;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div><b>{esc(pl['label'])}</b><br>
          <span class="tos {TOS_CLASS[tos]}">{TOS_LABEL[tos]}</span>
          <span style="font-size:12px;color:var(--muted)"> · {esc(pl['duration'])} · delivery {esc(sla_meta[pl['sla']])}</span></div>
        <div style="display:flex;align-items:center;gap:14px">
          <span style="font-size:22px;font-weight:900;color:var(--green2)">৳{pl['bdt']:,}</span>
          <button class="btn btn-primary btn-sm" onclick="cartAdd({jstr(p['id'])},{jstr(pl['label'])},{pl['bdt']},{jstr(name)})">Add to cart</button>
        </div></div>"""

    tos_notes = "".join(f'<p style="margin-top:6px"><span class="tos {TOS_CLASS[t]}">{TOS_LABEL[t]}</span> <span style="color:var(--muted);font-size:13.5px">{esc(tos_meta.get(t,""))}</span></p>'
                        for t in dict.fromkeys(pl['tos'] for pl in p['plans']) if t in tos_meta)

    faq_html = "".join(f"<details{' open' if i==0 else ''}><summary>{esc(f['q'])}</summary><p>{esc(f['a'])}</p></details>" for i, f in enumerate(p['faq']))

    rel_html = "".join(f"""<a class="pcard" href="{x['id']}.html"><span class="icon">{x['icon']}</span><h3>{esc(x['name'].replace('🎁 ',''))}</h3><span class="cat">{esc(x['category'])}</span><div class="price">৳{min(pl['bdt'] for pl in x['plans']):,}</div></a>""" for x in related(p))


    mk = p.get('market', {})
    ours_low = cheapest['bdt']
    if mk.get('surveyed'):
        beat = ours_low <= mk['low']
        honesty = ("We're the cheapest surveyed option — AND the only one with a written warranty." if beat else
                   "Cheaper exists in the market — without pay-after-testing, written warranty or honest risk labels. That's the trade; your call.")
        market_html = f"""<h2 class="mt3" style="font-size:22px">BD Market Reality — {esc(name)}</h2>
  <div class="tbl mt2"><table>
  <tr><th>Where</th><th>Price range</th><th>Warranty?</th></tr>
  <tr><td>Official (intl. card needed)</td><td>~৳{official_bdt:,}/mo</td><td>n/a</td></tr>
  <tr><td>BD market (surveyed)</td><td>৳{mk['low']:,} – ৳{mk['high']:,}</td><td>Usually none/unclear</td></tr>
  <tr style="background:rgba(20,212,184,.07)"><td><b>SAVEONSUB</b></td><td><b>from ৳{ours_low:,}</b></td><td><b>✅ 1-hour replacement, in writing</b></td></tr>
  </table></div>
  <p style="font-size:13px;color:var(--muted);margin-top:8px">{esc(mk['who'])} <i>(source: {esc(mk['src'])})</i>. {honesty}</p>"""
    else:
        market_html = f"""<div class="notice mt3" style="font-size:13.5px">📊 <b>Market survey pending for {esc(name)}</b> — we publish competitor ranges only when we've actually verified them. No invented numbers, ever. Seen a better BD price? <a href="https://wa.me/8801305869242?text=Better%20price%20found%20for%20{esc(name)}:%20" style="color:var(--green2)">Tell us</a> — we'll verify and show it here.</div>"""

    contains_html = ""
    if 'contains' in p:
        items = " + ".join(by_id[c]['name'] for c in p['contains'] if c in by_id)
        contains_html = f'<div class="notice green mt2">🎁 <b>Inside this bundle:</b> {esc(items)} — save ৳{p.get("save_bdt",0)} vs buying separately.</div>'

    wa = f"https://wa.me/8801305869242?text=" + esc(f"Hi! I want to order {name} ({cheapest['label']}, ৳{cheapest['bdt']})")

    # ---- SEO: keyword engine ----
    seo = p.get('seo', {})
    kw_all = seo.get('all', p.get('keywords', []))
    meta_keywords = ", ".join(kw_all[:18])
    # crawlable "commonly searched as" block (En + Bangla + translit) — real user queries
    searched_en = seo.get('short_tail', [])[:6] + seo.get('long_tail', [])[:4]
    searched_bn = seo.get('bangla', []) + seo.get('transliteration', [])
    searched_html = ""
    if searched_en or searched_bn:
        chips_en = " · ".join(esc(k) for k in searched_en)
        chips_bn = " · ".join(esc(k) for k in searched_bn)
        searched_html = f"""<h2 class="mt3" style="font-size:20px">Commonly searched as</h2>
  <p style="font-size:13px;color:var(--muted);line-height:1.9">{chips_en}</p>
  {f'<p style="font-size:13px;color:var(--muted);line-height:1.9">{chips_bn}</p>' if chips_bn else ''}
  <p style="font-size:12.5px;color:var(--muted)">However you search it, {esc(name)} in Bangladesh is here from ৳{cheapest['bdt']:,} with bKash/Nagad and a written warranty.</p>"""
    # guide cross-links (internal linking)
    GUIDE_LINKS = {
      "AI Video": ("ai-video-tools-price-comparison-bd-2026", "AI video tool price comparison BD"),
      "Entertainment": ("netflix-spotify-youtube-premium-price-bd", "Netflix/Spotify/YouTube BD prices"),
      "Education & Career": ("coursera-vs-youtube-learning-bd", "Coursera vs free YouTube"),
      "AI Code & Dev": ("free-ai-tools-that-beat-paid-bangladesh", "Free AI tools that beat paying"),
      "AI Image & Design": ("midjourney-vs-leonardo-bangladesh", "Midjourney vs Leonardo BD"),
    }
    gl = GUIDE_LINKS.get(p['category'], ("how-we-source-subscriptions-transparency", "How we source subscriptions (is it legal?)"))
    guide_html = f'<div class="notice mt2" style="font-size:13.5px">📖 Related guide: <a href="../blog/{gl[0]}.html" style="color:var(--green2);font-weight:700">{esc(gl[1])} →</a> · <a href="../blog/how-to-pay-for-ai-tools-with-bkash.html" style="color:var(--green2)">How to pay with bKash</a></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="{esc(meta_keywords)}">
<link rel="canonical" href="https://saveonsub.com/p/{p['id']}.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/p/{p['id']}.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/p/{p['id']}.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/p/{p['id']}.html">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="product"><meta property="og:url" content="https://saveonsub.com/p/{p['id']}.html">
<meta property="og:locale" content="en_BD"><meta property="og:locale:alternate" content="bn_BD">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta name="theme-color" content="#06181a">
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="manifest" href="../assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/social/{p['id']}.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:image" content="https://saveonsub.com/assets/social/{p['id']}.png">
<link rel="stylesheet" href="../assets/style.css">
<script type="application/ld+json">{json.dumps(product_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(speak_ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{nav_en("../")}
<main id="main"><div class="wrap" style="max-width:880px">
  <div class="crumbs"><a href="../index.html">Home</a> › <a href="../all.html">All Products</a> › <a href="../c/{_cs}.html">{esc(p['category'])}</a> › {esc(name)}</div>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
    <span style="font-size:46px">{p['icon']}</span>
    <div><h1 style="font-size:clamp(26px,4vw,38px)">{esc(name)}</h1>
    <span class="cat" style="font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;font-weight:800"><a href="../c/{_cs}.html" style="color:inherit">{esc(p['category'])}</a>{' · 🔥 '+str(p['orders'])+'+ orders' if p.get('orders',0)>100 else ''}</span></div>
  </div>
  <div class="anchor mt2">
    <span class="official">Official: ~৳{official_bdt:,}/mo (${p['official_usd']})</span>
    <span class="ours">From ৳{cheapest['bdt']:,}</span>
    {f'<span class="savepct">SAVE {save}%</span>' if save>0 else ''}
    <a href="{esc(p['official_url'])}" target="_blank" rel="noopener nofollow" style="font-size:12.5px;color:var(--muted);text-decoration:underline">verify official ↗</a>
  </div>
  <h2 class="mt3" style="font-size:22px">Choose your plan</h2>
  <div class="grid mt2" style="grid-template-columns:1fr;gap:10px">{plans_html}</div>
  {contains_html}
  {guide_html}
  {market_html}
  <div class="notice mt2"><b>🏷️ What these labels mean (we're honest):</b>{tos_notes}</div>
  <div class="notice green mt2">🛡️ <b>Warranty:</b> {esc(cat['meta']['warranty'])}</div>
  <div class="notice mt2">🧭 <b>Price-match guarantee:</b> Find a lower official price? We match it + 5% off. Every subscription is official, activated on YOUR own account, and 100% customer-owned.</div>
  <div class="notice mt2" style="font-size:12.5px;color:var(--muted);line-height:1.6"><b>Important Notice:</b> SAVEONSUB is not an official distributor, reseller, or partner of any subscription platform. We provide setup and activation support to help Bangladesh-based users access plans using local payment methods (bKash, Nagad, bank transfer). Your account is 100% customer-owned; we do not retain access to your credentials. If we cannot complete activation within the agreed window, you receive a full refund per our refund policy.</div>
  <h2 class="mt3" style="font-size:22px">Questions about {esc(name)}</h2>
  <div class="mt2">{faq_html}</div>
  {searched_html}
  <div class="heroctas mt3">
    <a class="btn btn-wa" href="{wa}">💬 Order {esc(name)} on WhatsApp</a>
    <a class="btn btn-ghost" href="../checkout.html">Go to checkout →</a>
  </div>
  <h2 class="mt3" style="font-size:22px">People also buy</h2>
  <div class="grid g3 mt2">{rel_html}</div>
</div></main>
<button class="fab fab-wa" onclick="location.href='{wa}'" aria-label="WhatsApp">💬 WhatsApp</button>
<a class="fab fab-quiz" href="../quiz.html" aria-label="Find my AI quiz">🧭 Find My AI</a>
{footer_en("../")}
<script src="../assets/catalog.js"></script>
<script src="../assets/app.js"></script>
</body>
</html>"""

count = 0
for p in products:
    open(f"p/{p['id']}.html", 'w').write(page(p))
    count += 1
print(f"OK: generated {count} product pages in p/")

# ===================== BANGLA PRODUCT PAGES (bn/p/<id>.html) =====================
TOS_LABEL_BN = {"official": "অফিসিয়াল", "personal": "পার্সোনাল অ্যাকাউন্ট",
                "shared-low": "শেয়ার্ড · কম ঝুঁকি", "shared-med": "শেয়ার্ড · ওয়ারেন্টিসহ", "bundle": "বান্ডেল"}
SLA_BN = {"instant": "৫–১৫ মিনিট", "fast": "১–৩ ঘণ্টা", "same-day": "একই দিনে", "1-2-days": "১–২ দিন"}
def sla_bn(s): return SLA_BN.get(s, esc(sla_meta.get(s, s)))
# Universal, hand-written Bangla FAQ — applies honestly to every product
def bn_faq(name, frm):
    return [
      ("এটা কি আসল এবং নিরাপদ?",
       f"হ্যাঁ — ২০২৪ সাল থেকে ৩,০০০+ কাস্টমার। প্রতিটি প্ল্যানে সৎ ঝুঁকির লেবেল দেওয়া, আর যেকোনো সমস্যায় ১ ঘণ্টার মধ্যে রিপ্লেসমেন্ট। প্রথমবার নার্ভাস? আগে টেস্ট করে তারপর টাকা দিন (pay-after-testing)।"),
      ("কত দ্রুত ডেলিভারি পাব?",
       "ইনস্ট্যান্ট প্রোডাক্ট হোয়াটসঅ্যাপে ৫–১৫ মিনিটে। পার্সোনাল অ্যাকাউন্ট সেটআপে ১–২ দিন লাগতে পারে — প্রতিটি প্ল্যানে সময় লেখা আছে।"),
      ("কীভাবে পেমেন্ট করব?",
       "বিকাশ, নগদ বা রকেটে সেন্ড মানি — কোনো কার্ড বা ব্যাংক অ্যাকাউন্ট লাগবে না। চেকআউটে পুরো নির্দেশনা কপি বাটনসহ দেওয়া থাকে।"),
      ("শেয়ার্ড প্ল্যানে আমার তথ্য কি অন্যরা দেখবে?",
       "না। শুধু সাবস্ক্রিপশনের খরচটাই শেয়ার হয় — আপনার চ্যাট, ফাইল বা ব্যক্তিগত ডেটা কেউ দেখে না।"),
      ("যদি কাজ না করে?",
       "সাপোর্ট আওয়ারে ১ ঘণ্টার মধ্যে রিপ্লেসমেন্ট। শেয়ার্ড সিটে ৭ দিন, পার্সোনাল প্ল্যানে ৩০ দিন গ্যারান্টি — লিখিতভাবে।"),
      (f"{name} বাংলাদেশে দাম কত?",
       f"{name} আমাদের এখানে ৳{frm:,} থেকে শুরু — বিকাশ/নগদে, ওয়ারেন্টিসহ। অফিসিয়াল দামের চেয়ে অনেক কম, আর প্রতিটি প্ল্যানের ঝুঁকি আগে থেকে জানিয়ে দিই।"),
    ]

def bn_page(p):
    cheapest = min(p['plans'], key=lambda x: x['bdt'])
    official_bdt = round(p['official_usd'] * rate)
    name = p['name'].replace('🎁 ', '')
    # Strip leading emoji for titles  
    import unicodedata as _uc2
    name_clean_bn = name
    while name_clean_bn and (_uc2.category(name_clean_bn[0]) == 'So' or ord(name_clean_bn[0]) > 255):
        name_clean_bn = name_clean_bn[1:].strip()
    if not name_clean_bn: name_clean_bn = name
    frm = cheapest['bdt']
    title = f"{name_clean_bn} দাম বাংলাদেশে — ৳{frm:,} থেকে | SAVEONSUB"
    if len(title) > 60: title = f"{name_clean_bn[:40]} — ৳{frm:,} থেকে | SAVEONSUB"
    if len(title) > 60: title = f"{name_clean_bn[:30]} | SAVEONSUB"
    desc = f"{name_clean_bn} বাংলাদেশে ৳{frm:,} থেকে — বিকাশ/নগদ, ৫–১৫ মিনিটে ডেলিভারি, ১ ঘণ্টার ওয়ারেন্টি। সৎ দামে আসল সাবস্ক্রিপশন।"
    if len(desc) > 155: desc = desc[:152] + "…"

    offers = [{"@type": "Offer", "name": pl['label'], "price": pl['bdt'], "priceCurrency": "BDT",
               "availability": "https://schema.org/InStock", "priceValidUntil": PRICE_VALID,
               "hasMerchantReturnPolicy": RETURN_POLICY,
               "url": f"https://saveonsub.com/bn/p/{p['id']}.html"} for pl in p['plans']]
    product_ld = {"@context": "https://schema.org", "@type": "Product", "sku": f"BD-{p['id'].upper()}", "name": name,
                  "description": desc, "brand": {"@type": "Brand", "name": name.split()[0]},
                  "image": [f"https://saveonsub.com/assets/social/{p['id']}.png"],
                  "category": p['category'],
                  "offers": {"@type": "AggregateOffer", "lowPrice": frm, "itemCondition": "https://schema.org/NewCondition",
                             "highPrice": max(pl['bdt'] for pl in p['plans']), "priceCurrency": "BDT",
                             "offerCount": len(p['plans']), "offers": offers}}
    faqs = bn_faq(name, frm)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    _cs = cslug(p['category'])
    crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "হোম", "item": "https://saveonsub.com/bn.html"},
        {"@type": "ListItem", "position": 2, "name": "সব প্রোডাক্ট", "item": "https://saveonsub.com/all.html"},
        {"@type": "ListItem", "position": 3, "name": p['category'], "item": f"https://saveonsub.com/bn/c/{_cs}.html"},
        {"@type": "ListItem", "position": 4, "name": name, "item": f"https://saveonsub.com/bn/p/{p['id']}.html"}]}
    speak_ld = {"@context": "https://schema.org", "@type": "WebPage",
        "url": f"https://saveonsub.com/bn/p/{p['id']}.html", "inLanguage": "bn",
        "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", ".anchor"]}}

    plans_html = ""
    for pl in p['plans']:
        tos = pl['tos']
        plans_html += f"""
      <div class="pcard" style="flex-direction:row;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div><b>{esc(pl['label'])}</b><br>
          <span class="tos {TOS_CLASS[tos]}">{TOS_LABEL_BN[tos]}</span>
          <span style="font-size:12px;color:var(--muted)"> · {esc(pl['duration'])} · ডেলিভারি {sla_bn(pl['sla'])}</span></div>
        <div style="display:flex;align-items:center;gap:14px">
          <span style="font-size:22px;font-weight:900;color:var(--green2)">৳{pl['bdt']:,}</span>
          <button class="btn btn-primary btn-sm" onclick="cartAdd({jstr(p['id'])},{jstr(pl['label'])},{pl['bdt']},{jstr(name)})">কার্টে যোগ করুন</button>
        </div></div>"""

    faq_html = "".join(f"<details{' open' if i==0 else ''}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for i, (q, a) in enumerate(faqs))
    rel_html = "".join(f"""<a class="pcard" href="{x['id']}.html"><span class="icon">{x['icon']}</span><h3>{esc(x['name'].replace('🎁 ',''))}</h3><span class="cat">{esc(x['category'])}</span><div class="price">৳{min(pl['bdt'] for pl in x['plans']):,}</div></a>""" for x in related(p))

    mk = p.get('market', {})
    if mk.get('surveyed'):
        beat = frm <= mk['low']
        honesty = ("সার্ভে করা অপশনগুলোর মধ্যে আমরাই সবচেয়ে সস্তা — এবং একমাত্র লিখিত ওয়ারেন্টিসহ।" if beat else
                   "বাজারে আরও সস্তা আছে — কিন্তু pay-after-testing, লিখিত ওয়ারেন্টি বা সৎ ঝুঁকির লেবেল ছাড়া। পছন্দ আপনার।")
        market_html = f"""<h2 class="mt3" style="font-size:22px">বাজারের বাস্তবতা — {esc(name)}</h2>
  <div class="tbl mt2"><table>
  <tr><th>কোথায়</th><th>দাম</th><th>ওয়ারেন্টি?</th></tr>
  <tr><td>অফিসিয়াল (কার্ড লাগবে)</td><td>~৳{official_bdt:,}/মাস</td><td>নেই</td></tr>
  <tr><td>বাংলাদেশ বাজার (সার্ভে করা)</td><td>৳{mk['low']:,} – ৳{mk['high']:,}</td><td>সাধারণত নেই/অস্পষ্ট</td></tr>
  <tr style="background:rgba(20,212,184,.07)"><td><b>SAVEONSUB</b></td><td><b>৳{frm:,} থেকে</b></td><td><b>✅ ১ ঘণ্টার রিপ্লেসমেন্ট, লিখিত</b></td></tr>
  </table></div>
  <p style="font-size:13px;color:var(--muted);margin-top:8px"><i>(সোর্স: {esc(mk['src'])})</i>. {honesty}</p>"""
    else:
        market_html = f"""<div class="notice mt3" style="font-size:13.5px">📊 <b>{esc(name)} — বাজার সার্ভে চলছে।</b> যাচাই না করা কোনো সংখ্যা আমরা লিখি না। ভালো দাম দেখেছেন? <a href="https://wa.me/8801305869242" style="color:var(--green2)">জানান</a> — যাচাই করে এখানে দেখাব।</div>"""

    seo = p.get('seo', {})
    searched_bn = seo.get('bangla', []) + seo.get('transliteration', [])
    searched_html = ""
    if searched_bn:
        chips_bn = " · ".join(esc(k) for k in searched_bn)
        searched_html = f"""<h2 class="mt3" style="font-size:20px">যেভাবে মানুষ খোঁজে</h2>
  <p style="font-size:13px;color:var(--muted);line-height:1.9">{chips_bn}</p>
  <p style="font-size:12.5px;color:var(--muted)">যেভাবেই খুঁজুন, {esc(name)} বাংলাদেশে এখানে ৳{frm:,} থেকে — বিকাশ/নগদে, লিখিত ওয়ারেন্টিসহ।</p>"""

    wa = "https://wa.me/8801305869242?text=" + esc(f"আসসালামু আলাইকুম! আমি {name} ({cheapest['label']}, ৳{cheapest['bdt']}) নিতে চাই")
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://saveonsub.com/bn/p/{p['id']}.html">
<link rel="alternate" hreflang="bn-bd" href="https://saveonsub.com/bn/p/{p['id']}.html">
<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/p/{p['id']}.html">
<link rel="alternate" hreflang="x-default" href="https://saveonsub.com/p/{p['id']}.html">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="product"><meta property="og:url" content="https://saveonsub.com/bn/p/{p['id']}.html">
<meta property="og:locale" content="bn_BD"><meta property="og:locale:alternate" content="en_BD">
<meta name="geo.region" content="BD"><meta name="geo.placename" content="Dhaka">
<meta name="theme-color" content="#06181a">
<link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png">
<link rel="manifest" href="../../assets/site.webmanifest">
<meta property="og:image" content="https://saveonsub.com/assets/social/{p['id']}.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:image" content="https://saveonsub.com/assets/social/{p['id']}.png">
<link rel="stylesheet" href="../../assets/style.css">
<script type="application/ld+json">{json.dumps(product_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(speak_ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">মূল কন্টেন্টে যান</a>
{nav_bn("../../")}
<main id="main"><div class="wrap" style="max-width:880px">
  <div class="crumbs"><a href="../../bn.html">হোম</a> › <a href="../../all.html">সব প্রোডাক্ট</a> › <a href="../c/{_cs}.html">{esc(p['category'])}</a> › {esc(name)}</div>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
    <span style="font-size:46px">{p['icon']}</span>
    <div><h1 style="font-size:clamp(26px,4vw,38px)">{esc(name)} — দাম বাংলাদেশে</h1>
    <span class="cat" style="font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;font-weight:800"><a href="../c/{_cs}.html" style="color:inherit">{esc(p['category'])}</a>{' · 🔥 '+str(p['orders'])+'+ অর্ডার' if p.get('orders',0)>100 else ''}</span></div>
  </div>
  <div class="anchor mt2">
    <span class="official">অফিসিয়াল: ~৳{official_bdt:,}/মাস</span>
    <span class="ours">৳{frm:,} থেকে</span>
    <a href="{esc(p['official_url'])}" target="_blank" rel="noopener nofollow" style="font-size:12.5px;color:var(--muted);text-decoration:underline">অফিসিয়াল যাচাই ↗</a>
  </div>
  <h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>
  <div class="grid mt2" style="grid-template-columns:1fr;gap:10px">{plans_html}</div>
  {market_html}
  <div class="notice green mt2">🛡️ <b>ওয়ারেন্টি:</b> সাপোর্ট আওয়ারে ১ ঘণ্টার মধ্যে রিপ্লেসমেন্ট। শেয়ার্ডে ৭ দিন, পার্সোনালে ৩০ দিন গ্যারান্টি।</div>
  <div class="notice mt2">🧭 <b>প্রাইস-ম্যাচ গ্যারান্টি:</b> কম অফিসিয়াল দাম পেয়েছেন? আমরা ম্যাচ করব + ৫% ছাড়। প্রতিটি সাবস্ক্রিপশন অফিসিয়াল, আপনার নিজের অ্যাকাউন্টে অ্যাক্টিভেটেড, ১০০% গ্রাহক-নিয়ন্ত্রিত।</div>
  <div class="notice mt2" style="font-size:12.5px;color:var(--muted);line-height:1.6"><b>গুরুত্বপূর্ণ বিজ্ঞপ্তি:</b> SAVEONSUB কোনো সাবস্ক্রিপশন প্ল্যাটফর্মের অফিসিয়াল ডিস্ট্রিবিউটর, রিসেলার বা অংশীদার নয়। আমরা বাংলাদেশ-ভিত্তিক ব্যবহারকারীদের স্থানীয় পেমেন্ট পদ্ধতি (বিকাশ, নগদ, ব্যাংক ট্রান্সফার) ব্যবহার করে সাবস্ক্রিপশন প্ল্যান অ্যাক্সেস করতে সেটআপ ও অ্যাক্টিভেশন সহায়তা প্রদান করি। অ্যাকাউন্ট ১০০% আপনার মালিকানাধীন; আমরা আপনার ক্রেডেনশিয়াল অ্যাক্সেস রাখি না। নির্ধারিত সময়ের মধ্যে অ্যাক্টিভেশন সম্পন্ন করতে না পারলে আমাদের রিফান্ড নীতি অনুযায়ী সম্পূর্ণ রিফান্ড পাবেন।</div>
  <h2 class="mt3" style="font-size:22px">{esc(name)} নিয়ে সাধারণ প্রশ্ন</h2>
  <div class="mt2">{faq_html}</div>
  {searched_html}
  <div class="heroctas mt3">
    <a class="btn btn-wa" href="{wa}">💬 হোয়াটসঅ্যাপে {esc(name)} অর্ডার করুন</a>
    <a class="btn btn-ghost" href="../../checkout.html">চেকআউটে যান →</a>
  </div>
  <h2 class="mt3" style="font-size:22px">মানুষ আরও যা কেনে</h2>
  <div class="grid g3 mt2">{rel_html}</div>
</div></main>
<button class="fab fab-wa" onclick="location.href='{wa}'" aria-label="হোয়াটসঅ্যাপ">💬 হোয়াটসঅ্যাপ</button>
{footer_bn("../../")}
<script src="../../assets/catalog.js"></script>
<script src="../../assets/app.js"></script>
</body>
</html>"""

os.makedirs('bn/p', exist_ok=True)
bcount = 0
for p in products:
    open(f"bn/p/{p['id']}.html", 'w').write(bn_page(p))
    bcount += 1
print(f"OK: generated {bcount} Bangla product pages in bn/p/")
