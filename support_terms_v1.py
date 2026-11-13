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
        "lede": "These are exactly the rules of our <a href=\"refund\">refund policy</a>, repeated here for support. The delivery time and covered period for your order are confirmed in writing before you pay (see checkout).",
        "table_label": "What support covers",
                "h2_claim": "How to claim", "refund_page": "refund.html", "claim_h2": "How to request",
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
        "lede": "এগুলো হুবহু আমাদের <a href=\"refund\">রিফান্ড নীতির</a> নিয়ম, সাপোর্টের জন্য এখানে আবার দেওয়া হলো। আপনার অর্ডারের ডেলিভারির সময় ও কভারের সময় পেমেন্টের আগে লিখিতভাবে নিশ্চিত করা হয় (চেকআউট দেখুন)।",
        "table_label": "সাপোর্টে কী কভার হয়",
                "h2_claim": "কীভাবে জানাবেন", "refund_page": "bn/refund.html", "claim_h2": "কীভাবে জানাবেন",
        "h2_help": "দ্রুত ঠিক করতে সাহায্য করুন",
        "help": "WhatsApp চ্যাট থেকে অর্ডার আইডি রেখে দিন। শেয়ার্ড সিটে পাসওয়ার্ড, ইমেইল বা ডিভাইস বদলাবেন না। শুধু \"কাজ করছে না\" না লিখে স্ক্রিনে কী দেখছেন তা জানান।",
        "cta": "WhatsApp-এ সাপোর্টে মেসেজ করুন",
        "wa_text": "হাই! আমার অর্ডারের জন্য সাপোর্ট দরকার। অর্ডার আইডি: ",
    },
}


def esc_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


TAGS = re.compile(r"<[^>]+>")
ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


def refund_source(site: Path, p: dict):
    """Single source of truth: situation/outcome pairs and the how-to-request paragraph
    are read verbatim from the built refund page, so support terms cannot drift from it."""
    t = (site / p["refund_page"]).read_text(encoding="utf-8")
    rows = []
    for r in ROW.findall(t):
        cells = CELL.findall(r)
        if len(cells) >= 2:
            rows.append((cells[0].strip(), cells[1].strip()))
    m = re.search(r"<h2[^>]*>\s*" + re.escape(p["claim_h2"]) + r"\s*</h2>\s*<p[^>]*>(.*?)</p>", t, re.S)
    if len(rows) < 8 or not m:
        raise SystemExit(f"[support-terms] FAIL — cannot read refund rows/claim from {p['refund_page']}")
    return rows, m.group(1).strip()


def body_html(p: dict, rows_src, claim: str) -> str:
    from urllib.parse import quote

    # Stacked cards instead of a table: at 375 px the shared .tbl wrapper scrolls
    # sideways and hides the outcome column, which is the part customers need.
    rows = "".join(
        '<li style="border:1px solid var(--line,rgba(255,255,255,.12));border-radius:14px;padding:14px 16px;margin:0 0 10px">'
        f'<p style="margin:0 0 6px;font-size:15px">{a}</p>'
        f'<p style="margin:0;font-size:15px;color:var(--green2,#3ee0c0)">→ {b}</p></li>'
        for a, b in rows_src
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
        f'<p class="sub" style="font-size:15px">{claim}</p>\n'
        f'<h2 class="mt3" style="font-size:21px">{p["h2_help"]}</h2>\n'
        f'<p class="sub" style="font-size:15px">{p["help"]}</p>\n'
        f'<p class="mt3"><a class="btn btn-wa" href="{WA}?text={quote(p["wa_text"])}" target="_blank" rel="noopener">{p["cta"]}</a></p>\n'
        "</div></main>"
    )


def set_meta(t: str, attr: str, name: str, value: str) -> str:
    pat = re.compile(rf'(<meta {attr}="{re.escape(name)}" content=")[^"]*(")')
    return pat.sub(lambda m: m.group(1) + esc_attr(value) + m.group(2), t)


ORDER_FIXES = {
    "order.html": [
        ("<li>Something off? <b>order-specific support terms support terms</b> from minute one.</li>",
         '<li>Something off? WhatsApp us your order ID. See the <a href="warranty">support terms</a> and <a href="refund">refund policy</a>.</li>'),
        ("ডেলিভারি সময় অর্ডারের আগে নিশ্চিত করা হয়ে ডেলিভারি।",
         "ডেলিভারির সময় ও কভারেজ পেমেন্টের আগে লিখিতভাবে নিশ্চিত করা হয়।"),
    ],
}


def fix_order_pages(site: Path) -> None:
    """Repair leftovers of earlier global text rewrites on the order receipt page."""
    for rel, pairs in ORDER_FIXES.items():
        f = site / rel
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        for old, new in pairs:
            t = t.replace(old, new)
        f.write_text(t, encoding="utf-8")


def main() -> int:
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
    for rel, p in PAGES.items():
        f = site / rel
        if not f.exists():
            print(f"[support-terms] FAIL — missing {rel}")
            return 1
        t = f.read_text(encoding="utf-8")
        rows_src, claim = refund_source(site, p)
        new, n = re.subn(r"(?s)<main id=\"main\">.*?</main>", lambda _m: body_html(p, rows_src, claim), t, count=1)
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
    fix_order_pages(site)
    print("[support-terms] PASS — /warranty EN+BN aligned with Refund V1 (no new timing or day-count promise)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
