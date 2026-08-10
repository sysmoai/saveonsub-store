#!/usr/bin/env python3
"""Build a strict SAVEONSUB v3 public-information artifact into _public_v3/.

This is an additive, static/Python build that preserves existing public product
and category URLs while commerce authority is unresolved. It deliberately emits:
- no SAVEONSUB selling prices;
- no Offer/AggregateOffer schema;
- no cart/checkout/payment controls;
- no WhatsApp destination;
- no unsupported order/review/bestseller claims;
- no raw catalog.js;
- no protected authority/control files.

Dedicated plan pages are generated but default to noindex,follow until their
content/authority is independently mature enough for indexing.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import shutil
import xml.etree.ElementTree as ET
from collections import Counter

from catalog_model import load_catalog
from routes_v3 import DOMAIN, strip_price_tokens
from site_config import SUPPORT_EMAIL, support_mailto

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "_public_v3"
ASSETS = DEST / "assets"

CATEGORY_ICONS = {
    "AI Assistants": "🤖",
    "AI Image & Design": "🎨",
    "AI Video": "🎬",
    "AI Voice & Music": "🎙️",
    "AI Code & Dev": "💻",
    "AI Writing": "✍️",
    "Workspace & Productivity": "🗂️",
    "Entertainment": "🍿",
    "Education & Career": "🎓",
    "VPN & Security": "🔒",
    "Bundles": "🎁",
    "Gaming": "🎮",
    "BD Lifestyle": "🇧🇩",
}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def safe_label(value: object, language: str) -> str:
    clean = strip_price_tokens(value)
    return clean or ("প্ল্যান" if language == "bn" else "Plan")


def state_copy(state: str, language: str) -> tuple[str, str]:
    if language == "bn":
        mapping = {
            "allowed": ("যাচাইকৃত", "এই প্ল্যানের প্রোভাইডার যোগ্যতা যাচাই করা হয়েছে; বাণিজ্যিক অ্যাক্টিভেশন এখনও আলাদা অনুমোদনের বিষয়।"),
            "direct_provider_only": ("অফিসিয়াল প্রোভাইডার", "এই প্ল্যানের জন্য অফিসিয়াল প্রোভাইডারের পথ ব্যবহার করুন। SAVEONSUB এখানে তথ্য ও তুলনা দেয়।"),
            "blocked": ("SAVEONSUB-এ উপলভ্য নয়", "বর্তমান প্রোভাইডার/নীতিগত অবস্থায় এই প্ল্যানটি SAVEONSUB commerce-এ দেওয়া হচ্ছে না।"),
            "unknown": ("যাচাই বাকি", "প্রোভাইডার ও বাণিজ্যিক যোগ্যতা যাচাই না হওয়া পর্যন্ত এই প্ল্যানটি তথ্য হিসেবে দেখানো হচ্ছে।"),
        }
    else:
        mapping = {
            "allowed": ("Provider-verified", "Provider eligibility has been verified; commercial activation remains separately authority-gated."),
            "direct_provider_only": ("Official provider path", "Use the official provider for this plan. SAVEONSUB provides information and comparison only."),
            "blocked": ("Not offered by SAVEONSUB", "This plan is not offered as SAVEONSUB commerce under the current provider/policy state."),
            "unknown": ("Verification pending", "This plan is informational until provider and commercial eligibility are verified."),
        }
    return mapping.get(state, mapping["unknown"])


def head(title: str, desc: str, canonical: str, language: str, alternate: str, robots: str = "index,follow", page_type: str = "website") -> str:
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{esc(robots)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="alternate" hreflang="{'bn-bd' if language == 'bn' else 'en-bd'}" href="{esc(canonical)}">
<link rel="alternate" hreflang="{'en-bd' if language == 'bn' else 'bn-bd'}" href="{esc(alternate)}">
<link rel="alternate" hreflang="x-default" href="{esc(canonical if language == 'en' else alternate)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{esc(page_type)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="SAVEONSUB">
<meta property="og:locale" content="{'bn_BD' if language == 'bn' else 'en_BD'}">
<meta name="theme-color" content="#06181a">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="/assets/site.webmanifest">
<link rel="stylesheet" href="/assets/style.css">"""


