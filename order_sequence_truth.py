#!/usr/bin/env python3
"""Make /how-to-order (EN + BN) follow the same order sequence as the homepage,
the product pages and the refund terms.

Problem (CEO audit 14 Nov 2026): /how-to-order told buyers to send money in
step 2 and confirm on WhatsApp in step 3, while the homepage, product pages and
checkout say price, access method, timing and covered period are confirmed in
writing BEFORE payment. The page also promised "3 minutes, start to delivered"
and described a screenshot/TxnID flow without saying that payment only counts
once the actual incoming credit is verified in the authorized receiving account.

New sequence (identical everywhere):
  choose -> written confirmation on WhatsApp -> pay -> receiving-side verification ->
  fulfil -> support.

What this step does NOT do: it does not change the payment number or any
receiving instruction. The number that was already printed on the page stays
exactly as it was; the page now tells buyers to pay only after the written
confirmation and to check that the number matches it. Which number is the
CEO-verified receiving account is a CEO decision (see PR description).
No delivery-time promise, no SLA, no new guarantee.

Usage: python3 order_sequence_truth.py [SITE_DIR] [--check]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = "data-order-sequence-truth"
NUM_EN = "+880 1305-869242"
NUM_BN = "+৮৮০ ১৩০৫-৮৬৯২৪২"

PAGES = {
    "how-to-order.html": {
        "title": "How to Order with bKash, Nagad or Rocket — Step by Step | SAVEONSUB",
        "desc": "Choose a plan, get the access method, total and timing confirmed in writing on WhatsApp, then pay. We verify the payment before fulfilling your order.",
        "h1": 'First time? <span class="grad-text">Here is the order, step by step.</span>',
        "steps": [
            ("Pick your product", 'Browse <a href="all" style="color:var(--green2)">all products</a> or take the <a href="quiz" style="color:var(--green2)">quiz</a>. Each plan shows its price and whether access is shared, personal or team. Tap <b>Add to cart</b>.'),
            ("Confirm on WhatsApp before you pay", "Tap the green button. A WhatsApp message with your order ID opens. Send it. We reply in writing with the plan, access method, total, delivery timing, covered period and the payment destination for your order."),
            ("Pay only after that confirmation", f"Open bKash/Nagad/Rocket → <b>Send Money</b> → the payment number shown at our checkout (currently {NUM_EN}). It must match the number in our written confirmation. Amount = the confirmed total. Reference = your order ID. Never pay a number from another website or chat."),
            ("We verify the incoming payment", "A payment counts only after we see the actual incoming credit in the authorized receiving account (wallet or bank). A TxnID or screenshot alone is not payment. We then update the payment status and delivery status of your existing order ID."),
            ("Delivery and support", "Access or an invite follows on WhatsApp, as confirmed for your order. The support terms of your plan are on its product page and in the refund policy. Save our number in case you need help."),
        ],
        "nervous_h": "Nervous about paying first?",
        "nervous": "You never have to pay before you have the price, access method, timing and covered period in writing. If anything in the written confirmation differs from the product page, stop and ask us before you pay.",
        "mistakes_h": "Common first-order mistakes (avoid these)",
        "mistakes": "Paying before the written confirmation · forgetting the order ID in the reference · sending to a number that does not match our written confirmation, or one from any other website · changing the password on a shared seat (it can end access for everyone and support terms may not apply).",
        "cta": "Start shopping →",
        "howto_name": "How to buy a subscription on SAVEONSUB with bKash, Nagad or Rocket",
        "howto_names": ["Pick your product", "Confirm on WhatsApp before you pay", "Pay after the written confirmation", "We verify the incoming payment", "Delivery and support"],
    },
    "bn/how-to-order.html": {
        "title": "বিকাশ, নগদ বা রকেটে কীভাবে অর্ডার করবেন — ধাপে ধাপে | SAVEONSUB",
        "desc": "প্ল্যান বাছুন, WhatsApp-এ অ্যাক্সেস পদ্ধতি, মোট দাম ও সময় লিখিতভাবে নিশ্চিত করুন, তারপর পেমেন্ট করুন। পেমেন্ট যাচাইয়ের পরই অর্ডার পূরণ হয়।",
        "h1": 'প্রথমবার? <span class="grad-text">অর্ডারের ধাপগুলো এক নজরে।</span>',
        "steps": [
            ("প্রোডাক্ট বেছে নিন", '<a href="../all" style="color:var(--green2)">সব প্রোডাক্ট</a> দেখুন বা <a href="quiz" style="color:var(--green2)">কুইজ</a> দিন। প্রতিটি প্ল্যানে দাম এবং অ্যাক্সেস শেয়ার্ড, পার্সোনাল না টিম, তা লেখা আছে। <b>কার্টে যোগ করুন</b>।'),
            ("পেমেন্টের আগে WhatsApp-এ নিশ্চিত করুন", "সবুজ বাটনে চাপ দিন। আপনার অর্ডার আইডিসহ একটি মেসেজ খুলবে, পাঠিয়ে দিন। আমরা লিখিতভাবে জানাব প্ল্যান, অ্যাক্সেস পদ্ধতি, মোট দাম, ডেলিভারির সময়, কভারের সময় ও পেমেন্ট গ্রহণের গন্তব্য।"),
            ("নিশ্চিতকরণের পরই পেমেন্ট করুন", f"বিকাশ/নগদ/রকেট খুলুন → <b>Send Money</b> → আমাদের চেকআউটে দেখানো পেমেন্ট নম্বর (বর্তমানে {NUM_BN})। নম্বরটি আমাদের লিখিত নিশ্চিতকরণের নম্বরের সাথে মিলতে হবে। অ্যামাউন্ট = নিশ্চিত করা মোট। রেফারেন্স = আপনার অর্ডার আইডি। অন্য কোনো ওয়েবসাইট বা চ্যাটের নম্বরে টাকা পাঠাবেন না।"),
            ("আমরা আসল ইনকামিং পেমেন্ট যাচাই করি", "অনুমোদিত রিসিভিং অ্যাকাউন্টে (ওয়ালেট বা ব্যাংক) আসল ইনকামিং টাকা দেখার পরই পেমেন্ট গণ্য হয়। শুধু TxnID বা স্ক্রিনশট পেমেন্ট নয়। তারপর আপনার বিদ্যমান অর্ডার আইডির পেমেন্ট স্ট্যাটাস ও ডেলিভারি স্ট্যাটাস আপডেট করি।"),
            ("ডেলিভারি ও সাপোর্ট", "আপনার অর্ডারে যা নিশ্চিত করা হয়েছে সেই অনুযায়ী WhatsApp-এ অ্যাক্সেস বা ইনভাইট আসে। প্ল্যানের সাপোর্ট শর্ত পণ্যের পেজে ও রিফান্ড নীতিতে আছে। সাহায্য লাগলে নম্বরটা সেভ রাখুন।"),
        ],
        "nervous_h": "আগে টাকা দিতে ভয়?",
        "nervous": "দাম, অ্যাক্সেস পদ্ধতি, সময় ও কভারের সময় লিখিতভাবে হাতে পাওয়ার আগে আপনাকে টাকা দিতে হবে না। লিখিত নিশ্চিতকরণ পণ্যের পেজ থেকে আলাদা হলে পেমেন্টের আগে আমাদের জিজ্ঞেস করুন।",
        "mistakes_h": "নতুনদের সাধারণ ভুল (এড়িয়ে চলুন)",
        "mistakes": "লিখিত নিশ্চিতকরণের আগে পেমেন্ট করা · রেফারেন্সে অর্ডার আইডি না দেওয়া · আমাদের লিখিত নিশ্চিতকরণের সাথে মেলে না এমন নম্বরে বা অন্য ওয়েবসাইটের নম্বরে টাকা পাঠানো · শেয়ার্ড সিটের পাসওয়ার্ড বদলানো (এতে সবার অ্যাক্সেস বন্ধ হতে পারে এবং সাপোর্ট শর্ত নাও খাটতে পারে)।",
        "cta": "শপিং শুরু করুন →",
        "howto_name": "বিকাশ, নগদ বা রকেটে SAVEONSUB থেকে সাবস্ক্রিপশন কেনার ধাপ",
        "howto_names": ["প্রোডাক্ট বেছে নিন", "পেমেন্টের আগে WhatsApp-এ নিশ্চিত করুন", "নিশ্চিতকরণের পর পেমেন্ট", "আমরা আসল ইনকামিং পেমেন্ট যাচাই করি", "ডেলিভারি ও সাপোর্ট"],
    },
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;")


def strip(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def render_main(c: dict) -> str:
    steps = "".join(f'<div class="step"><h3>{i}. {t}</h3><p>{p}</p></div>' for i, (t, p) in enumerate(c["steps"], 1))
    return (
        f'<h1 style="font-size:clamp(26px,4vw,38px)" {MARK}="1">{c["h1"]}</h1>\n'
        f'<div class="steps mt3" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr))">{steps}</div>\n'
        f'<h2 class="mt3" style="font-size:21px">{c["nervous_h"]}</h2>\n'
        f'<p class="sub" style="font-size:15px">{c["nervous"]}</p>\n'
        f'<h2 class="mt3" style="font-size:21px">{c["mistakes_h"]}</h2>\n'
        f'<p class="sub" style="font-size:15px">{c["mistakes"]}</p>\n'
    )


MAIN_RE = re.compile(r'<h1 style="font-size:clamp\(26px,4vw,38px\)"[^>]*>.*?(?=<div class="heroctas)', re.S)
HOWTO_RE = re.compile(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "HowTo".*?</script>', re.S)


def howto(c: dict) -> str:
    data = {"@context": "https://schema.org", "@type": "HowTo", "name": c["howto_name"],
            "step": [{"@type": "HowToStep", "position": i, "name": n, "text": strip(p)}
                     for i, (n, (_, p)) in enumerate(zip(c["howto_names"], c["steps"]), 1)]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


def apply_page(site: Path, rel: str, c: dict) -> str | None:
    f = site / rel
    if not f.exists():
        return f"missing {rel}"
    t = f.read_text(encoding="utf-8")
    if MARK in t:
        return None
    if not MAIN_RE.search(t) or not HOWTO_RE.search(t):
        return f"anchors not found in {rel}"
    t = MAIN_RE.sub(lambda m: render_main(c), t, count=1)
    t = HOWTO_RE.sub(lambda m: howto(c), t, count=1)
    t = re.sub(r"<title>.*?</title>", lambda m: f"<title>{esc(c['title'])}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', lambda m: f'<meta name="description" content="{esc(c["desc"])}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: f'<meta property="og:title" content="{esc(c["title"])}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: f'<meta property="og:description" content="{esc(c["desc"])}">', t, count=1)
    f.write_text(t, encoding="utf-8")
    return None


def verify(site: Path) -> list[str]:
    errs = []
    for rel, c in PAGES.items():
        t = (site / rel).read_text(encoding="utf-8") if (site / rel).exists() else ""
        if MARK not in t:
            errs.append(f"{rel}: sequence block missing")
            continue
        main = t[t.find("<main"):t.find("</main>")]
        txt = re.sub(r"<[^>]+>", " ", main)
        for bad in ("3 minutes", "৩ মিনিট", "3-Minute", "PT3M", "5–15", "৫–১৫", "start to delivered"):
            if bad in t:
                errs.append(f"{rel}: forbidden phrase {bad!r}")
        pay = re.search(r"Send Money", txt)
        conf = re.search(r"Confirm on WhatsApp before you pay|পেমেন্টের আগে WhatsApp-এ নিশ্চিত করুন", txt)
        if not (pay and conf and conf.start() < pay.start()):
            errs.append(f"{rel}: written confirmation must come before the payment step")
        num = NUM_BN if rel.startswith("bn/") else NUM_EN
        if txt.count(num) != 1:
            errs.append(f"{rel}: payment number must appear exactly once and unchanged")
    return errs


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    site = Path(args[0]) if args else ROOT / "_site"
    if "--check" not in sys.argv:
        for rel, c in PAGES.items():
            e = apply_page(site, rel, c)
            if e:
                print(f"[order-sequence] FAIL — {e}")
                return 1
    errs = verify(site)
    if errs:
        print("[order-sequence] FAIL")
        for e in errs:
            print("  " + e)
        return 1
    print("[order-sequence] PASS — /how-to-order (EN+BN): confirm in writing, then pay, then receiving-side verification; no minute SLA; payment number unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
