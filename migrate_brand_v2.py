#!/usr/bin/env python3
"""One-time SaveOnSub Brand v2 migration.

Runs only on the brand-v2-2026-08-19 branch. It updates committed static pages and
source templates together so the approved brand cannot drift on the next rebuild.
It deliberately does NOT invent prices, order counts, reviews, delivery SLAs or
warranty promises.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

SAFE_EN = "Save more on premium AI and digital subscriptions with clear access options and real human WhatsApp support in Bangladesh."
SAFE_BN = "প্রিমিয়াম AI ও ডিজিটাল সাবস্ক্রিপশনে স্মার্ট সেভিংস, পরিষ্কার অ্যাক্সেস তথ্য এবং বাংলাদেশে সরাসরি হিউম্যান WhatsApp সাপোর্ট।"
WA = "https://wa.me/8801305869242"


def write_if_changed(path: Path, text: str):
    old = path.read_text(encoding="utf-8")
    if old != text:
        path.write_text(text, encoding="utf-8")
        print("updated", path.relative_to(ROOT))


def migrate_html(path: Path):
    s = path.read_text(encoding="utf-8", errors="replace")
    old = s

    # Replace legacy typed wordmark in nav with the approved master artwork.
    # Capture the relative prefix from the existing href so nested pages work.
    s = re.sub(
        r'<a class="logo" href="([^"]*?)(?:index|bn)\.html">SAVE<em>ON</em>SUB</a>',
        lambda m: f'<a class="logo brand-lockup" href="{m.group(1)}index.html"><img src="{m.group(1)}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>',
        s,
    )
    # Footer typed wordmark -> approved artwork; infer nesting from stylesheet path.
    rel = ""
    m = re.search(r'href="([^\"]*)assets/style\.css"', s)
    if m:
        rel = m.group(1)
    s = s.replace(
        '<span class="logo">SAVE<em>ON</em>SUB</span>',
        f'<a class="logo brand-lockup footer-brand" href="{rel}index.html"><img src="{rel}assets/logo.svg" alt="SaveOnSub" class="brand-logo"></a>',
    )

    # Retire stale universal claims from shared static output.
    s = s.replace("Bangladesh's Subscription Operating System — official, customer-owned subscriptions paid in BDT — Dhaka, Bangladesh.", SAFE_EN)
    s = s.replace("বাংলাদেশের সাবস্ক্রিপশন অপারেটিং সিস্টেম — অফিসিয়াল, গ্রাহক-নিয়ন্ত্রিত সাবস্ক্রিপশন — ঢাকা, বাংলাদেশ।", SAFE_BN)

    # Homepage/public recurring legacy claim language. Exact-string replacements
    # are intentionally conservative: anything not matched is left for audit.
    s = s.replace("🇧🇩 BANGLADESH'S HONEST SUBSCRIPTION STORE", "🇧🇩 AI-FIRST SUBSCRIPTION SAVINGS FOR BANGLADESH")
    s = s.replace("Premium subscriptions at <span class=\"grad-text\">prices that make sense</span> in Bangladesh.", "Save more on premium subscriptions. <span class=\"grad-text\">Subscribe smarter.</span>")
    s = s.replace(
        "ChatGPT, Claude, Netflix, Canva, Midjourney and 58+ more — authentic, delivered to WhatsApp in 5–15 minutes, paid with bKash. Every plan honestly labeled. Every seat covered by warranty.",
        "Compare premium AI and digital subscriptions, understand your access options, find smarter-value choices, and talk directly with our human team on WhatsApp before or after you buy.",
    )

    # Risky homepage trustbar -> evidence-safe 3S system.
    s = s.replace('<span>✅ <b>100% official, customer-owned</b> on your own account</span>', '<span>💰 <b>Savings</b> — smarter subscription value</span>')
    s = s.replace('<span>⚡ <b>5–15 min</b> delivery</span>', '<span>🛡️ <b>Security</b> — clear access information</span>')
    s = s.replace('<span>🛡️ <b>1-hour</b> replacement warranty</span>', '<span>💬 <b>Support</b> — real humans on WhatsApp</span>')
    s = s.replace('<span>💳 bKash · Nagad · Rocket</span>', '<span>📱 <b>WhatsApp</b> +880 1305 869242</span>')

    # Safer page title/meta/OG for homepage.
    if path.name == "index.html" and path.parent == ROOT:
        s = re.sub(r'<title>.*?</title>', '<title>SaveOnSub — Save More on Premium AI &amp; Digital Subscriptions</title>', s, count=1)
        s = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Compare premium AI and digital subscriptions, find smarter-value options, and get real human WhatsApp support in Bangladesh.">', s, count=1)
        s = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="SaveOnSub — Save More. Subscribe Smarter.">', s, count=1)
        s = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="Premium AI and digital subscription savings with clear access information and real human WhatsApp support in Bangladesh.">', s, count=1)

        # Make WhatsApp a primary hero action while retaining catalog discovery.
        s = s.replace('<a href="all.html" class="btn btn-primary">Browse Subscriptions →</a>', f'<a href="{WA}?text=Hi%20SaveOnSub%2C%20I%20need%20help%20choosing%20a%20subscription." class="btn btn-wa">💬 Get Human Support</a>\n      <a href="all.html" class="btn btn-primary">Browse Subscriptions →</a>', 1)

        # Remove homepage-only unverified hero savings/order proof until evidence is linked.
        s = re.sub(r'\s*<div class="anchor">.*?</div>\s*<div class="ticker mt2">.*?</div>', '\n    <div class="ticker mt2"><span class="dotp"></span><span>Before You Subscribe, Check SaveOnSub.</span></div>', s, count=1, flags=re.S)
        s = re.sub(r'<span class="cat">#\d+ Bestseller</span>', '<span class="cat">Popular choice</span>', s)

    if s != old:
        path.write_text(s, encoding="utf-8")
        print("updated", path.relative_to(ROOT))


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
    p = ROOT / "assets" / "style.css"
    s = p.read_text(encoding="utf-8")
    marker = "/* SAVEONSUB BRAND V2 LOCK — 2026-08-19 */"
    if marker not in s:
        s += f'''\n\n{marker}\n/* Approved logo is artwork, never typeset or reconstructed in CSS. */\n.brand-lockup {{ display:inline-flex; align-items:center; flex:0 0 auto; background:#fff; border-radius:10px; padding:4px 7px; line-height:0; overflow:hidden; }}\n.brand-logo {{ display:block; width:190px; height:auto; max-height:46px; object-fit:contain; }}\n.footer-brand {{ margin-bottom:8px; }}\n@media (max-width:600px) {{ .brand-logo {{ width:155px; max-height:40px; }} .brand-lockup {{ padding:3px 5px; }} }}\n/* Brand V2 uses the approved dark-navy + teal identity while retaining accessible existing surfaces. */\n:root {{ --brand-navy:#082035; --brand-teal:#008f82; }}\n''' 
        p.write_text(s, encoding="utf-8")
        print("updated assets/style.css")


def protect_master_assets():
    p = ROOT / "build_assets.py"
    s = p.read_text(encoding="utf-8")
    old = s
    # Prevent future builds from recreating the deprecated tilted ৳ logo.
    start = s.find("# ---------- favicon.svg — the Honest Price Tag mark ----------")
    end = s.find("# ---------- apple-touch-icon.png ----------")
    if start != -1 and end != -1 and end > start:
        replacement = '''# ---------- LOCKED BRAND ASSETS ----------\n# assets/logo.svg and assets/favicon.svg are CEO-approved master-derived assets.\n# DO NOT generate, redraw, recolor or overwrite them in this build script.\n# The deprecated tilted-Taka price-tag generator was removed on 2026-08-19.\n\n'''
        s = s[:start] + replacement + s[end:]
    if s != old:
        p.write_text(s, encoding="utf-8")
        print("updated build_assets.py")


def main():
    migrate_templates()
    migrate_css()
    protect_master_assets()
    for p in ROOT.rglob("*.html"):
        # Skip generated/dependency/internal dirs if present.
        if any(part in {".git", ".next", ".astro", "node_modules", "_site"} for part in p.parts):
            continue
        migrate_html(p)
    print("Brand v2 migration complete")


if __name__ == "__main__":
    main()