def nav(language: str) -> str:
    if language == "bn":
        return f"""<nav><div class="wrap navin"><a class="logo" href="/bn.html">SAVE<em>ON</em>SUB</a>
<div class="navlinks"><a href="/all.html">সব সাবস্ক্রিপশন</a><a href="/bn.html#categories">ক্যাটাগরি</a><a href="/faq.html">প্রশ্নোত্তর</a><a href="/about.html">আমাদের সম্পর্কে</a></div>
<div class="navright"><a class="navtrack" href="{esc(support_mailto('SAVEONSUB সহায়তা'))}">✉ সহায়তা</a><a href="/" class="navtrack">EN</a><button class="hamb" onclick="navToggle()" aria-label="মেনু">☰</button></div></div></nav>"""
    return f"""<nav><div class="wrap navin"><a class="logo" href="/">SAVE<em>ON</em>SUB</a>
<div class="navlinks"><a href="/all.html">Subscriptions</a><a href="/#categories">Categories</a><a href="/faq.html">FAQ</a><a href="/about.html">About</a></div>
<div class="navright"><a class="navtrack" href="{esc(support_mailto())}">✉ Support</a><a href="/bn.html" class="navtrack">বাংলা</a><button class="hamb" onclick="navToggle()" aria-label="Menu">☰</button></div></div></nav>"""


def footer(language: str) -> str:
    if language == "bn":
        return f"""<footer><div class="wrap"><div class="fcols"><div><span class="logo">SAVE<em>ON</em>SUB</span><p>বাংলাদেশ-কেন্দ্রিক ডিজিটাল সাবস্ক্রিপশন তথ্য, তুলনা ও নিরাপদ সিদ্ধান্ত সহায়তা।</p></div><div><b>ব্রাউজ</b><a href="/all.html">সব সাবস্ক্রিপশন</a><a href="/bn.html#categories">ক্যাটাগরি</a></div><div><b>সহায়তা</b><a href="/faq.html">প্রশ্নোত্তর</a><a href="/contact.html">যোগাযোগ</a></div><div><b>নীতি</b><a href="/privacy.html">প্রাইভেসি</a><a href="/terms.html">শর্তাবলি</a></div><div><b>যোগাযোগ</b><a href="mailto:{esc(SUPPORT_EMAIL)}">{esc(SUPPORT_EMAIL)}</a></div></div><p class="fine">© 2026 SAVEONSUB। ট্রেডমার্ক তাদের নিজ নিজ মালিকের। যাচাই ছাড়া কোনো প্রোভাইডার পার্টনারশিপ বা অনুমোদন দাবি করা হয় না।</p></div></footer>"""
    return f"""<footer><div class="wrap"><div class="fcols"><div><span class="logo">SAVE<em>ON</em>SUB</span><p>Bangladesh-first digital subscription information, comparison and decision support.</p></div><div><b>Browse</b><a href="/all.html">All subscriptions</a><a href="/#categories">Categories</a></div><div><b>Help</b><a href="/faq.html">FAQ</a><a href="/contact.html">Contact</a></div><div><b>Policies</b><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a></div><div><b>Contact</b><a href="mailto:{esc(SUPPORT_EMAIL)}">{esc(SUPPORT_EMAIL)}</a></div></div><p class="fine">© 2026 SAVEONSUB. Product names and trademarks belong to their respective owners. No provider partnership or authorization is implied unless explicitly verified.</p></div></footer>"""


def shell(body: str, *, title: str, desc: str, canonical: str, language: str, alternate: str, robots: str = "index,follow", page_type: str = "website") -> str:
    return f"""<!DOCTYPE html><html lang="{language}"><head>{head(title, desc, canonical, language, alternate, robots, page_type)}</head><body><a class="skip" href="#main">{'মূল কন্টেন্টে যান' if language == 'bn' else 'Skip to content'}</a>{nav(language)}<main id="main">{body}</main>{footer(language)}<script src="/assets/app.js"></script></body></html>"""


