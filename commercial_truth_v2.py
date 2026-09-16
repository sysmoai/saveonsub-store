#!/usr/bin/env python3
"""Final customer-facing commercial truth projection for the staged site.

Runs after legacy provider cohorts so this stage has the final word on public
prices, access labels and unsupported operational claims. It preserves canonical
URLs and the approved brand assets while replacing stale AI commerce with the
2026-09-17 governed projection.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
CATALOG = ROOT / "catalog.json"
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
REVISION = "pricing-v2-2026-09-17"
WA = "8801305869242"


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def money(value: int) -> str:
    return f"৳{int(value):,}"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def remove_jsonld(html_text: str, needles: tuple[str, ...]) -> str:
    pat = re.compile(r'<script\s+type=["\']application/ld\+json["\'][^>]*>.*?</script>', re.I | re.S)
    def repl(match):
        block = match.group(0)
        low = block.lower()
        return "" if any(n.lower() in low for n in needles) else block
    return pat.sub(repl, html_text)


def set_title(text: str, title: str) -> str:
    if re.search(r"<title>.*?</title>", text, re.I | re.S):
        return re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", text, count=1, flags=re.I | re.S)
    return text.replace("</head>", f"<title>{esc(title)}</title>\n</head>", 1)


def set_meta(text: str, name: str, content: str, prop: bool = False) -> str:
    attr = "property" if prop else "name"
    pat = re.compile(rf'<meta\s+{attr}=["\']{re.escape(name)}["\'][^>]*>', re.I)
    tag = f'<meta {attr}="{esc(name)}" content="{esc(content)}">'
    if pat.search(text):
        return pat.sub(tag, text, count=1)
    return text.replace("</head>", tag + "\n</head>", 1)


def add_revision_meta(text: str) -> str:
    if 'name="saveonsub-commercial-revision"' in text:
        return text
    return text.replace(
        "</head>",
        f'<meta name="saveonsub-commercial-revision" content="{REVISION}">\n</head>',
        1,
    )


def sanitize_common(text: str) -> str:
    # Unsupported global merchandising/operations claims. Provider references
    # such as "official provider pricing" are intentionally not blanket-removed.
    replacements = {
        "Official · Personal · Shared": "Customer-specific · Team / Workspace · Bundle · Setup / Service",
        "official · personal · shared": "customer-specific · team/workspace · bundle · setup/service",
        "shared, personal or official": "customer-specific, team/workspace, bundle or setup/service",
        "SHARED · POLICY RISK": "PRICE / ACCESS REVIEW REQUIRED",
        "SHARED · WARRANTY COVERED": "ACCESS METHOD REQUIRES CONFIRMATION",
        "WARRANTY COVERED": "SUPPORT TERMS: CONFIRM BEFORE PAYMENT",
        "100% official": "clearly labeled",
        "100% Official": "Clearly labeled",
        "100% authentic": "clearly labeled",
        "100% Authentic": "Clearly labeled",
        "customer-owned": "customer-specific",
        "Customer-owned": "Customer-specific",
        "instant delivery": "delivery timing confirmed before payment",
        "Instant delivery": "Delivery timing confirmed before payment",
        "human replies in minutes": "human support is available through WhatsApp",
        "Human replies in minutes": "Human support is available through WhatsApp",
        "delivered to WhatsApp": "coordinated through WhatsApp",
        "Delivered to WhatsApp": "Coordinated through WhatsApp",
        "the only BD store": "a Bangladesh subscription store",
        "The only BD store": "A Bangladesh subscription store",
        "Bangladesh's honest subscription store": "Bangladesh subscription store",
        "BANGLADESH'S HONEST SUBSCRIPTION STORE": "BANGLADESH SUBSCRIPTION STORE",
        "বাজারের সবচেয়ে সস্তা": "বর্তমান মূল্য অর্ডারের আগে নিশ্চিত করুন",
        "ওয়ারেন্টি": "সাপোর্ট শর্ত",
        "ওয়ারেন্টি": "সাপোর্ট শর্ত",
        "warranty": "support terms",
        "Warranty": "Support terms",
        "bestseller": "listed product",
        "Bestseller": "Listed product",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"5\s*[–-]\s*15\s*(?:minutes?|mins?|min)\b", "timing confirmed before payment", text, flags=re.I)
    text = re.sub(r"৫\s*[–-]\s*১৫\s*মিনিট", "ডেলিভারি সময় অর্ডারের আগে নিশ্চিত করা হয়", text)
    text = re.sub(r"\b1\s*[–-]\s*2\s*(?:days?|দিন)\b", "timing confirmed before payment", text, flags=re.I)
    text = re.sub(r"\b1[- ]hour\s+replacement\b", "order-specific support terms", text, flags=re.I)
    text = re.sub(r"\b(?:7|30)[- ]day\s+(?:warranty|support terms)\b", "order-specific support terms", text, flags=re.I)
    text = re.sub(r"\bSAVE\s+\d{1,3}%\b", "CONFIRM ACCESS TYPE", text, flags=re.I)
    text = re.sub(r"\b\d[\d,]*\+?\s+orders\b", "customer orders", text, flags=re.I)
    text = re.sub(r"\b\d[\d,]*\+?\s+customers\b", "customers", text, flags=re.I)
    text = re.sub(r"<s>\s*৳[\d,]+(?:\.\d+)?\s*</s>", "", text, flags=re.I)
    text = re.sub(r"\b(?:our\s+)?#1\s+(?:seller|product)\b", "listed product", text, flags=re.I)
    text = text.replace("Pay-after-testing", "Order-specific payment/access confirmation")
    text = text.replace("pay-after-testing", "order-specific payment/access confirmation")
    return text


def js_args(*values) -> str:
    raw = ",".join(json.dumps(v, ensure_ascii=False) for v in values)
    return html.escape(raw, quote=True)


def access_label(plan: dict, bn: bool = False) -> str:
    kind = plan.get("type") or plan.get("access_type")
    if bn:
        return {"personal": "কাস্টমার-নির্দিষ্ট অ্যাক্সেস", "team": "টিম / ওয়ার্কস্পেস অ্যাক্সেস"}.get(kind, "অ্যাক্সেস পদ্ধতি নিশ্চিত করুন")
    return {"personal": "Customer-specific access", "team": "Team / Workspace access"}.get(kind, "Confirm access method")


def price_label(plan: dict, bn: bool = False) -> str:
    base = money(plan["bdt"])
    unit = plan.get("billing_unit", "month")
    if unit == "user/month":
        return f"{base} / {'ব্যবহারকারী / মাস' if bn else 'user / month'}"
    return f"{base} / {'মাস' if bn else 'month'}"


def product_main(product: dict, bn: bool) -> str:
    pid = product.get("id", "")
    name = product.get("name", pid)
    plans = product.get("plans") or []
    request_price = bool(product.get("request_price")) or not plans
    official_url = product.get("official_url") or product.get("url") or ""
    official_usd = product.get("official_usd")
    prefix = "../.." if bn else ".."
    home = f"{prefix}/bn.html" if bn else f"{prefix}/index.html"
    all_link = f"{prefix}/all.html"
    checkout = f"{prefix}/checkout.html"
    cat = esc(product.get("category", "Subscriptions"))
    icon = esc(product.get("emoji", "✨"))

    if bn:
        heading = f"{name} — বাংলাদেশে মূল্য ও অ্যাক্সেস"
        intro = "SaveOnSub-এর বর্তমান পাবলিক অফারটি নিচে দেখুন। পেমেন্টের আগে exact provider tier, access method, availability এবং order-specific support terms নিশ্চিত করুন।"
        access_heading = "অ্যাক্সেস আগে নিশ্চিত করুন"
        access_copy = "Credential-shared AI access-কে provider-supported personal বা team access হিসেবে দেখানো হয় না। এই পেজে fixed price থাকলে সেটি SaveOnSub-এর approved local catalog price; provider checkout price আলাদা হতে পারে।"
        how_heading = "অর্ডার করার আগে"
        how_items = ["Exact plan/tier নিশ্চিত করুন", "অ্যাক্সেস পদ্ধতি ও account/workspace ownership নিশ্চিত করুন", "বর্তমান availability ও delivery timing নিশ্চিত করুন", "তারপর দেখানো local payment method ব্যবহার করুন"]
        independent = "SaveOnSub একটি স্বাধীন local subscription/payment assistance store; provider-এর সাথে affiliation কেবল স্পষ্টভাবে প্রমাণিত হলে বলা হবে। Provider plan, limits ও terms পরিবর্তিত হতে পারে।"
        confirm = "WhatsApp-এ বর্তমান মূল্য নিশ্চিত করুন"
        provider_text = "Provider pricing/terms যাচাই করুন"
    else:
        heading = f"{name} Price in Bangladesh"
        intro = "Review the current SaveOnSub public offer below. Before payment, confirm the exact provider tier, access method, availability and order-specific support terms."
        access_heading = "Confirm the access model before payment"
        access_copy = "Credential-shared AI access is not presented as provider-supported personal or team access. When this page shows a fixed price, it is SaveOnSub's approved local catalog price; the provider checkout price can be different."
        how_heading = "Before you order"
        how_items = ["Confirm the exact plan or tier", "Confirm the account/workspace access method and ownership", "Confirm current availability and delivery timing", "Then use the local payment method shown at checkout"]
        independent = "SaveOnSub is an independent local subscription/payment assistance store. Provider affiliation is stated only when it is explicitly evidenced. Provider plans, limits and terms can change."
        confirm = "Confirm current price on WhatsApp"
        provider_text = "Verify provider pricing/terms"

    provider_ref = ""
    if official_url:
        ref = f"{provider_text} ↗"
        usd = f" · provider list reference: ${official_usd:g}" if isinstance(official_usd, (int, float)) else ""
        provider_ref = f'<a href="{esc(official_url)}" target="_blank" rel="noopener nofollow" style="font-size:13px;color:var(--muted);text-decoration:underline">{esc(ref)}</a>{esc(usd)}'

    if request_price:
        plan_html = f'''<div class="pcard"><div><b>{esc(confirm)}</b><br><span class="tos">{esc("PRICE REVIEW REQUIRED" if not bn else "মূল্য যাচাই প্রয়োজন")}</span></div><div class="ctas"><a class="btn btn-primary btn-sm" href="https://wa.me/{WA}?text={esc('Hi, please confirm the current ' + name + ' price, exact tier and access method.')}" target="_blank" rel="noopener">{esc(confirm)}</a></div></div>'''
        anchor = esc(confirm)
    else:
        cards = []
        for plan in plans:
            label = str(plan.get("label", "Plan"))
            price = int(plan["bdt"])
            access = access_label(plan, bn)
            billing = price_label(plan, bn)
            onclick = js_args(pid, label, price, name)
            cards.append(
                f'''<div class="pcard" style="flex-direction:row;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px"><div><b>{esc(label)}</b><br><span class="tos personal">{esc(access)}</span><span style="font-size:12px;color:var(--muted)"> · {esc(plan.get("duration", "1 month"))}</span></div><div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"><span style="font-size:22px;font-weight:900;color:var(--green2)">{esc(billing)}</span><button class="btn btn-primary btn-sm" onclick="cartAdd({onclick})">{'কার্টে যোগ করুন' if bn else 'Add to cart'}</button></div></div>'''
            )
        plan_html = "\n".join(cards)
        anchor = ("From " if len(plans) > 1 and not bn else "") + money(min(int(p["bdt"]) for p in plans))

    caveat = ""
    if pid == "chatgpt-business":
        caveat = "<div class=\"notice mt2\">ChatGPT Business is a workspace product and provider minimum-seat/billing rules can apply. Confirm the current seat requirement and workspace role before payment.</div>"
    elif pid in {"chatgpt-go", "chatgpt-plus", "claude-pro"}:
        caveat = "<div class=\"notice mt2\">This listing is not a credential-sharing offer. Confirm the exact customer-specific activation method before payment.</div>"
    elif pid == "chatgpt-pro":
        caveat = "<div class=\"notice mt2\">Fixed-price sale is paused on this page until the currently available provider tier and checkout amount are reconfirmed.</div>"

    items = "".join(f"<li>{esc(x)}</li>" for x in how_items)
    return f'''<main id="main" data-commercial-truth="{REVISION}"><div class="wrap" style="max-width:880px">
<div class="crumbs"><a href="{home}">{'হোম' if bn else 'Home'}</a> › <a href="{all_link}">{'সব সাবস্ক্রিপশন' if bn else 'All subscriptions'}</a> › {esc(name)}</div>
<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap"><span style="font-size:46px">{icon}</span><div><h1 style="font-size:clamp(26px,4vw,38px)">{esc(heading)}</h1><span class="cat">{cat}</span></div></div>
<p class="sub mt2">{esc(intro)}</p>
<div class="anchor mt2"><span class="ours">{esc(anchor)}</span>{provider_ref}</div>
<h2 class="mt3" style="font-size:22px">{'বর্তমান অফার' if bn else 'Current public offer'}</h2>
<div class="grid mt2" style="grid-template-columns:1fr;gap:10px">{plan_html}</div>
{caveat}
<section class="mt3"><h2 style="font-size:22px">{esc(access_heading)}</h2><p>{esc(access_copy)}</p></section>
<section class="mt3"><h2 style="font-size:22px">{esc(how_heading)}</h2><ul>{items}</ul><p><a class="btn btn-ghost btn-sm" href="{checkout}">{'চেকআউট দেখুন' if bn else 'View checkout'}</a></p></section>
<div class="notice mt3">{esc(independent)}</div>
</div></main>'''


def rewrite_product_page(path: Path, product: dict, bn: bool) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    name = product.get("name", product.get("id", "Subscription"))
    plans = product.get("plans") or []
    request_price = bool(product.get("request_price")) or not plans
    if bn:
        price_part = "বর্তমান মূল্য নিশ্চিত করুন" if request_price else f"{money(min(int(p['bdt']) for p in plans))} থেকে"
        title = f"{name} বাংলাদেশে — {price_part} | SAVEONSUB"
        desc = f"{name} বাংলাদেশে: বর্তমান SaveOnSub মূল্য, access method এবং provider tier পেমেন্টের আগে নিশ্চিত করুন।"
    else:
        price_part = "Current Price Confirmation" if request_price else f"From {money(min(int(p['bdt']) for p in plans))}"
        title = f"{name} Price in Bangladesh — {price_part} | SAVEONSUB"
        desc = f"{name} in Bangladesh: review the current SaveOnSub price and confirm the exact provider tier, access method and availability before payment."
    text = remove_jsonld(text, ('"@type": "FAQPage"', '"@type":"FAQPage"', '"@type": "Product"', '"@type":"Product"'))
    text = set_title(text, title)
    text = set_meta(text, "description", desc)
    text = set_meta(text, "og:title", title, prop=True)
    text = set_meta(text, "og:description", desc, prop=True)
    text = add_revision_meta(text)
    new_main = product_main(product, bn)
    if re.search(r'<main\b[^>]*>.*?</main>', text, re.I | re.S):
        text = re.sub(r'<main\b[^>]*>.*?</main>', new_main, text, count=1, flags=re.I | re.S)
    else:
        text = text.replace("</body>", new_main + "\n</body>", 1)
    path.write_text(sanitize_common(text), encoding="utf-8")


def card_price(product: dict, bn: bool) -> tuple[str, str]:
    plans = product.get("plans") or []
    if product.get("request_price") or not plans:
        return ("বর্তমান মূল্য নিশ্চিত করুন" if bn else "Confirm current price", "মূল্য/অ্যাক্সেস নিশ্চিত করুন" if bn else "Confirm price/access")
    low = min(int(p["bdt"]) for p in plans)
    label = ("৳" + f"{low:,}")
    if len(plans) > 1:
        label = ("থেকে " if bn else "From ") + label
    kinds = {p.get("type") for p in plans}
    access = "Team / Workspace" if kinds == {"team"} else ("কাস্টমার-নির্দিষ্ট" if bn else "Customer-specific")
    return label, access


def patch_listing_cards(text: str, governed: dict, bn: bool) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "pcard" not in line:
            continue
        for pid, product in governed.items():
            if f"{pid}.html" not in line:
                continue
            price, access = card_price(product, bn)
            line = re.sub(r'<div class="price">.*?</div>', f'<div class="price">{esc(price)}</div>', line, flags=re.I)
            line = re.sub(r'<span class="tos[^"]*">.*?</span>', f'<span class="tos personal">{esc(access)}</span>', line, flags=re.I)
            line = re.sub(r'<s>.*?</s>', '', line, flags=re.I)
            lines[i] = line
            break
    return "\n".join(lines)


def home_body(governed: dict, bn: bool) -> str:
    picks = ["chatgpt-plus", "claude-pro", "google-ai-pro", "midjourney", "runway", "github-copilot"]
    cards = []
    for pid in picks:
        product = governed.get(pid)
        if not product:
            continue
        price, access = card_price(product, bn)
        cards.append(f'<div class="pcard"><span class="icon">{esc(product.get("emoji", "✨"))}</span><h3>{esc(product.get("name", pid))}</h3><div class="price">{esc(price)}</div><span class="tos personal">{esc(access)}</span><div class="ctas"><a class="btn btn-primary btn-sm" href="p/{esc(pid)}.html">{"দেখুন" if bn else "View"}</a></div></div>')
    card_html = "".join(cards)
    categories = [
        ("🤖", "ai-assistants", "এআই অ্যাসিস্ট্যান্ট" if bn else "AI Assistants"),
        ("🎨", "ai-image-design", "ইমেজ ও ডিজাইন" if bn else "Image & Design"),
        ("🎬", "ai-video", "এআই ভিডিও" if bn else "AI Video"),
        ("🎙️", "ai-voice-music", "ভয়েস ও মিউজিক" if bn else "Voice & Music"),
        ("💻", "ai-code-dev", "কোডিং ও ডেভ" if bn else "Code & Dev"),
        ("✍️", "ai-writing", "এআই রাইটিং" if bn else "AI Writing"),
        ("🗂️", "workspace-productivity", "ওয়ার্কস্পেস" if bn else "Workspace"),
        ("🍿", "entertainment", "এন্টারটেইনমেন্ট" if bn else "Entertainment"),
        ("🔒", "vpn-security", "ভিপিএন ও সিকিউরিটি" if bn else "VPN & Security"),
        ("🎁", "bundles", "কাস্টম বান্ডেল" if bn else "Custom Bundles"),
    ]
    cat_html = "".join(f'<a class="cattile" href="c/{slug}.html"><span class="icon">{icon}</span>{esc(label)}</a>' for icon, slug, label in categories)
    if bn:
        eyebrow = "🇧🇩 বাংলাদেশ সাবস্ক্রিপশন স্টোর"
        h1 = "সঠিক সাবস্ক্রিপশন বেছে নিন। BDT-তে পেমেন্ট করুন। অ্যাক্সেস আগে বুঝে নিন।"
        sub = "AI, productivity, streaming ও অন্যান্য subscription তুলনা করুন। Fixed price কেবল approved plan-এ দেখানো হয়; dynamic plan-এ payment-এর আগে exact tier, access method এবং বর্তমান price নিশ্চিত করা হয়।"
        how = [("১. প্রোডাক্ট বাছুন", "আপনার কাজ অনুযায়ী tool/plan নির্বাচন করুন।"), ("২. অ্যাক্সেস নিশ্চিত করুন", "Personal/customer-specific, provider-supported Team/Workspace, Bundle বা Setup/Service—exact method আগে জানুন।"), ("৩. মূল্য নিশ্চিত করুন", "Fixed approved price থাকলে page-এ দেখবেন; অন্যথায় WhatsApp-এ current checkout reconfirm করা হবে।"), ("৪. তারপর পেমেন্ট", "Availability, delivery timing ও support terms নিশ্চিত হওয়ার পর দেখানো local method ব্যবহার করুন।")]
        note = "Credential-shared AI access-কে provider-supported personal/team plan হিসেবে দেখানো হয় না। SaveOnSub স্বাধীন local subscription/payment assistance store; provider plans ও terms পরিবর্তিত হতে পারে।"
        browse = "সব সাবস্ক্রিপশন দেখুন"
        ask = "WhatsApp-এ সাহায্য নিন"
    else:
        eyebrow = "🇧🇩 BANGLADESH SUBSCRIPTION STORE"
        h1 = "Choose the right subscription. Pay in BDT. Know the access model first."
        sub = "Compare AI, productivity, streaming and other subscriptions. Fixed prices are published only for approved plans; dynamic plans require confirmation of the exact tier, access method and current checkout before payment."
        how = [("1. Pick the product", "Choose the tool or plan that matches the work you need to do."), ("2. Confirm access", "Know whether it is customer-specific, a provider-supported Team/Workspace seat, a Bundle, or a Setup/Service arrangement."), ("3. Confirm the price", "Approved fixed prices appear on the page; dynamic plans are reconfirmed against the current provider tier before payment."), ("4. Pay after confirmation", "Use the displayed local payment method after availability, delivery timing and support terms are confirmed.")]
        note = "Credential-shared AI access is not presented as provider-supported personal/team commerce. SaveOnSub is an independent local subscription/payment assistance store; provider plans and terms can change."
        browse = "Browse subscriptions"
        ask = "Ask on WhatsApp"
    steps = "".join(f'<div class="step"><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for a, b in how)
    return f'''<header class="hero" id="main" data-commercial-truth="{REVISION}"><div class="wrap hgrid"><div><span class="pill">{esc(eyebrow)}</span><h1>{esc(h1)}</h1><p class="sub">{esc(sub)}</p><div class="heroctas"><a href="all.html" class="btn btn-primary">{esc(browse)} →</a><a href="https://wa.me/{WA}" class="btn btn-ghost" target="_blank" rel="noopener">{esc(ask)}</a></div><div class="ticker mt2"><span class="dotp"></span><span id="tick">{esc(note)}</span></div></div><div><div class="grid g3" style="gap:12px">{card_html}</div></div></div></header>
<section><div class="wrap"><span class="pill">{'ক্যাটাগরি' if bn else 'CATEGORIES'}</span><h2>{'প্রয়োজন অনুযায়ী ব্রাউজ করুন' if bn else 'Browse by what you need'}</h2><div class="grid g4 mt3">{cat_html}</div></div></section>
<section style="background:var(--bg2);border-block:1px solid var(--line)"><div class="wrap"><span class="pill">{'কীভাবে কাজ করে' if bn else 'HOW IT WORKS'}</span><h2>{'পেমেন্টের আগে গুরুত্বপূর্ণ তথ্য নিশ্চিত করুন' if bn else 'Confirm the important details before payment'}</h2><div class="steps mt3">{steps}</div></div></section>
<section><div class="wrap" style="max-width:900px"><div class="notice"><b>{'অ্যাক্সেস ও মূল্য নীতি:' if bn else 'Access and pricing policy:'}</b> {esc(note)}</div></div></section>'''


def rewrite_home(path: Path, governed: dict, bn: bool) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    title = "SAVEONSUB — AI & Subscription Plans in Bangladesh" if not bn else "SAVEONSUB — বাংলাদেশে AI ও সাবস্ক্রিপশন প্ল্যান"
    desc = "Compare subscription plans in Bangladesh, see approved BDT prices and confirm the exact access model, provider tier and availability before payment." if not bn else "বাংলাদেশে subscription plan তুলনা করুন, approved BDT price দেখুন এবং payment-এর আগে exact access model, provider tier ও availability নিশ্চিত করুন।"
    text = remove_jsonld(text, ('"@type":"FAQPage"', '"@type": "FAQPage"', '"@type":"OnlineStore"', '"@type": "OnlineStore"'))
    text = set_title(text, title)
    text = set_meta(text, "description", desc)
    text = set_meta(text, "og:title", title, prop=True)
    text = set_meta(text, "og:description", desc, prop=True)
    text = add_revision_meta(text)
    replacement = home_body(governed, bn)
    if re.search(r'<header\s+class="hero"[^>]*>.*?(?=<footer\b)', text, re.I | re.S):
        text = re.sub(r'<header\s+class="hero"[^>]*>.*?(?=<footer\b)', replacement + "\n", text, count=1, flags=re.I | re.S)
    else:
        # Fail closed rather than leave a legacy commercial homepage untouched.
        raise SystemExit(f"[commercial-truth] homepage structure not recognized: {path}")
    path.write_text(sanitize_common(text), encoding="utf-8")


def main() -> int:
    if not SITE.exists():
        raise SystemExit("[commercial-truth] _site is missing; stage_deploy.py must run first")
    catalog = read_json(CATALOG)
    policy = read_json(POLICY)
    if catalog.get("meta", {}).get("commercial_revision") != policy.get("revision"):
        raise SystemExit("[commercial-truth] catalog projection revision mismatch")

    products = {str(p.get("id")): p for p in catalog.get("products", []) if p.get("id")}
    governed = {
        pid: p for pid, p in products.items()
        if p.get("pricing_status") in {"approved-fixed", "price-review-required"}
    }

    # First sanitize every public HTML surface, then replace the high-risk AI and
    # bundle product bodies with deterministic governed content.
    html_files = list(SITE.rglob("*.html"))
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = sanitize_common(text)
        text = patch_listing_cards(text, governed, bn="/bn/" in path.as_posix() or path.name == "bn.html")
        path.write_text(text, encoding="utf-8")

    rewrite_home(SITE / "index.html", governed, False)
    rewrite_home(SITE / "bn.html", governed, True)

    rewritten = 0
    for pid, product in governed.items():
        for path, bn in ((SITE / "p" / f"{pid}.html", False), (SITE / "bn" / "p" / f"{pid}.html", True)):
            if path.exists():
                rewrite_product_page(path, product, bn)
                rewritten += 1

    # Runtime/public catalog must expose the same revision as the HTML artifact.
    public_catalog = SITE / "assets" / "catalog.js"
    if not public_catalog.exists() or REVISION not in public_catalog.read_text(encoding="utf-8", errors="replace"):
        raise SystemExit("[commercial-truth] staged assets/catalog.js is not pricing-v2 governed")

    print(f"[commercial-truth] revision={REVISION}; sanitized_html={len(html_files)}; rewritten_product_pages={rewritten}; governed_products={len(governed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
