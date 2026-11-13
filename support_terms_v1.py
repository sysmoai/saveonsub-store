#!/usr/bin/env python3
"""Align the staged /warranty pages (EN + BN) with the live Refund Policy V1.

Why: earlier rewriting stages turned the word "warranty" into "support terms"
by global replacement, which left the published page with a duplicated title
("Support terms & Support Terms"), a broken H1 ("A support terms that actually
means something") and a half-English Bangla H1. The body was also vaguer than
the approved Refund V1 table, so customers saw two different stories.

This step rewrites only warranty.html and bn/warranty.html in _site, using the
same situations and outcomes as refund.html / bn/refund.html (CEO-approved
Refund V1, live since 12 Nov 2026). It adds no new promise: no fixed hours,
no day counts, no replacement guarantee. The fail-closed claims guard runs
after this step and checks the result.

Usage: python3 support_terms_v1.py [SITE_DIR]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WA = "https://wa.me/8801305869242"

PAGES = {
    "warranty.html": {
        "title": "Support Terms — What We Fix and How to Claim | SaveOnSub",
        "desc": "If access stops working through no fault of yours inside the covered period, we fix it first, or refund the unused days. Same rules as our refund policy.",
        "home": "./",
        "crumb": "Home",
        "crumb_here": "Support terms",
        "pill": "🛡️ SUPPORT TERMS",
        "h1": 'If it stops working, <span class="grad-text">we fix it first</span>.',
        "lede": "These are the same rules as our <a href=\"refund\">refund policy</a>, written from the support side. The covered period and delivery time for your plan are shown on the product page and at checkout before you pay.",
        "table_label": "What support covers",
        "th": ("Situation", "What we do"),
        "rows": [
            ("Access stops working, it is not your doing, and you are inside the covered period shown on your product",
             "We fix it first. If we cannot restore working access, you get a <b>refund for the unused days</b>"),
            ("Access never worked from the first day and we cannot fix it", "<b>Full refund</b>"),
            ("Wrong product delivered", "Correct product, or <b>full refund</b> if we cannot supply it"),
            ("We do not deliver within the delivery time shown for your order", "<b>Full refund</b> (see the <a href=\"refund\">refund policy</a>)"),
            ("You broke the seat rules given at delivery (changed a shared password, added extra devices, resold or shared your seat)", "Not covered"),
            ("The provider changes something for all users (a model or feature retired, a provider price rise)", "Not our fault. We help you adjust; no refund"),
            ("Plan set up on your own account and covered by the provider's own guarantee", "The provider's own rules apply. We still help you contact them"),
        ],
        "h2_claim": "How to claim",
        "claim": "WhatsApp <b>+880 1305-869242</b> with your order ID and a screenshot of the problem, inside the covered period shown on your product. A person checks every claim and tells you the outcome in writing. Any refund amount and date are confirmed in writing before it is paid.",
        "h2_help": "Help us fix it faster",
        "help": "Keep the order ID from your WhatsApp chat. Do not change passwords, emails or devices on a shared seat. Tell us what you see on screen, not just \"it doesn't work\".",
        "cta": "Message support on WhatsApp",
        "wa_text": "Hi! I need support for my order ID: ",
    },
    "bn/warranty.html": {
        "title": "সাপোর্ট শর্ত — কী ঠিক করি ও কীভাবে জানাবেন | SaveOnSub",
        "desc": "আপনার দোষ ছাড়া কভারের সময়ের মধ্যে অ্যাক্সেস বন্ধ হলে আগে আমরা ঠিক করি, না পারলে অব্যবহৃত দিনের টাকা ফেরত। রিফান্ড নীতির একই নিয়ম।",
        "home": "../bn",
        "crumb": "হোম",
        "crumb_here": "সাপোর্ট শর্ত",
        "pill": "🛡️ সাপোর্ট শর্ত",
        "h1": 'বন্ধ হয়ে গেলে <span class="grad-text">আগে আমরা ঠিক করি</span>।',
        "lede": "এগুলো আমাদের <a href=\"refund\">রিফান্ড নীতির</a> একই নিয়ম, সাপোর্টের দিক থেকে লেখা। আপনার প্ল্যানের কভারের সময় ও ডেলিভারির সময় পেমেন্টের আগে প্রোডাক্ট পেজ ও চেকআউটে দেখানো থাকে।",
        "table_label": "সাপোর্টে কী কভার হয়",
        "th": ("পরিস্থিতি", "আমরা কী করি"),
        "rows": [
            ("আপনার দোষ ছাড়া অ্যাক্সেস বন্ধ হলে এবং প্রোডাক্টে দেখানো কভারের সময়ের মধ্যে থাকলে",
             "আগে আমরা ঠিক করব। চালু করতে না পারলে <b>অব্যবহৃত দিনের রিফান্ড</b>"),
            ("প্রথম দিন থেকেই অ্যাক্সেস কাজ না করলে এবং ঠিক করতে না পারলে", "<b>পূর্ণ রিফান্ড</b>"),
            ("ভুল প্রোডাক্ট ডেলিভারি", "সঠিক প্রোডাক্ট, দিতে না পারলে <b>পূর্ণ রিফান্ড</b>"),
            ("অর্ডারে দেখানো ডেলিভারির সময়ের মধ্যে ডেলিভারি না দিলে", "<b>পূর্ণ রিফান্ড</b> (<a href=\"refund\">রিফান্ড নীতি</a> দেখুন)"),
            ("ডেলিভারির সময় দেওয়া নিয়ম ভাঙলে (শেয়ার্ড পাসওয়ার্ড বদল, বাড়তি ডিভাইস, সিট বিক্রি বা শেয়ার)", "কভার নয়"),
            ("প্রোভাইডার সব ব্যবহারকারীর জন্য কিছু বদলালে (মডেল বা ফিচার বন্ধ, দাম বাড়ানো)", "আমাদের দোষ নয়। মানিয়ে নিতে সাহায্য করব, রিফান্ড নয়"),
            ("আপনার নিজের অ্যাকাউন্টে চালু করা প্ল্যান, যেখানে প্রোভাইডারের নিজস্ব গ্যারান্টি আছে", "প্রোভাইডারের নিয়ম প্রযোজ্য। তাদের সাথে যোগাযোগে আমরা সাহায্য করব"),
        ],
        "h2_claim": "কীভাবে জানাবেন",
        "claim": "WhatsApp <b>+880 1305-869242</b> নম্বরে অর্ডার আইডি ও সমস্যার স্ক্রিনশট পাঠান, প্রোডাক্টে দেখানো কভারের সময়ের মধ্যে। প্রতিটি দাবি একজন মানুষ দেখেন এবং ফলাফল লিখিতভাবে জানান। রিফান্ড হলে টাকা পাঠানোর আগে পরিমাণ ও তারিখ লিখিতভাবে জানানো হয়।",
        "h2_help": "দ্রুত ঠিক করতে সাহায্য করুন",
        "help": "WhatsApp চ্যাট থেকে অর্ডার আইডি রেখে দিন। শেয়ার্ড সিটে পাসওয়ার্ড, ইমেইল বা ডিভাইস বদলাবেন না। শুধু \"কাজ করছে না\" না লিখে স্ক্রিনে কী দেখছেন তা জানান।",
        "cta": "WhatsApp-এ সাপোর্টে মেসেজ করুন",
        "wa_text": "হাই! আমার অর্ডারের জন্য সাপোর্ট দরকার। অর্ডার আইডি: ",
    },
}


def esc_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def body_html(p: dict) -> str:
    from urllib.parse import quote

    # Stacked cards instead of a table: at 375 px the shared .tbl wrapper scrolls
    # sideways and hides the outcome column, which is the part customers need.
    rows = "".join(
        '<li style="border:1px solid var(--line,rgba(255,255,255,.12));border-radius:14px;padding:14px 16px;margin:0 0 10px">'
        f'<p style="margin:0 0 6px;font-size:15px">{a}</p>'
        f'<p style="margin:0;font-size:15px;color:var(--green2,#3ee0c0)">→ {b}</p></li>'
        for a, b in p["rows"]
    )
    return (
        '<main id="main"><div class="wrap" style="max-width:820px">\n'
        f'  <div class="crumbs"><a href="{p["home"]}">{p["crumb"]}</a> › {p["crumb_here"]}</div>\n'
        f'<span class="pill">{p["pill"]}</span>'
        f'<h1 style="font-size:clamp(26px,4vw,38px)">{p["h1"]}</h1>\n'
        f'<p class="sub">{p["lede"]}</p>\n'
        f'<h2 class="mt3" style="font-size:21px">{p["table_label"]}</h2>\n'
        f'<ul class="mt3" style="list-style:none;padding:0;margin:12px 0 0">{rows}</ul>\n'
        f'<h2 class="mt3" style="font-size:21px">{p["h2_claim"]}</h2>\n'
        f'<p class="sub" style="font-size:15px">{p["claim"]}</p>\n'
        f'<h2 class="mt3" style="font-size:21px">{p["h2_help"]}</h2>\n'
        f'<p class="sub" style="font-size:15px">{p["help"]}</p>\n'
        f'<p class="mt3"><a class="btn btn-wa" href="{WA}?text={quote(p["wa_text"])}" target="_blank" rel="noopener">{p["cta"]}</a></p>\n'
        "</div></main>"
    )


def set_meta(t: str, attr: str, name: str, value: str) -> str:
    pat = re.compile(rf'(<meta {attr}="{re.escape(name)}" content=")[^"]*(")')
    return pat.sub(lambda m: m.group(1) + esc_attr(value) + m.group(2), t)


def main() -> int:
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
    for rel, p in PAGES.items():
        f = site / rel
        if not f.exists():
            print(f"[support-terms] FAIL — missing {rel}")
            return 1
        t = f.read_text(encoding="utf-8")
        new, n = re.subn(r"(?s)<main id=\"main\">.*?</main>", lambda _m: body_html(p), t, count=1)
        if n != 1:
            print(f"[support-terms] FAIL — no <main> in {rel}")
            return 1
        new = re.sub(r"<title>[^<]*</title>", f"<title>{p['title']}</title>", new, count=1)
        new = set_meta(new, "name", "description", p["desc"])
        new = set_meta(new, "property", "og:title", p["title"])
        new = set_meta(new, "property", "og:description", p["desc"])
        new = set_meta(new, "name", "twitter:title", p["title"])
        new = set_meta(new, "name", "twitter:description", p["desc"])
        for bad in ("Support terms & Support Terms", "A support terms", "সাপোর্ট শর্ত ও সাপোর্ট শর্ত"):
            if bad in new:
                print(f"[support-terms] FAIL — '{bad}' still in {rel}")
                return 1
        f.write_text(new, encoding="utf-8")
    print("[support-terms] PASS — /warranty EN+BN aligned with Refund V1 (no new timing or day-count promise)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
