#!/usr/bin/env python3
"""Conversion + SEO upgrade for staged product pages and the home pages (build step).

Runs after ``prices_page.py`` and BEFORE ``hold_content_price_guard.py`` and the
claims/commercial audits, so every guard still checks the final HTML. Source of
truth is the governed public catalog already staged in ``_site/assets/catalog.js``
(only CEO-approved plans), so this step cannot invent a price.

Per priced product page (EN /p and BN /bn/p, AIPS and inquiry pages excluded):
- hero: generic emoji -> branded monogram tile (no provider logos/trademarks);
- "Key facts" box right under the plans: price range, access types, billing,
  payment methods, how to order, provider list price (when catalog has one),
  refund policy link and last price update. Answer-first for shoppers and AI
  search; every value is already visible elsewhere on the page or in the catalog;
- "Compare plans" table when a product has more than one plan;
- "How ordering works" 4-step strip (no timing/SLA promises);
- related products: plain link list -> cards (tile, name, category, plan count;
  no amounts, because a product page may only show its own approved prices);
- mobile sticky buy bar (lowest price + WhatsApp order + jump to plans); the
  WhatsApp link reuses the page's existing order prefill so catalog_reconcile
  still sees one prefill per page.

Home (/ and /bn):
- trust bar lists every access type actually sold (it omitted "Shared");
- hero headline/sub rewritten for shoppers (no superlatives, no counts of
  customers/orders, product count taken from the catalog);
- hero card emoji -> monogram tiles; "Why SaveOnSub" (4 verifiable facts),
  payment-method row and a 5-question FAQ with matching FAQPage JSON-LD.

No ratings, reviews, rankings, savings %, compare-at prices, delivery-time or
guarantee claims are added. ``--check`` verifies the staged artifact only.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from product_rich_results import (FORBIDDEN, access_text, clean_name, load_catalog, price_text,
                                  priced, approved_on, money, unit_text)

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
CATALOG_SRC = ROOT / "catalog.json"
MARK = "conversion-upgrade-2026-11-10"
WA = "8801305869242"
WA_DISPLAY = "+880 1305 869242"

HUE = {"AI Assistants": 172, "AI Image & Design": 300, "AI Video": 345, "AI Voice & Music": 260,
       "AI Code & Dev": 210, "AI Writing": 30, "Workspace & Productivity": 195, "Entertainment": 0,
       "Education & Career": 45, "VPN & Security": 140, "Gaming": 280, "BD Lifestyle": 150, "Bundles": 185}

BLOCK = re.compile(rf'<(section|div|script)[^>]*data-sos="{MARK}"[^>]*>.*?</\1>', re.S)


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def initials(name: str) -> str:
    words = [w for w in re.split(r"[\s\-+()/]+", clean_name(name)) if w and w[0].isalnum()]
    if not words:
        return "S"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def tile(name: str, category: str, cls: str = "ptile") -> str:
    # Category hue plus a small stable per-name offset so neighbours differ.
    hue = (HUE.get(category, 172) + (sum(map(ord, name)) % 7 - 3) * 9) % 360
    return f'<span class="{cls}" style="--h:{hue}" aria-hidden="true">{esc(initials(name))}</span>'


def kinds_of(plans: list[dict]) -> list[str]:
    seen: list[str] = []
    for pl in plans:
        k = pl.get("type") or pl.get("access_type") or ""
        if k not in seen:
            seen.append(k)
    return seen


def official_refs() -> dict[str, dict]:
    try:
        data = json.loads(CATALOG_SRC.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    items = data.get("products", data) if isinstance(data, dict) else data
    out = {}
    for p in items if isinstance(items, list) else []:
        if isinstance(p, dict) and p.get("id"):
            out[p["id"]] = {"usd": p.get("official_usd"), "url": p.get("official_url") or p.get("url")}
    return out


# ------------------------------------------------------------------ copy

BILLING = {False: {"month": "Monthly", "user/month": "Per user, monthly", "year": "Yearly", "6 months": "Every 6 months"},
           True: {"month": "মাসিক", "user/month": "প্রতি ব্যবহারকারী, মাসিক", "year": "বার্ষিক", "6 months": "প্রতি ৬ মাস"}}

GOOD_FOR = {
    "shared": ("Trying it out or light personal use (others share the account)",
               "চেষ্টা করে দেখা বা হালকা ব্যক্তিগত ব্যবহার (অন্যরাও একই অ্যাকাউন্ট ব্যবহার করেন)"),
    "personal": ("Work, private chats and files, your own history",
                 "কাজ, ব্যক্তিগত চ্যাট ও ফাইল, নিজের হিস্ট্রি"),
    "team": ("Teams that need a shared workspace", "যাদের টিম ওয়ার্কস্পেস দরকার"),
    "official": ("Your own provider account, with setup help", "নিজের প্রোভাইডার অ্যাকাউন্ট, সেটআপ সহায়তাসহ"),
    "bundle": ("Getting several tools in one order", "এক অর্ডারে একাধিক টুল"),
}


def key_facts(p: dict, plans: list[dict], ref: dict, date: str, bn: bool, prefix: str) -> str:
    low = min(plans, key=lambda x: x["bdt"])
    high = max(plans, key=lambda x: x["bdt"])
    access = ", ".join(dict.fromkeys(access_text(pl, bn) for pl in plans))
    units = ", ".join(dict.fromkeys(BILLING[bn].get(pl.get("billing_unit", "month"), unit_text(pl, bn)) for pl in plans))
    rng = price_text(low, bn) if low is high or low["bdt"] == high["bdt"] else \
        (f"{money(low['bdt'])} – {money(high['bdt'])}" + (f" ({len(plans)}টি প্ল্যান)" if bn else f" ({len(plans)} plans)"))
    rows = []
    if bn:
        rows += [("দাম", rng), ("অ্যাক্সেস টাইপ", access), ("বিলিং", units),
                 ("পেমেন্ট", "বিকাশ, নগদ, রকেট (টাকায়)"),
                 ("অর্ডার", f'কার্টে যোগ করুন বা WhatsApp <a href="https://wa.me/{WA}" target="_blank" rel="noopener">{WA_DISPLAY}</a>')]
        if isinstance(ref.get("usd"), (int, float)) and ref.get("url"):
            rows.append(("প্রোভাইডারের লিস্ট প্রাইস", f'${ref["usd"]:g} (আন্তর্জাতিক কার্ডে), সাথে বিদেশি ডিজিটাল সার্ভিসে কার্ড পেমেন্টে ১৫% ভ্যাট (চেকআউটে বা ব্যাংক কেটে নেয়) ও ব্যাংকের চার্জ — <a href="{esc(ref["url"])}" target="_blank" rel="noopener nofollow">অফিসিয়াল পেজ ↗</a>'))
        rows += [("রিফান্ড", f'<a href="{prefix}/refund">রিফান্ড নীতি</a> · <a href="{prefix}/warranty">সাপোর্ট শর্ত</a>'),
                 ("দাম হালনাগাদ", esc(date))]
        title = f"{esc(p['name'])} — মূল তথ্য"
    else:
        rows += [("Price", rng), ("Access type", access), ("Billing", units),
                 ("Payment", "bKash, Nagad, Rocket (pay in taka)"),
                 ("How to order", f'Add to cart, or WhatsApp <a href="https://wa.me/{WA}" target="_blank" rel="noopener">{WA_DISPLAY}</a>')]
        if isinstance(ref.get("usd"), (int, float)) and ref.get("url"):
            rows.append(("Provider list price", f'${ref["usd"]:g} by international card, plus 15% Bangladesh VAT on card payments to foreign digital services (charged at checkout or by your bank) and any bank charges — <a href="{esc(ref["url"])}" target="_blank" rel="noopener nofollow">official page ↗</a>'))
        rows += [("Refunds", f'<a href="{prefix}/refund">Refund policy</a> · <a href="{prefix}/warranty">Support terms</a>'),
                 ("Prices updated", esc(date))]
        title = f"{esc(p['name'])} key facts"
    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return f'<section data-sos="{MARK}" class="kfacts mt3"><h2>{title}</h2><dl>{dl}</dl></section>'


BD_VAT = 0.15
NO_VALUE_BOX = {"pubg-royale-pass"}  # game passes are not provider-billed subscriptions


def fx_reference() -> float:
    try:
        return float(json.loads(POLICY.read_text(encoding="utf-8")).get("fx_reference_bdt_per_usd") or 0)
    except (OSError, ValueError, TypeError):
        return 0.0


def direct_plans(pid: str, plans: list[dict], usd, fx: float) -> list[dict]:
    """Personal plans whose taka price covers the provider's list price + 15% VAT at the
    pricebook FX reference: the plans SaveOnSub buys directly on the customer's own
    account (CEO, 2026-11-12). Cheaper 'personal' plans are not described this way."""
    if pid in NO_VALUE_BOX or not isinstance(usd, (int, float)) or usd <= 0 or fx <= 0:
        return []
    floor = usd * (1 + BD_VAT) * fx
    return [pl for pl in plans
            if (pl.get("type") or pl.get("access_type")) in ("personal", "official")
            and floor <= int(pl["bdt"]) <= floor * 1.3]


def value_box(p: dict, plans: list[dict], ref: dict, bn: bool) -> str:
    usd = ref.get("usd")
    picks = direct_plans(p["id"], plans, usd, fx_reference())
    if not picks:
        return ""
    name = clean_name(p.get("name", p["id"]))
    pl = min(picks, key=lambda x: int(x["bdt"]))
    bdt = f"৳{int(pl['bdt']):,}"
    with_vat = f"{usd * (1 + BD_VAT):.2f}".rstrip("0").rstrip(".")
    if bn:
        bdt = bdt.translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))
        h = f"{esc(pl['label'])} প্ল্যানের {bdt}-এ কী কী থাকে"
        rows = [
            f"প্রোভাইডারের কাছ থেকে <b>আপনার নিজের অ্যাকাউন্টে</b> কেনা অফিসিয়াল {esc(name)} প্ল্যান। লিস্ট প্রাইস ${usd:g}।",
            f"বাংলাদেশে বিদেশি ডিজিটাল সার্ভিসে কার্ড পেমেন্টে <b>১৫% ভ্যাট</b> লাগে, তাই চেকআউটে ${usd:g} হয়ে যায় ${with_vat}।",
            f"আপনার {bdt}-এর মধ্যে এই পুরো খরচ, আন্তর্জাতিক কার্ড ও ডলার রেটের চার্জ, অ্যাক্টিভেশন সহায়তা এবং বাংলা ও ইংরেজিতে WhatsApp সাপোর্ট ধরা আছে। আমাদের পেমেন্ট করার সময় আলাদা ভ্যাট বা কার্ড চার্জ নেই।",
            "বিকাশ, নগদ বা রকেটে টাকায় পেমেন্ট করুন; আন্তর্জাতিক কার্ড লাগবে না।",
        ]
    else:
        h = f"What the {bdt} {esc(pl['label'])} plan includes"
        rows = [
            f"An official {esc(name)} plan bought from the provider on <b>your own account</b>. List price ${usd:g}.",
            f"Bangladesh adds <b>15% VAT</b> to card payments for foreign digital services, so ${usd:g} becomes ${with_vat} at checkout.",
            f"Your {bdt} covers that full amount, the international card and dollar-rate charges, activation help and WhatsApp support in Bangla and English. No separate VAT or card fee when you pay us.",
            "Pay in taka with bKash, Nagad or Rocket; no international card needed.",
        ]
    lis = "".join(f"<li>{r}</li>" for r in rows)
    return f'<section data-sos="{MARK}" class="valuebox mt3"><h2>{h}</h2><ul>{lis}</ul></section>'


# Provider benefit lists, checked against the provider's own plan pages. Keep each
# entry dated and sourced; model names and limits change often, so describe them
# by tier ("Pro models") rather than version numbers.
BENEFITS = {
    "google-ai-pro": {
        "checked": "2026-11-12",
        "source": "https://gemini.google/subscriptions/",
        "en": [
            "<b>Gemini with Google's Pro models</b>: about 4x the usage limits of free Gemini and a 1M-token context window for long files.",
            "<b>Deep Research</b>: Gemini searches the web and writes a sourced report for you.",
            "<b>Video and image generation</b>: Veo video in Gemini, 1,000 monthly credits in Google Flow, and higher Nano Banana image limits.",
            "<b>Gemini Notebook (NotebookLM)</b>: more notebooks and 5x the Audio Overviews.",
            "<b>Gemini inside Gmail, Docs, Sheets and Vids</b>, plus Gemini in Chrome and more AI Mode access in Google Search.",
            "<b>For developers</b>: higher limits in Google AI Studio, Antigravity and Android Studio, 200 Colab compute units a month and $10 monthly Google Cloud credit.",
            "<b>5 TB cloud storage</b> across Gmail, Drive and Photos, with family sharing for up to five others.",
            "<b>Extras</b> where Google offers them in your country: YouTube Premium Lite and Google Home Premium.",
        ],
        "bn": [
            "<b>Google-এর Pro মডেলসহ Gemini</b>: ফ্রি Gemini-এর প্রায় ৪ গুণ ইউসেজ লিমিট, আর লম্বা ফাইলের জন্য ১০ লাখ টোকেন context window।",
            "<b>Deep Research</b>: Gemini ওয়েব ঘেঁটে সোর্সসহ পুরো রিপোর্ট লিখে দেয়।",
            "<b>ভিডিও ও ছবি বানানো</b>: Gemini-তে Veo ভিডিও, Google Flow-তে মাসে ১,০০০ ক্রেডিট, Nano Banana ইমেজের বেশি লিমিট।",
            "<b>Gemini Notebook (NotebookLM)</b>: বেশি নোটবুক আর ৫ গুণ Audio Overview।",
            "<b>Gmail, Docs, Sheets ও Vids-এর ভেতরেই Gemini</b>, সাথে Chrome-এ Gemini আর Google Search-এর AI Mode-এ বেশি অ্যাক্সেস।",
            "<b>ডেভেলপারদের জন্য</b>: Google AI Studio, Antigravity ও Android Studio-তে বেশি লিমিট, মাসে ২০০ Colab compute unit আর $১০ Google Cloud ক্রেডিট।",
            "<b>৫ TB ক্লাউড স্টোরেজ</b> Gmail, Drive ও Photos জুড়ে, পরিবারের আরও ৫ জনের সাথে শেয়ার করা যায়।",
            "<b>এক্সট্রা</b> (Google আপনার দেশে দিলে): YouTube Premium Lite ও Google Home Premium।",
        ],
    },
}


def benefits_box(p: dict, plans: list[dict], bn: bool) -> str:
    b = BENEFITS.get(p["id"])
    if not b or not plans:
        return ""
    name = clean_name(p.get("name", p["id"]))
    pl = min(plans, key=lambda x: int(x["bdt"]))
    bdt = f"৳{int(pl['bdt']):,}"
    src = f'<a href="{b["source"]}" target="_blank" rel="noopener nofollow">'
    if bn:
        bdt = bdt.translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))
        h = f"{esc(name)}-এ কী কী পাবেন"
        lead = (f"{bdt}-এ {esc(name)} চালু হয় <b>আপনার নিজের Gmail অ্যাকাউন্টে</b>, তাই প্রতিটি ফিচার আপনার নিজের "
                "Gemini অ্যাপ ও Google অ্যাপে আসে। Google-এর প্ল্যানে যা যা আছে:")
        foot = (f"Google-এর অফিসিয়াল প্ল্যান পেজ থেকে {b['checked']} তারিখে মিলিয়ে দেখা। ফিচার, লিমিট ও দেশভেদে প্রাপ্যতা "
                f"Google বদলাতে পারে, আর কিছু ফিচার শুধু ১৮+ বয়সীদের জন্য। {src}Google-এ বর্তমান তালিকা দেখুন ↗</a>")
    else:
        h = f"What you get with {esc(name)}"
        lead = (f"At {bdt}, {esc(name)} is activated on <b>your own Gmail account</b>, so every feature shows up in your own "
                "Gemini app and Google apps. Google's plan includes:")
        foot = (f"Checked against Google's official plan page on {b['checked']}. Google can change features, limits and "
                f"country availability, and some features are 18+ only. {src}See Google's current list ↗</a>")
    rows = b["bn" if bn else "en"]
    lis = "".join(f"<li>{r}</li>" for r in rows)
    return (f'<section data-sos="{MARK}" class="valuebox benefits mt3"><h2>{h}</h2><p>{lead}</p>'
            f'<ul>{lis}</ul><p class="bfoot">{foot}</p></section>')



def compare_table(plans: list[dict], bn: bool) -> str:
    if len(plans) < 2:
        return ""
    head = ("প্ল্যান", "দাম", "অ্যাক্সেস", "কার জন্য") if bn else ("Plan", "Price", "Access", "Good for")
    body = []
    for pl in sorted(plans, key=lambda x: x["bdt"]):
        k = pl.get("type") or pl.get("access_type") or ""
        good = GOOD_FOR.get(k, ("Confirm on WhatsApp", "WhatsApp-এ জেনে নিন"))[1 if bn else 0]
        body.append(f'<tr><td data-l="{head[0]}">{esc(pl.get("label", "Plan"))}</td><td data-l="{head[1]}"><b>{price_text(pl, bn)}</b></td>'
                    f'<td data-l="{head[2]}">{access_text(pl, bn)}</td><td data-l="{head[3]}">{esc(good)}</td></tr>')
    h2 = "প্ল্যান তুলনা" if bn else "Compare plans"
    ths = "".join(f"<th>{h}</th>" for h in head)
    return (f'<section data-sos="{MARK}" class="mt3"><h2 style="font-size:22px">{h2}</h2><div class="tblwrap">'
            f'<table class="plancmp"><thead><tr>{ths}</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>')


def order_steps(bn: bool) -> str:
    if bn:
        steps = [("প্ল্যান বাছুন", "উপরের তালিকা থেকে অ্যাক্সেস টাইপ দেখে প্ল্যান বেছে নিন।"),
                 ("WhatsApp-এ নিশ্চিত করুন", "আমরা প্ল্যান, অ্যাক্সেস পদ্ধতি ও সময় লিখিতভাবে জানাই।"),
                 ("টাকায় পেমেন্ট", "বিকাশ, নগদ বা রকেটে পাঠিয়ে ট্রানজ্যাকশন আইডি দিন।"),
                 ("অ্যাক্টিভেশন ও সাপোর্ট", "অ্যাক্টিভেশনের পর WhatsApp-এ মানুষের সাপোর্ট পাবেন।")]
        h2 = "কীভাবে অর্ডার হয়"
    else:
        steps = [("Pick a plan", "Choose a plan above; each one shows its access type."),
                 ("Confirm on WhatsApp", "We confirm the plan, access method and timing in writing."),
                 ("Pay in taka", "Send by bKash, Nagad or Rocket and share the transaction ID."),
                 ("Activation and support", "After activation, a real person supports you on WhatsApp.")]
        h2 = "How ordering works"
    lis = "".join(f"<li><b>{esc(a)}</b>{esc(b)}</li>" for a, b in steps)
    return f'<section data-sos="{MARK}" class="mt3"><h2 style="font-size:22px">{h2}</h2><ol class="osteps">{lis}</ol></section>'


def related_cards(block: str, products: dict, priced_ids: set, bn: bool) -> str | None:
    ids = re.findall(r'<li><a href="(?:\.\./p/)?([a-z0-9-]+)(?:\.html)?">', block)
    cards = []
    for rid in ids:
        rp = products.get(rid)
        if not rp:
            continue
        name = clean_name(rp.get("name", rid))
        cat = rp.get("category", "")
        # Product pages may only show their own approved prices inside <main>
        # (audit_commercial_truth_v2), so related cards carry no amount.
        if rid in priced_ids:
            n = len(rp["plans"])
            price = (f"{n}টি প্ল্যান দেখুন →" if bn else f"See {n} plan{'s' if n > 1 else ''} →")
        else:
            price = "দাম জেনে নিন →" if bn else "Ask for price →"
        cards.append(f'<a class="pcard" href="../p/{rid}">{tile(name, cat)}<h3>{esc(name)}</h3>'
                     f'<span class="from">{esc(cat)}</span><div class="from" style="color:var(--green2);font-weight:800">{price}</div></a>')
    if not cards:
        return None
    return f'<div class="relgrid" data-sos-rel="{MARK}">{"".join(cards)}</div>'


def buybar(plans: list[dict], wa_href: str, bn: bool) -> str:
    low = min(int(pl["bdt"]) for pl in plans)
    many = len(plans) > 1
    if bn:
        price = f"{money(low)}{' থেকে' if many else ''}<small>বিকাশ · নগদ · রকেট</small>"
        a, b = "প্ল্যান", "WhatsApp-এ অর্ডার"
    else:
        price = f"{'From ' if many else ''}{money(low)}<small>bKash · Nagad · Rocket</small>"
        a, b = "Plans", "Order on WhatsApp"
    return (f'<div class="buybar" data-sos="{MARK}"><span class="bb-price">{price}</span>'
            f'<a class="btn btn-ghost" href="#plans">{a}</a>'
            f'<a class="btn btn-primary" href="{wa_href}" target="_blank" rel="noopener">{b}</a></div>')


def upgrade_product(text: str, p: dict, products: dict, priced_ids: set, ref: dict, date: str, bn: bool) -> str:
    text = BLOCK.sub("", text)
    plans = p["plans"]
    name = clean_name(p.get("name", p["id"]))
    prefix = "../.."
    # 1. hero emoji -> monogram tile
    text, n = re.subn(r'<span style="font-size:46px">[^<]*</span>', tile(name, p.get("category", "")), text, count=1)
    # 2. plans anchor for the sticky bar
    text = text.replace('<div class="grid mt2" style="grid-template-columns:1fr;gap:10px">',
                        '<div class="grid mt2" id="plans" style="grid-template-columns:1fr;gap:10px">', 1)
    # 3. key facts + compare + steps right after the plan cards (before caveat / access copy)
    access_h = "অ্যাক্সেস আগে নিশ্চিত করুন" if bn else "Confirm the access model before payment"
    anchor = f'<section class="mt3"><h2 style="font-size:22px">{access_h}</h2>'
    i = text.find(anchor)
    if i < 0:
        raise SystemExit(f"[conversion-upgrade] {p['id']} ({'bn' if bn else 'en'}): access section anchor not found")
    # keep a caveat notice (if any) directly under the plans
    j = text.rfind('<div class="notice mt2">', 0, i)
    k = text.rfind('id="plans"', 0, i)
    insert_at = text.find("</div>", j) + 6 if j > k else i
    if insert_at < i:
        insert_at = i
    block = key_facts(p, plans, ref, date, bn, prefix) + value_box(p, plans, ref, bn) + benefits_box(p, plans, bn) + compare_table(plans, bn) + order_steps(bn)
    text = text[:insert_at] + block + text[insert_at:]
    # 4. related list -> cards
    rel_h = "সম্পর্কিত টুল" if bn else "Related tools"
    m = re.search(rf'(<h2[^>]*>{re.escape(rel_h)}</h2>)(<ul>.*?</ul>)', text, re.S)
    if m:
        cards = related_cards(m.group(2), products, priced_ids, bn)
        if cards:
            text = text[:m.start(2)] + cards + text[m.end(2):]
    # 5. sticky buy bar reusing the existing WhatsApp order prefill
    wa = re.search(r'<a class="fab fab-wa" href="([^"]+)"', text)
    if wa:
        text = text.replace("<body>", '<body class="has-buybar">', 1)
        text = text.replace("</main>", "</main>" + buybar(plans, wa.group(1), bn), 1)
    return text


# ------------------------------------------------------------------ home

HOME_FAQ = {
    False: [
        ("How do I pay for a subscription in Bangladesh?",
         "Pay in taka with bKash, Nagad or Rocket. You do not need an international card. Share the transaction ID on WhatsApp or at checkout so we can match your payment."),
        ("What is the difference between a shared and a personal plan?",
         "On a shared plan several people use one account, so others may see your activity and the provider's terms may restrict sharing. A personal (customer-specific) plan is for your own use, work and private data. Every plan on SaveOnSub shows which one it is."),
        ("How do I order?",
         "Pick a plan and add it to the cart, or message us on WhatsApp at +880 1305 869242. We confirm the plan, access method and timing in writing before you pay."),
        ("What if my subscription stops working?",
         "Message us on WhatsApp with your order ID. Support and refunds follow the written support terms and refund policy linked at the bottom of every page."),
        ("Is SaveOnSub an official partner of these brands?",
         "No. SaveOnSub is an independent Bangladeshi subscription and payment assistance store. Product names belong to their owners, and we only state a provider relationship when it is evidenced."),
    ],
    True: [
        ("বাংলাদেশ থেকে সাবস্ক্রিপশনের পেমেন্ট কীভাবে করব?",
         "বিকাশ, নগদ বা রকেটে টাকায় পেমেন্ট করুন; আন্তর্জাতিক কার্ড লাগবে না। পেমেন্ট মেলাতে WhatsApp বা চেকআউটে ট্রানজ্যাকশন আইডি দিন।"),
        ("শেয়ার্ড আর পার্সোনাল প্ল্যানের পার্থক্য কী?",
         "শেয়ার্ড প্ল্যানে একাধিক ব্যবহারকারী একই অ্যাকাউন্ট ব্যবহার করেন, তাই অন্যরা আপনার অ্যাক্টিভিটি দেখতে পারেন এবং প্রোভাইডারের নিয়মে ঝুঁকি থাকে। পার্সোনাল (কাস্টমার-নির্দিষ্ট) প্ল্যান আপনার নিজের, কাজ ও গোপন তথ্যের জন্য। প্রতিটি প্ল্যানে কোনটি তা লেখা থাকে।"),
        ("কীভাবে অর্ডার করব?",
         "প্ল্যান কার্টে যোগ করুন, অথবা WhatsApp-এ +880 1305 869242 নম্বরে মেসেজ দিন। পেমেন্টের আগে প্ল্যান, অ্যাক্সেস পদ্ধতি ও সময় লিখিতভাবে নিশ্চিত করা হয়।"),
        ("সাবস্ক্রিপশন কাজ না করলে কী হবে?",
         "অর্ডার আইডিসহ WhatsApp-এ জানান। সাপোর্ট ও রিফান্ড প্রতিটি পেজের নিচে দেওয়া লিখিত সাপোর্ট শর্ত ও রিফান্ড নীতি অনুযায়ী হয়।"),
        ("SaveOnSub কি এই ব্র্যান্ডগুলোর অফিসিয়াল পার্টনার?",
         "না। SaveOnSub একটি স্বাধীন বাংলাদেশি সাবস্ক্রিপশন ও পেমেন্ট সহায়তা স্টোর। পণ্যের নাম তাদের মালিকদের; প্রমাণ থাকলেই কেবল প্রোভাইডার সম্পর্কের কথা বলা হয়।"),
    ],
}


def home_sections(bn: bool, count: int) -> str:
    if bn:
        why = [("৳", "টাকায় পেমেন্ট", "বিকাশ, নগদ বা রকেট — আন্তর্জাতিক কার্ড লাগবে না।"),
               ("🏷️", "অ্যাক্সেস টাইপ লেখা", "শেয়ার্ড, পার্সোনাল, টিম বা বান্ডেল — পেমেন্টের আগেই দেখুন।"),
               ("💬", "মানুষের সাপোর্ট", "WhatsApp-এ বাংলায় কথা বলুন, অর্ডারের আগে ও পরে।"),
               ("📄", "লিখিত নীতি", "রিফান্ড নীতি ও সাপোর্ট শর্ত সবার জন্য প্রকাশিত।")]
        h_why, h_faq, pill = "কেন SaveOnSub", "সাধারণ প্রশ্ন", "কেন আমরা"
    else:
        why = [("৳", "Pay in taka", "bKash, Nagad or Rocket. No international card needed."),
               ("🏷️", "Access type on every plan", "Shared, personal, team or bundle, shown before you pay."),
               ("💬", "Real human support", "Chat with us on WhatsApp in Bangla or English, before and after you order."),
               ("📄", "Written policies", "Refund policy and support terms are public on every page.")]
        h_why, h_faq, pill = "Why order from SaveOnSub", "Common questions", "WHY SAVEONSUB"
    tiles = "".join(f'<div><span style="font-size:24px">{i}</span><b>{esc(a)}</b><p>{esc(b)}</p></div>' for i, a, b in why)
    pay = "".join(f"<span>{x}</span>" for x in (["বিকাশ", "নগদ", "রকেট"] if bn else ["bKash", "Nagad", "Rocket"]))
    faqs = HOME_FAQ[bn]
    det = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    return (f'<section data-sos="{MARK}"><div class="wrap"><span class="pill">{pill}</span><h2>{h_why}</h2>'
            f'<div class="whyg mt3">{tiles}</div><div class="payrow">{pay}</div></div></section>'
            f'<section data-sos="{MARK}" class="homefaq" style="background:var(--bg2);border-block:1px solid var(--line)">'
            f'<div class="wrap" style="max-width:900px"><h2>{h_faq}</h2>{det}</div></section>'
            f'<script type="application/ld+json" data-sos="{MARK}">{json.dumps(ld, ensure_ascii=False)}</script>')


def upgrade_home(text: str, products: dict, priced_ids: set, bn: bool) -> str:
    text = BLOCK.sub("", text)
    count = len(priced_ids)
    if not bn:
        text = text.replace(
            "<span>🏷️ <b>Every plan clearly labeled</b>: Customer-specific · Team / Workspace · Bundle · Setup / Service</span>",
            "<span>🏷️ <b>Every plan labeled</b>: Shared · Personal · Team · Bundle</span>")
        text = text.replace(
            "<h1>Choose the right subscription. Pay in BDT. Know the access model first.</h1>",
            "<h1>ChatGPT, Claude, Canva and more. Pay in taka.</h1>")
        text = re.sub(
            r'<p class="sub">Compare AI, productivity, streaming and other subscriptions\..*?</p>',
            f'<p class="sub">{count} AI, design, streaming and productivity subscriptions with fixed prices in BDT. '
            'Pay by bKash, Nagad or Rocket, see whether each plan is shared or personal before you pay, '
            'and get help from a real person on WhatsApp.</p>', text, count=1, flags=re.S)
    # hero card emoji -> monogram tiles (name comes from the card's own <h3>)
    def card(m: re.Match) -> str:
        nm = html.unescape(m.group(2))
        pid = m.group(3)
        cat = (products.get(pid) or {}).get("category", "")
        return m.group(0).replace(m.group(1), tile(nm, cat), 1)
    text = re.sub(r'<div class="pcard">(<span class="icon">[^<]*</span>)<h3>([^<]+)</h3>.*?href="(?:\.\./)?(?:bn/)?p/([a-z0-9-]+)',
                  card, text, flags=re.S)
    # why + FAQ before the footer
    sections = home_sections(bn, count)
    i = text.find("<footer")
    if i < 0:
        raise SystemExit("[conversion-upgrade] home footer not found")
    text = text[:i] + sections + text[i:]
    return text


# ------------------------------------------------------------------ main

def check_text(rel: str, text: str) -> list[str]:
    errs = []
    for m in BLOCK.finditer(text):
        body = re.sub(r"<[^>]+>", " ", m.group(0))
        hit = FORBIDDEN.search(body)
        if hit:
            errs.append(f"{rel}: forbidden claim '{hit.group(0)}' in upgrade block")
    return errs


def main(argv: list[str]) -> int:
    check = "--check" in argv
    products = load_catalog(SITE)
    pr = priced(products)
    priced_ids = set(pr)
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    refs = official_refs()
    errors: list[str] = []
    pages = 0
    for pid, p in sorted(pr.items()):
        for bn in (False, True):
            path = SITE / ("bn/p" if bn else "p") / f"{pid}.html"
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(SITE))
            if check:
                if f'data-sos="{MARK}"' not in text:
                    errors.append(f"{rel}: upgrade block missing")
            else:
                text = upgrade_product(text, p, products, priced_ids, refs.get(pid, {}), approved_on(pid, policy), bn)
                path.write_text(text, encoding="utf-8")
            errors += check_text(rel, text)
            pages += 1
    for name, bn in (("index.html", False), ("bn.html", True)):
        path = SITE / name
        text = path.read_text(encoding="utf-8")
        if not check:
            text = upgrade_home(text, products, priced_ids, bn)
            path.write_text(text, encoding="utf-8")
        if f'data-sos="{MARK}"' not in text:
            errors.append(f"{name}: home upgrade block missing")
        errors += check_text(name, text)
    if errors:
        print("[conversion-upgrade] FAIL\n  " + "\n  ".join(errors[:20]))
        return 1
    print(f"[conversion-upgrade] PASS — {pages} product pages + 2 home pages upgraded; no forbidden claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