def product_card(product: dict, language: str, prefix: str = "") -> str:
    pid = product["id"]
    name = product.get("name", pid).replace("🎁 ", "")
    category = product.get("category", "")
    icon = product.get("icon", "◈")
    path = f"/bn/p/{pid}.html" if language == "bn" else f"/p/{pid}.html"
    state = product.get("commercial_state_v3", "unknown")
    badge, _ = state_copy(state, language)
    detail = "বিস্তারিত" if language == "bn" else "View details"
    return f"""<article class="pcard"><span class="icon">{esc(icon)}</span><h3>{esc(name)}</h3><span class="cat">{esc(category)}</span><span class="tos official">{esc(badge)}</span><div class="ctas"><a class="btn btn-primary btn-sm" href="{path}">{detail} →</a></div></article>"""


def product_page(product: dict, language: str) -> str:
    bn = language == "bn"
    pid = product["id"]
    name = product.get("name", pid).replace("🎁 ", "")
    category = product.get("category", "")
    icon = product.get("icon", "◈")
    canonical = f"{DOMAIN}/bn/p/{pid}.html" if bn else f"{DOMAIN}/p/{pid}.html"
    alternate = f"{DOMAIN}/p/{pid}.html" if bn else f"{DOMAIN}/bn/p/{pid}.html"
    pstate = product.get("commercial_state_v3", "unknown")
    pbadge, pcopy = state_copy(pstate, language)
    title = f"{name} — {'বাংলাদেশ গাইড' if bn else 'Bangladesh Guide'} | SAVEONSUB"
    desc = (f"{name} সম্পর্কে প্ল্যান, প্রোভাইডার স্ট্যাটাস ও অফিসিয়াল সোর্স দেখুন। SAVEONSUB যাচাই ছাড়া দাম বা ক্রয় সুবিধা প্রকাশ করে না।" if bn else f"Explore {name} plans, provider status and official source for Bangladesh. SAVEONSUB does not publish a price or purchase control without verification.")

    plans = []
    for plan in product.get("plans", []):
        label = safe_label(plan.get("label"), language)
        state = plan.get("commercial_state_v3", "unknown")
        badge, copy = state_copy(state, language)
        href = f"/{plan['routes_v3'][language]}"
        plans.append(f"""<article class="tcard"><h3>{esc(label)}</h3><p class="sub">{esc(plan.get('duration', ''))}</p><p><span class="tos official">{esc(badge)}</span></p><p class="sub">{esc(copy)}</p><a class="btn btn-ghost btn-sm" href="{href}">{'প্ল্যান বিস্তারিত' if bn else 'Plan details'} →</a></article>""")

    official = ""
    if product.get("official_url"):
        official = f'<a class="btn btn-primary" href="{esc(product["official_url"])}" target="_blank" rel="noopener nofollow">{"অফিসিয়াল প্রোভাইডার ↗" if bn else "Official provider ↗"}</a>'

    faq_items = []
    for faq in product.get("faq", [])[:3]:
        q = strip_price_tokens(faq.get("q", ""))
        a = strip_price_tokens(faq.get("a", ""))
        # Legacy FAQ copy can describe shared/resale mechanics. Do not publish it
        # in L1 unless it is generic and free of known commerce-risk vocabulary.
        if re.search(r"shared|seat|warranty|order|buy|price|৳|discount|resell", f"{q} {a}", re.I):
            continue
        faq_items.append(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>")

    body = f"""<div class="wrap" style="max-width:980px;padding-top:30px;padding-bottom:50px"><div class="crumbs"><a href="{'/bn.html' if bn else '/'}">{'হোম' if bn else 'Home'}</a> › <a href="{'/bn/c/' if bn else '/c/'}{slug(category)}.html">{esc(category)}</a> › {esc(name)}</div><div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><span style="font-size:54px">{esc(icon)}</span><div><span class="cat">{esc(category)}</span><h1>{esc(name)}</h1></div></div><div class="notice mt2"><b>{esc(pbadge)}</b><p>{esc(pcopy)}</p>{official}</div><section class="mt3"><h2>{'প্ল্যানসমূহ' if bn else 'Plans'}</h2><p class="sub">{'প্রতিটি প্ল্যানের নিজস্ব পেজ আছে। দাম ও ক্রয় কন্ট্রোল শুধুমাত্র আলাদা অনুমোদনের পরে দেখানো হবে।' if bn else 'Every plan has a dedicated page. Price and purchase controls appear only after separate authority verification.'}</p><div class="grid g3 mt2">{''.join(plans)}</div></section>{f'<section class="mt3"><h2>{"সাধারণ প্রশ্ন" if bn else "Common questions"}</h2>{"".join(faq_items)}</section>' if faq_items else ''}<section class="mt3"><div class="notice">{'ভুল বা পুরোনো তথ্য দেখলে আমাদের ইমেইল করুন।' if bn else 'Found outdated or incorrect information? Email us so we can verify and correct it.'} <a href="{esc(support_mailto('SAVEONSUB product correction'))}">{esc(SUPPORT_EMAIL)}</a></div></section></div>"""
    return shell(body, title=title, desc=desc, canonical=canonical, language="bn" if bn else "en", alternate=alternate, page_type="product")


def plan_page(product: dict, plan: dict, language: str) -> str:
    bn = language == "bn"
    pid = product["id"]
    name = product.get("name", pid).replace("🎁 ", "")
    label = safe_label(plan.get("label"), language)
    route = plan["routes_v3"][language]
    canonical = f"{DOMAIN}/{route}"
    alternate = f"{DOMAIN}/{plan['routes_v3']['en' if bn else 'bn']}"
    state = plan.get("commercial_state_v3", "unknown")
    badge, copy = state_copy(state, language)
    title = f"{name} — {label} | SAVEONSUB"
    desc = (f"{name} {label} প্ল্যানের সময়কাল, প্রোভাইডার স্ট্যাটাস ও অফিসিয়াল সোর্স।" if bn else f"Dedicated information page for the {name} {label} plan, including term, provider status and official source.")
    official = ""
    if product.get("official_url"):
        official = f'<a class="btn btn-primary" href="{esc(product["official_url"])}" target="_blank" rel="noopener nofollow">{"অফিসিয়াল প্রোভাইডার ↗" if bn else "Official provider ↗"}</a>'
    parent = f"/bn/p/{pid}.html" if bn else f"/p/{pid}.html"
    body = f"""<div class="wrap" style="max-width:860px;padding-top:30px;padding-bottom:50px"><div class="crumbs"><a href="{parent}">{esc(name)}</a> › {esc(label)}</div><span class="pill">{esc(product.get('category',''))}</span><h1>{esc(name)}</h1><h2>{esc(label)}</h2><div class="notice mt2"><b>{esc(badge)}</b><p>{esc(copy)}</p></div><div class="tbl mt3"><table><tr><th>{'ফিল্ড' if bn else 'Field'}</th><th>{'তথ্য' if bn else 'Information'}</th></tr><tr><td>{'প্ল্যান আইডি' if bn else 'Plan ID'}</td><td><code>{esc(plan['plan_id_v3'])}</code></td></tr><tr><td>{'সময়কাল' if bn else 'Duration'}</td><td>{esc(plan.get('duration',''))}</td></tr><tr><td>{'ডেলিভারি শ্রেণি' if bn else 'Delivery class'}</td><td>{esc(plan.get('sla','verification pending'))}</td></tr></table></div><p class="mt3">{official}</p><div class="notice mt3">{'এই পেজে কোনো SAVEONSUB বিক্রয় মূল্য বা পেমেন্ট নির্দেশনা নেই।' if bn else 'This page contains no SAVEONSUB selling price or payment instruction.'}</div></div>"""
    return shell(body, title=title, desc=desc, canonical=canonical, language="bn" if bn else "en", alternate=alternate, robots="noindex,follow", page_type="product")


def category_page(category: str, products: list[dict], language: str) -> str:
    bn = language == "bn"
    cs = slug(category)
    canonical = f"{DOMAIN}/bn/c/{cs}.html" if bn else f"{DOMAIN}/c/{cs}.html"
    alternate = f"{DOMAIN}/c/{cs}.html" if bn else f"{DOMAIN}/bn/c/{cs}.html"
    title = f"{category} — {'বাংলাদেশ' if bn else 'Bangladesh'} | SAVEONSUB"
    desc = (f"{category} ক্যাটাগরির {len(products)}টি ডিজিটাল সাবস্ক্রিপশন তথ্য ও প্রোভাইডার স্ট্যাটাস দেখুন।" if bn else f"Browse {len(products)} {category} subscriptions with provider-status information for Bangladesh.")
    cards = "".join(product_card(p, language) for p in products)
    body = f"""<div class="wrap" style="padding-top:30px;padding-bottom:50px"><span class="pill">{esc(CATEGORY_ICONS.get(category,'◈'))} {esc(category)}</span><h1>{esc(category)}</h1><p class="sub">{esc(desc)}</p><div class="grid g3 mt3">{cards}</div></div>"""
    return shell(body, title=title, desc=desc, canonical=canonical, language="bn" if bn else "en", alternate=alternate)


def home(catalog: dict, language: str) -> str:
    bn = language == "bn"
    products = catalog.get("products", [])
    cats = catalog.get("categories", [])
    canonical = f"{DOMAIN}/bn.html" if bn else f"{DOMAIN}/"
    alternate = f"{DOMAIN}/" if bn else f"{DOMAIN}/bn.html"
    title = "SAVEONSUB — বাংলাদেশে ডিজিটাল সাবস্ক্রিপশন গাইড" if bn else "SAVEONSUB — Digital Subscription Guide for Bangladesh"
    desc = (f"বাংলাদেশের জন্য {len(products)}টি ডিজিটাল সাবস্ক্রিপশন, {len(cats)}টি ক্যাটাগরি, বাংলা/ইংরেজি গাইড ও প্রোভাইডার যাচাই।" if bn else f"Explore {len(products)} digital subscriptions across {len(cats)} categories with English/Bangla guidance and provider-status verification for Bangladesh.")
    cat_counts = Counter(p.get("category") for p in products)
    cat_html = "".join(f'<a class="cattile" href="{("/bn/c/" if bn else "/c/")}{slug(c)}.html"><span class="icon">{esc(CATEGORY_ICONS.get(c,"◈"))}</span>{esc(c)}<span class="n">{cat_counts[c]} {"টি প্রোডাক্ট" if bn else "products"}</span></a>' for c in cats)
    featured = "".join(product_card(p, language) for p in products[:9])
    body = f"""<header class="hero"><div class="wrap"><span class="pill">🇧🇩 SAVEONSUB</span><h1>{'বাংলাদেশের ডিজিটাল সাবস্ক্রিপশন গাইড' if bn else 'Understand digital subscriptions before you choose.'}</h1><p class="sub">{esc(desc)}</p><div class="heroctas"><a class="btn btn-primary" href="/all.html">{'সব সাবস্ক্রিপশন দেখুন' if bn else 'Browse all subscriptions'} →</a><a class="btn btn-ghost" href="{esc(support_mailto('SAVEONSUB guidance'))}">✉ {'সহায়তা নিন' if bn else 'Ask for guidance'}</a></div><div class="notice mt3"><b>{'তথ্য-প্রথম মোড' if bn else 'Information-first mode'}</b><p>{'যাচাইকৃত দাম, পেমেন্ট গন্তব্য ও বাণিজ্যিক প্ল্যান আলাদাভাবে অনুমোদিত না হওয়া পর্যন্ত ক্রয় কন্ট্রোল বন্ধ থাকে।' if bn else 'Purchase controls remain disabled until plan eligibility, SAVEONSUB pricing and payment destinations are separately verified.'}</p></div></div></header><section id="categories"><div class="wrap"><h2>{'ক্যাটাগরি' if bn else 'Categories'}</h2><div class="grid g4 mt2">{cat_html}</div></div></section><section><div class="wrap"><h2>{'কিছু জনপ্রিয় টুল' if bn else 'Explore the catalog'}</h2><div class="grid g3 mt2">{featured}</div><p class="center mt3"><a class="btn btn-ghost" href="/all.html">{'সব ৭২টি দেখুন' if bn else 'See all 72'} →</a></p></div></section>"""
    return shell(body, title=title, desc=desc, canonical=canonical, language="bn" if bn else "en", alternate=alternate)


def all_page(catalog: dict) -> str:
    products = catalog.get("products", [])
    cards = "".join(product_card(p, "en") for p in products)
    body = f"""<div class="wrap" style="padding-top:30px;padding-bottom:50px"><span class="pill">FULL CATALOG</span><h1>All {len(products)} subscriptions</h1><p class="sub">Browse the full SAVEONSUB information catalog. Selling prices and payment controls are published only after separate verification.</p><div class="grid g3 mt3">{cards}</div></div>"""
    return shell(body, title=f"All {len(products)} Subscriptions | SAVEONSUB", desc=f"Browse {len(products)} digital subscription products across Bangladesh-focused categories.", canonical=f"{DOMAIN}/all.html", language="en", alternate=f"{DOMAIN}/all.html")


def simple_page(slug_name: str, title: str, desc: str, body_html: str) -> str:
    return shell(f'<div class="wrap" style="max-width:840px;padding-top:30px;padding-bottom:50px">{body_html}</div>', title=title, desc=desc, canonical=f"{DOMAIN}/{slug_name}.html", language="en", alternate=f"{DOMAIN}/{slug_name}.html")


def write(rel: str, content: str) -> None:
    path = DEST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_safe_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "app.js", "favicon.svg", "logo.svg", "icon-192.png", "icon-512.png", "apple-touch-icon.png"):
        src = ROOT / "assets" / name
        if src.is_file():
            shutil.copy2(src, ASSETS / name)
    manifest = {
        "name": "SAVEONSUB — Digital Subscription Guide for Bangladesh",
        "short_name": "SAVEONSUB",
        "description": "Bangladesh-first digital subscription information and comparison.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#06181a",
        "theme_color": "#06181a",
        "lang": "en-BD",
        "icons": [
            {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    (ASSETS / "site.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")


def build_sitemap(indexable: list[str]) -> None:
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}urlset")
    for url in indexable:
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = url
    ET.ElementTree(root).write(DEST / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def main() -> int:
    catalog = load_catalog()
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()
    copy_safe_assets()

    products = catalog.get("products", [])
    categories = catalog.get("categories", [])
    by_category = {c: [p for p in products if p.get("category") == c] for c in categories}
    indexable = [f"{DOMAIN}/", f"{DOMAIN}/bn.html", f"{DOMAIN}/all.html"]

    write("index.html", home(catalog, "en"))
    write("bn.html", home(catalog, "bn"))
    write("all.html", all_page(catalog))

    plan_count = 0
    for product in products:
        pid = product["id"]
        write(f"p/{pid}.html", product_page(product, "en"))
        write(f"bn/p/{pid}.html", product_page(product, "bn"))
        indexable += [f"{DOMAIN}/p/{pid}.html", f"{DOMAIN}/bn/p/{pid}.html"]
        for plan in product.get("plans", []):
            write(plan["routes_v3"]["en"], plan_page(product, plan, "en"))
            write(plan["routes_v3"]["bn"], plan_page(product, plan, "bn"))
            plan_count += 1

    for category, items in by_category.items():
        cs = slug(category)
        write(f"c/{cs}.html", category_page(category, items, "en"))
        write(f"bn/c/{cs}.html", category_page(category, items, "bn"))
        indexable += [f"{DOMAIN}/c/{cs}.html", f"{DOMAIN}/bn/c/{cs}.html"]

    info_note = "<div class=\"notice\"><b>Information-first release.</b><p>SAVEONSUB selling prices, payment destinations and order controls are not published until separately verified and authorized.</p></div>"
    write("about.html", simple_page("about", "About SAVEONSUB", "About SAVEONSUB's Bangladesh-first subscription information platform.", f"<span class=\"pill\">ABOUT</span><h1>About SAVEONSUB</h1><p class=\"sub\">SAVEONSUB organizes digital subscription information for Bangladesh in English and Bangla, with dedicated product and plan pages and links to official providers.</p>{info_note}"))
    write("contact.html", simple_page("contact", "Contact SAVEONSUB", "Contact SAVEONSUB support by email.", f"<span class=\"pill\">CONTACT</span><h1>Contact support</h1><p class=\"sub\">The currently verified public support channel is email.</p><p><a class=\"btn btn-primary\" href=\"mailto:{esc(SUPPORT_EMAIL)}\">{esc(SUPPORT_EMAIL)}</a></p><p class=\"fine\">A dedicated SAVEONSUB WhatsApp number and payment destinations will appear only after owner verification.</p>"))
    write("faq.html", simple_page("faq", "SAVEONSUB FAQ", "Frequently asked questions about SAVEONSUB's information-first subscription catalog.", f"<span class=\"pill\">FAQ</span><h1>Frequently asked questions</h1><details open><summary>Can I buy directly from this version of SAVEONSUB?</summary><p>No. Product and plan information is public, but order and payment controls remain disabled until eligibility, pricing and payment destinations are verified.</p></details><details><summary>Why are prices not shown?</summary><p>A public selling price is treated as an authority-controlled fact. SAVEONSUB will publish it only when the current approved price registry is populated.</p></details><details><summary>What if a plan is marked Official provider path?</summary><p>Use the official provider link on that product or plan page. SAVEONSUB is not offering that plan as reseller commerce in the current state.</p></details>"))
    write("privacy.html", simple_page("privacy", "Privacy | SAVEONSUB", "SAVEONSUB privacy information for the public information release.", "<span class=\"pill\">PRIVACY</span><h1>Privacy</h1><p>This public information release does not provide customer accounts, payment intake, or a server-side order form. Normal hosting/security logs may still be processed by the hosting platform. If you email support, your email provider and SAVEONSUB mailbox process the message you intentionally send.</p>"))
    write("terms.html", simple_page("terms", "Terms | SAVEONSUB", "Terms for SAVEONSUB's public subscription information catalog.", "<span class=\"pill\">TERMS</span><h1>Terms</h1><p>SAVEONSUB provides independent information and comparison about third-party digital services. Product names and trademarks belong to their respective owners. A listing does not imply partnership, distributor status, or authorization. No transaction is formed through this information-only release because checkout and payment collection are disabled.</p>"))
    write("404.html", simple_page("404", "Page not found | SAVEONSUB", "The requested SAVEONSUB page was not found.", "<h1>Page not found</h1><p><a class=\"btn btn-primary\" href=\"/all.html\">Browse subscriptions</a></p>"))
    indexable += [f"{DOMAIN}/about.html", f"{DOMAIN}/contact.html", f"{DOMAIN}/faq.html", f"{DOMAIN}/privacy.html", f"{DOMAIN}/terms.html"]

    build_sitemap(indexable)
    (DEST / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://saveonsub.com/sitemap.xml\n", encoding="utf-8")
    (DEST / "_redirects").write_text("/home / 301\n/shop /all.html 301\n/products /all.html 301\n/checkout.html /all.html 302\n/track.html /contact.html 302\n", encoding="utf-8")
    (DEST / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()\n  Strict-Transport-Security: max-age=63072000; includeSubDomains\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests\n\n/sw.js\n  Cache-Control: no-cache, no-store, must-revalidate\n\n/assets/*.js\n  Cache-Control: public, max-age=0, must-revalidate\n/assets/*.css\n  Cache-Control: public, max-age=0, must-revalidate\n", encoding="utf-8")
    (DEST / "sw.js").write_text("""const CACHE='sos-info-v3';const CORE=['/','/index.html','/all.html','/assets/style.css','/assets/app.js','/assets/favicon.svg'];self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);if(u.origin!==location.origin)return;if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));}return r;}).catch(()=>caches.match(e.request).then(r=>r||caches.match('/all.html'))));return;}e.respondWith(caches.match(e.request).then(c=>c||fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(CACHE).then(x=>x.put(e.request,cp));}return r;})));});""", encoding="utf-8")

    manifest = {
        "release_mode": "L1_PUBLIC_INFO_ONLY",
        "products": len(products),
        "plans": plan_count,
        "categories": len(categories),
        "public_prices": 0,
        "commerce_controls": 0,
        "payment_destinations": 0,
        "whatsapp_destinations": 0,
        "indexable_urls": len(indexable),
        "plan_pages_robots": "noindex,follow",
    }
    (DEST / "BUILD-MANIFEST.txt").write_text("\n".join(f"{k}={v}" for k,v in manifest.items()) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
