#!/usr/bin/env python3
"""Deterministic SaveOnSub Brand v2 migration for the staging branch.
Updates committed HTML and source templates together. Safe to run repeatedly.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
WA = "https://wa.me/8801305869242"
SAFE_EN = "Save more on premium AI and digital subscriptions with clear access options and real human WhatsApp support in Bangladesh."
SAFE_BN = "প্রিমিয়াম AI ও ডিজিটাল সাবস্ক্রিপশনে স্মার্ট সেভিংস, পরিষ্কার অ্যাক্সেস তথ্য এবং বাংলাদেশে সরাসরি হিউম্যান WhatsApp সাপোর্ট।"
WA_CTA = f'<a href="{WA}?text=Hi%20SaveOnSub%2C%20I%20need%20help%20choosing%20a%20subscription." class="btn btn-wa">💬 Get Human Support</a>'


def migrate_html(path: Path):
    s = path.read_text(encoding="utf-8", errors="replace")
    old = s

    # Legacy typed logo -> approved artwork, while preserving page destination.
    s = re.sub(
        r'<a class="logo" href="([^"]+)">SAVE<em>ON</em>SUB</a>',
        lambda m: f'<a class="logo brand-lockup" href="{m.group(1)}"><img src="{_asset_prefix(s)}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>',
        s,
    )
    rel = _asset_prefix(s)
    s = s.replace(
        '<span class="logo">SAVE<em>ON</em>SUB</span>',
        f'<a class="logo brand-lockup footer-brand" href="{rel}index.html"><img src="{rel}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>',
    )

    s = s.replace("Bangladesh's Subscription Operating System — official, customer-owned subscriptions paid in BDT — Dhaka, Bangladesh.", SAFE_EN)
    s = s.replace("বাংলাদেশের সাবস্ক্রিপশন অপারেটিং সিস্টেম — অফিসিয়াল, গ্রাহক-নিয়ন্ত্রিত সাবস্ক্রিপশন — ঢাকা, বাংলাদেশ।", SAFE_BN)

    # English homepage brand migration.
    if path == ROOT / "index.html":
        s = re.sub(r'<title>.*?</title>', '<title>SaveOnSub — Save More on Premium AI &amp; Digital Subscriptions</title>', s, count=1)
        s = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Compare premium AI and digital subscriptions, find smarter-value options, and get real human WhatsApp support in Bangladesh.">', s, count=1)
        s = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="SaveOnSub — Save More. Subscribe Smarter.">', s, count=1)
        s = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="Premium AI and digital subscription savings with clear access information and real human WhatsApp support in Bangladesh.">', s, count=1)

        s = s.replace("🇧🇩 BANGLADESH'S HONEST SUBSCRIPTION STORE", "🇧🇩 AI-FIRST SUBSCRIPTION SAVINGS FOR BANGLADESH")
        s = s.replace("Premium subscriptions at <span class=\"grad-text\">prices that make sense</span> in Bangladesh.", "Save more on premium subscriptions. <span class=\"grad-text\">Subscribe smarter.</span>")
        s = s.replace("ChatGPT, Claude, Netflix, Canva, Midjourney and 58+ more — authentic, delivered to WhatsApp in 5–15 minutes, paid with bKash. Every plan honestly labeled. Every seat covered by warranty.", "Compare premium AI and digital subscriptions, understand your access options, find smarter-value choices, and talk directly with our human team on WhatsApp before or after you buy.")

        # 3S trust bar.
        s = s.replace('<span>✅ <b>100% official, customer-owned</b> on your own account</span>', '<span>💰 <b>Savings</b> — smarter subscription value</span>')
        s = s.replace('<span>⚡ <b>5–15 min</b> delivery</span>', '<span>🛡️ <b>Security</b> — clear access information</span>')
        s = s.replace('<span>🛡️ <b>1-hour</b> replacement warranty</span>', '<span>💬 <b>Support</b> — real humans on WhatsApp</span>')
        s = s.replace('<span>💳 bKash · Nagad · Rocket</span>', '<span>📱 <b>WhatsApp</b> +880 1305 869242</span>')

        # Make CTA idempotent and remove duplicate copies from prior migrations.
        s = re.sub(r'(?:\s*<a href="https://wa\.me/8801305869242\?text=[^"]+" class="btn btn-wa">💬 Get Human Support</a>)+', '\n      ' + WA_CTA, s)
        if WA_CTA not in s:
            s = s.replace('<a href="all.html" class="btn btn-primary">Browse Subscriptions →</a>', WA_CTA + '\n      <a href="all.html" class="btn btn-primary">Browse Subscriptions →</a>', 1)

        # Replace unsupported hero proof with brand habit; editorial "Featured" is not a ranking claim.
        s = re.sub(r'\s*<div class="anchor">.*?</div>\s*<div class="ticker mt2">.*?</div>', '\n    <div class="ticker mt2"><span class="dotp"></span><span>Before You Subscribe, Check SaveOnSub.</span></div>', s, count=1, flags=re.S)
        s = re.sub(r'<span class="cat">#\d+ Bestseller</span>', '<span class="cat">Featured</span>', s)
        s = s.replace('<span class="cat">Popular choice</span>', '<span class="cat">Featured</span>')

        # Structured data must match current public authority and not overstate proof.
        s = s.replace("Bangladesh's honest premium subscription store — authentic subscriptions at affordable BD prices, paid with bKash/Nagad/Rocket.", "AI-first subscription savings and support platform for Bangladesh, with clear access information and real human WhatsApp support.")
        s = s.replace('"slogan":"সাবস্ক্রিপশনের সৎ দোকান"', '"slogan":"Save More. Subscribe Smarter."')
        s = re.sub(r',"parentOrganization":\{"@type":"Organization","name":"SYSmoAI".*?\},"areaServed"', ',"areaServed"', s, count=1)
        s = s.replace('"Yes — Bangladesh\'s trusted subscription OS, replacement within 1 hour, and honest risk labels on every plan. Nervous? Use our pay-after-testing option on your first order."', '"Each plan should clearly state its access type and applicable support terms. If you are unsure, contact our human team on WhatsApp before paying."')
        s = s.replace('"5–15 minutes on WhatsApp for instant products, up to 1–2 days for managed personal accounts. The SLA is shown on every product."', '"Activation time varies by product and access method. Confirm the current expected activation time with our human team before payment."')
        s = s.replace('"No. ChatGPT keeps every user\'s conversations private. Only the subscription cost is shared — never your chat history."', '"Privacy and account-control implications depend on the access method. Review the access label and choose a customer-owned option when privacy or business use is important."')
        s = s.replace('"Replacement within 1 hour during support hours. Shared seats carry a 7-day guarantee; personal plans 30 days."', '"Support and warranty terms vary by plan. The applicable terms should be shown before payment, and our WhatsApp team can clarify them."')

    # Bangla homepage: bring the visible brand story into the same 3S/WhatsApp system.
    if path == ROOT / "bn.html":
        s = s.replace("🇧🇩 বাংলাদেশের সৎ সাবস্ক্রিপশন দোকান", "🇧🇩 বাংলাদেশের AI-FIRST SUBSCRIPTION SAVINGS PLATFORM")
        s = s.replace('প্রিমিয়াম সাবস্ক্রিপশন — <span class="grad-text">বাংলাদেশি দামে</span>, বিকাশে।', 'প্রিমিয়াম সাবস্ক্রিপশনে <span class="grad-text">আরও স্মার্ট সেভিংস</span> করুন।')
        s = s.replace("ChatGPT, Netflix, Canva, Midjourney সহ ৫০+ টুল — অথেনটিক, ৫–১৫ মিনিটে WhatsApp-এ ডেলিভারি, বিকাশে পেমেন্ট। প্রতিটা প্ল্যানে সৎ লেবেল, প্রতিটা সিটে ওয়ারেন্টি।", "AI ও অন্যান্য প্রিমিয়াম সাবস্ক্রিপশন তুলনা করুন, অ্যাক্সেস পদ্ধতি পরিষ্কারভাবে বুঝুন এবং কেনার আগে বা পরে সরাসরি আমাদের হিউম্যান WhatsApp টিমের সহায়তা নিন।")
        s = re.sub(r'\s*<div class="anchor">.*?</div>\s*<div class="ticker mt2">.*?</div>', '\n    <div class="ticker mt2"><span class="dotp"></span><span>সাবস্ক্রাইব করার আগে SaveOnSub চেক করুন।</span></div>', s, count=1, flags=re.S)
        s = re.sub(r'<span class="cat">#\d+ বেস্টসেলার</span>', '<span class="cat">ফিচার্ড</span>', s)
        if 'হিউম্যান WhatsApp সাপোর্ট' not in s.split('</header>',1)[0]:
            s = s.replace('<div class="heroctas">', f'<div class="heroctas"><a href="{WA}?text=Hi%20SaveOnSub" class="btn btn-wa">💬 হিউম্যান WhatsApp সাপোর্ট</a>', 1)

    if s != old:
        path.write_text(s, encoding="utf-8")
        print("updated", path.relative_to(ROOT))


def _asset_prefix(s: str) -> str:
    m = re.search(r'href="([^\"]*)assets/style\.css"', s)
    return m.group(1) if m else ""


def migrate_templates():
    p = ROOT / "templates.py"
    s = p.read_text(encoding="utf-8")
    old = s
    s = s.replace('<a class="logo" href="{rel}index.html">SAVE<em>ON</em>SUB</a>', '<a class="logo brand-lockup" href="{rel}index.html"><img src="{rel}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>')
    s = s.replace('<a class="logo" href="{rel}bn.html">SAVE<em>ON</em>SUB</a>', '<a class="logo brand-lockup" href="{rel}bn.html"><img src="{rel}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>')
    s = s.replace('<span class="logo">SAVE<em>ON</em>SUB</span>', '<a class="logo brand-lockup footer-brand" href="{rel}index.html"><img src="{rel}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>')
    s = s.replace("Bangladesh's Subscription Operating System — official, customer-owned subscriptions paid in BDT — Dhaka, Bangladesh.", SAFE_EN)
    s = s.replace("বাংলাদেশের সাবস্ক্রিপশন অপারেটিং সিস্টেম — অফিসিয়াল, গ্রাহক-নিয়ন্ত্রিত সাবস্ক্রিপশন — ঢাকা, বাংলাদেশ।", SAFE_BN)
    if s != old:
        p.write_text(s, encoding="utf-8")
        print("updated templates.py")


def migrate_css():
    p = ROOT / "assets/style.css"
    s = p.read_text(encoding="utf-8")
    marker = "/* SAVEONSUB BRAND V2 LOCK — 2026-08-19 */"
    if marker not in s:
        s += f'''\n\n{marker}\n.brand-lockup {{ display:inline-flex; align-items:center; flex:0 0 auto; background:#fff; border-radius:10px; padding:4px 7px; line-height:0; overflow:hidden; }}\n.brand-logo {{ display:block; width:190px; height:auto; max-height:46px; object-fit:contain; }}\n.footer-brand {{ margin-bottom:8px; }}\n@media (max-width:600px) {{ .brand-logo {{ width:155px; max-height:40px; }} .brand-lockup {{ padding:3px 5px; }} }}\n:root {{ --brand-navy:#082035; --brand-teal:#008f82; }}\n'''
        p.write_text(s, encoding="utf-8")
        print("updated assets/style.css")


def protect_master_assets():
    p = ROOT / "build_assets.py"
    s = p.read_text(encoding="utf-8")
    old = s
    start = s.find("# ---------- favicon.svg — the Honest Price Tag mark ----------")
    end = s.find("# ---------- apple-touch-icon.png ----------")
    if start != -1 and end != -1 and end > start:
        s = s[:start] + "# ---------- LOCKED BRAND ASSETS ----------\n# logo.svg and favicon.svg are CEO-approved master-derived assets; never regenerate them here.\n\n" + s[end:]
    if s != old:
        p.write_text(s, encoding="utf-8")
        print("updated build_assets.py")


def main():
    migrate_templates()
    migrate_css()
    protect_master_assets()
    for p in ROOT.rglob("*.html"):
        if any(part in {".git", ".next", ".astro", "node_modules", "_site"} for part in p.parts):
            continue
        migrate_html(p)
    print("Brand v2 migration complete")


if __name__ == "__main__":
    main()
