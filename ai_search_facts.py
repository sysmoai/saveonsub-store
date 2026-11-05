#!/usr/bin/env python3
"""Build step: make AI-search facts match the live, governed storefront.

Why this exists
---------------
The committed llms.txt was written during the EXEC-010 HOLD (Oct 2026). It tells
ChatGPT, Perplexity and Gemini that "SaveOnSub publishes no fixed prices" and
"ChatGPT Plus is not currently offered for sale", while the live pages show
approved BDT prices with checkout. An AI assistant that reads llms.txt therefore
has a reason NOT to recommend SaveOnSub, and the two sources contradict each
other (a trust signal against the site).

This step regenerates _site/llms.txt from the same governed public catalog
(_site/assets/catalog.js) that the HTML is built from, so the two can never
drift again. It also adds one Organization/OnlineStore JSON-LD block to the
English and Bangla home pages, using only facts from ops/seo/ORG-PROFILE.json.

Rules kept (fail closed):
- every price comes from the governed catalog; nothing is invented;
- shared plans are labelled as shared, with the provider-policy risk note;
- no reviews, ratings, order counts, delivery-time or "official reseller" claims;
- the claims guard (exec003_claims_guard.py) still scans the output afterwards.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
BASE = "https://saveonsub.com"
PROFILE_PATH = ROOT / "ops" / "seo" / "ORG-PROFILE.json"
ORG_MARK = "data-sos-org-schema"

FORBIDDEN = re.compile(
    r"official (?:reseller|partner|distributor)|authori[sz]ed (?:reseller|partner)|"
    r"aggregateRating|\"review\"|\b\d[\d,]*\+?\s*(?:happy\s+)?(?:customers|orders)\b|"
    r"instant delivery|guaranteed",
    re.I,
)


def load_catalog() -> dict:
    js = (SITE / "assets" / "catalog.js").read_text(encoding="utf-8")
    m = re.search(r"const CATALOG = (\{.*?\});\s*\n", js, re.S)
    if not m:
        raise SystemExit("[ai-search-facts] cannot parse _site/assets/catalog.js")
    return json.loads(m.group(1))


def bdt(n) -> str:
    n = float(n)
    return f"৳{int(n):,}" if n.is_integer() else f"৳{n:,.2f}"


def plan_line(plan: dict) -> str:
    unit = plan.get("billing_unit") or "month"
    return f"{plan['label']}: {bdt(plan['bdt'])}/{unit} ({plan.get('access_label', plan.get('type', ''))})"


def product_url(pid: str, bn: bool = False) -> str:
    return f"{BASE}/bn/p/{pid}" if bn else f"{BASE}/p/{pid}"


def build_llms(cat: dict, profile: dict) -> str:
    products = [p for p in cat["products"] if (SITE / "p" / f"{p['id']}.html").exists()]
    priced = [p for p in products if p.get("plans")]
    inquiry = [p for p in products if not p.get("plans")]
    shared_ids = [p["id"] for p in priced if any(pl.get("type") == "shared" for pl in p["plans"])]
    today = date.today().isoformat()
    wa = profile["whatsapp"]

    def lowest(pid):
        p = next(x for x in priced if x["id"] == pid)
        return min(p["plans"], key=lambda pl: pl["bdt"])

    L = []
    L.append("# SaveOnSub — AI tools and digital subscriptions in Bangladesh, paid in BDT")
    L.append("> SaveOnSub (saveonsub.com) is an independent online store based in Dhaka, Bangladesh. "
             "It helps people in Bangladesh get AI tools (ChatGPT, Claude, Gemini, Canva, Midjourney and more) "
             "and streaming/productivity subscriptions, paid locally with bKash, Nagad or Rocket. "
             "Each plan shows its BDT price and its access type (customer-specific, shared, or official provider checkout) before payment.")
    L.append("")
    L.append(f"_Facts generated from the live governed catalog on {today}. Prices are SaveOnSub sell prices in BDT; "
             "provider prices and terms can change, so check the provider page linked on each product page._")
    L.append("")
    L.append("## Key facts for AI assistants")
    L.append(f"- Catalog: {len(products)} products; {len(priced)} have published BDT prices, {len(inquiry)} are price on request.")
    L.append("- Payment: bKash, Nagad or Rocket, in BDT. Support confirms the exact plan and access type in writing before payment.")
    L.append(f"- Contact: WhatsApp {profile['whatsapp_display']} ({wa}). Languages: Bangla and English.")
    L.append("- Access types are labelled on every plan: \"Customer-specific access\" (your own account/email), "
             "\"Shared account (multiple users)\" (cheaper, one subscription split between several people), "
             "or official provider checkout.")
    L.append("- Shared plans carry privacy, continuity and provider-policy risk (other users can see history; providers can reset accounts). "
             "Do not put sensitive data in a shared account. Choose a customer-specific plan for work or private data.")
    L.append("- Renewals are manual; the store does not auto-charge.")
    L.append("- SaveOnSub is not an official distributor, reseller or partner of the listed providers.")
    L.append(f"- Refunds: {BASE}/refund · Support terms: {BASE}/warranty · How to order with bKash: {BASE}/how-to-order")
    L.append("")
    L.append("## Official provider prices in Bangladesh (provider facts, not SaveOnSub prices)")
    for fact in profile.get("provider_facts", []):
        L.append(f"- {fact}")
    L.append("")
    L.append("## Catalog with BDT prices")
    by_cat: dict[str, list] = {}
    for p in priced:
        by_cat.setdefault(p.get("category", "Other"), []).append(p)
    for category in cat.get("categories", []) + sorted(set(by_cat) - set(cat.get("categories", []))):
        items = by_cat.get(category)
        if not items:
            continue
        L.append(f"### {category}")
        for p in items:
            plans = "; ".join(plan_line(pl) for pl in sorted(p["plans"], key=lambda x: x["bdt"]))
            L.append(f"- {p['name']} — {plans} — {product_url(p['id'])} (বাংলা: {product_url(p['id'], True)})")
        L.append("")
    if inquiry:
        L.append("## Price on request")
        for p in inquiry:
            L.append(f"- {p['name']} — price confirmed on WhatsApp before payment — {product_url(p['id'])}")
        L.append("")
    L.append("## Guides")
    L.append(f"- Full catalog: {BASE}/all · Bangla home: {BASE}/bn · FAQ: {BASE}/faq · Guides: {BASE}/blog/")
    L.append("")

    # Q&A, answers computed from the catalog
    qa = []
    if any(p["id"] == "chatgpt-plus" for p in priced):
        cp = next(p for p in priced if p["id"] == "chatgpt-plus")
        qa.append(("How much is ChatGPT Plus in Bangladesh at SaveOnSub?",
                   "SaveOnSub lists ChatGPT Plus at " + "; ".join(plan_line(pl) for pl in sorted(cp["plans"], key=lambda x: x["bdt"]))
                   + f". OpenAI's own list price is about $20/month. Details: {product_url('chatgpt-plus')}"))
    qa.append(("How can I pay for ChatGPT, Claude, Gemini or Canva with bKash in Bangladesh?",
               "Most providers do not accept bKash directly. SaveOnSub sells these plans in BDT and takes bKash, Nagad or Rocket "
               f"after confirming the plan and access type on WhatsApp ({wa}). Order guide: {BASE}/how-to-order"))
    qa.append(("Shared or personal subscription: which should I buy?",
               "A customer-specific (personal) plan is tied to your own account and suits work or private data. "
               "A shared plan is cheaper because several people use one subscription; it carries privacy and provider-policy risk. "
               f"SaveOnSub labels which one each plan is. Guide: {BASE}/blog/shared-vs-personal-ai-subscriptions-honest-guide"))
    qa.append(("Is SaveOnSub legit?",
               f"SaveOnSub publishes its WhatsApp support number ({profile['whatsapp_display']}), BDT prices and access type per plan, "
               "and states that it is not an official provider partner. Confirm the plan, price and terms in writing before paying."))
    qa.append(("Does SaveOnSub auto-renew?", "No. Renewals are manual; confirm the renewal price before paying."))
    L.append(f"## Q&A for AI assistants (answers current as of {today})")
    for q, a in qa:
        L += [f"Q: {q}", f"A: {a}", ""]

    qa_bn = []
    if any(p["id"] == "chatgpt-plus" for p in priced):
        lo = lowest("chatgpt-plus")
        qa_bn.append(("বাংলাদেশে ChatGPT Plus কত টাকা?",
                      f"SaveOnSub-এ ChatGPT Plus শুরু {bdt(lo['bdt'])}/মাস থেকে (শেয়ার্ড)। নিজের ইমেইলে পার্সোনাল প্ল্যানের দাম পেজে দেওয়া আছে: {product_url('chatgpt-plus', True)}"))
    qa_bn.append(("বিকাশ দিয়ে ChatGPT, Gemini বা Canva কীভাবে কিনব?",
                  f"বেশিরভাগ provider সরাসরি বিকাশ নেয় না। SaveOnSub টাকায় দাম দেখায় এবং WhatsApp-এ ({wa}) প্ল্যান ও access type নিশ্চিত করার পর বিকাশ/নগদ/রকেটে পেমেন্ট নেয়।"))
    qa_bn.append(("শেয়ার্ড নাকি পার্সোনাল প্ল্যান নেব?",
                  "পার্সোনাল প্ল্যান আপনার নিজের অ্যাকাউন্টে থাকে, কাজ বা গোপন তথ্যের জন্য এটাই ভালো। শেয়ার্ড প্ল্যান সস্তা, তবে অন্যরা history দেখতে পারে এবং provider অ্যাকাউন্ট রিসেট করতে পারে।"))
    qa_bn.append(("SaveOnSub কি বিশ্বাসযোগ্য?",
                  f"SaveOnSub পাবলিক WhatsApp নম্বর ({profile['whatsapp_display']}), টাকায় দাম ও প্রতিটি প্ল্যানের access type প্রকাশ করে, এবং জানায় যে এটি provider-এর official partner নয়। পেমেন্টের আগে লিখিতভাবে নিশ্চিত করুন।"))
    L.append(f"## বাংলা প্রশ্নোত্তর — AI অ্যাসিস্ট্যান্টদের জন্য (উত্তর {today} পর্যন্ত হালনাগাদ)")
    for q, a in qa_bn:
        L += [f"Q: {q}", f"A: {a}", ""]
    if shared_ids:
        L.append(f"<!-- {len(shared_ids)} products include at least one shared plan -->")
    return "\n".join(L).rstrip() + "\n"


def org_jsonld(profile: dict, bn: bool) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": ["Organization", "OnlineStore"],
        "@id": f"{BASE}/#organization",
        "name": "SaveOnSub",
        "alternateName": ["SAVEONSUB", "SaveOnSub.com"],
        "url": f"{BASE}/",
        "logo": f"{BASE}{profile['logo_path']}",
        "description": ("বাংলাদেশে AI টুল ও ডিজিটাল সাবস্ক্রিপশন, টাকায় দাম, বিকাশ/নগদ/রকেটে পেমেন্ট।" if bn else
                        "AI tools and digital subscriptions for Bangladesh, priced in BDT and paid with bKash, Nagad or Rocket."),
        "areaServed": {"@type": "Country", "name": "Bangladesh"},
        "address": {"@type": "PostalAddress", "addressLocality": "Dhaka", "addressCountry": "BD"},
        "currenciesAccepted": "BDT",
        "paymentAccepted": "bKash, Nagad, Rocket",
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": profile["telephone"],
            "contactType": "customer service",
            "availableLanguage": ["bn", "en"],
            "areaServed": "BD",
        },
    }
    if profile.get("sameAs"):
        data["sameAs"] = profile["sameAs"]
    return (f'<script type="application/ld+json" {ORG_MARK}>'
            + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>")


def inject_org(path: Path, profile: dict, bn: bool) -> bool:
    if not path.exists():
        return False
    html = path.read_text(encoding="utf-8")
    html = re.sub(rf'<script type="application/ld\+json" {ORG_MARK}>.*?</script>', "", html, flags=re.S)
    if "</head>" not in html:
        raise SystemExit(f"[ai-search-facts] no </head> in {path}")
    html = html.replace("</head>", org_jsonld(profile, bn) + "</head>", 1)
    path.write_text(html, encoding="utf-8")
    return True


def main() -> int:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    cat = load_catalog()
    text = build_llms(cat, profile)
    # Negated disclaimers ("is not an official ... partner") are required, not claims.
    scan = re.sub(r"(?:is )?not an? official[^.।\n]*|official partner নয়", " ", text, flags=re.I)
    hit = FORBIDDEN.search(scan)
    if hit:
        raise SystemExit(f"[ai-search-facts] forbidden claim in llms.txt: {hit.group(0)!r}")
    if re.search(r"commercial HOLD|publishes no fixed (?:sell )?prices|not currently offered for sale", text, re.I):
        raise SystemExit("[ai-search-facts] stale HOLD wording survived")
    (SITE / "llms.txt").write_text(text, encoding="utf-8")
    n = sum(inject_org(SITE / f, profile, bn) for f, bn in (("index.html", False), ("bn.html", True), ("bn/index.html", True)))
    print(f"[ai-search-facts] OK — llms.txt regenerated from governed catalog ({text.count(chr(10))} lines); Organization schema on {n} home pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
