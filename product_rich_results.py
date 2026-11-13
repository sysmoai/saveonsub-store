#!/usr/bin/env python3
"""Product rich results + answer-first copy for priced product pages (build step).

Runs after product_seo_enrich.py and before the price/claims guards, so every
guard still checks the final HTML. Source of truth is the governed public
catalog the build already staged (_site/assets/catalog.js): only plans the CEO
approved in the pricebook are present there, so this step can never invent a
price.

Per priced product page (EN /p and BN /bn/p, AIPS excluded) it:
- puts the lowest approved price in the <title> and a price/payment summary in
  the meta + OG description (search snippet = answer to "X price in Bangladesh");
- adds a visible "Quick answer" paragraph listing every approved plan, its
  access type and price, plus the pricebook approval date (quotable by AI
  search engines);
- adds a visible price & ordering FAQ (3 questions, facts from the catalog);
- adds Product JSON-LD with one Offer per approved plan (BDT, no availability claim) and a
  FAQPage JSON-LD built only from FAQ text that is visible on the page.

No ratings, reviews, rankings, delivery-time or guarantee claims are added.
`--check` re-verifies the staged artifact without writing.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
BASE = "https://saveonsub.com"
MARK = "rich-results-2026-11-06"
TITLE_MAX = 60
DESC_MAX = 160
JS_CATALOG = re.compile(r"const CATALOG = (\{.*?\});\s*$", re.S | re.M)
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]+")
BLOCK = re.compile(rf'<(section|script)[^>]*data-sos="{MARK}"[^>]*>.*?</\1>\s*', re.S)
FORBIDDEN = re.compile(
    r"cheapest|lowest price|\#1\b|lifetime|guarantee|instant|ratingValue|aggregateRating|"
    r"\bbest\b|সবচেয়ে কম|গ্যারান্টি|within\s+\d+\s*(?:min|minutes|hours?)|\d+\s*[–-]\s*\d+\s*(?:min|minutes|মিনিট)|\d+\s*মিনিটে",
    re.I,
)


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", EMOJI.sub("", name or "")).strip()


def money(v: int) -> str:
    return f"৳{int(v):,}"


def unit_text(plan: dict, bn: bool) -> str:
    unit = plan.get("billing_unit", "month")
    if bn:
        return {"user/month": "ব্যবহারকারী / মাস", "year": "বছর", "6 months": "৬ মাস"}.get(unit, "মাস")
    return {"user/month": "user / month", "year": "year", "6 months": "6 months"}.get(unit, "month")


def price_text(plan: dict, bn: bool) -> str:
    return f"{money(plan['bdt'])} / {unit_text(plan, bn)}"


def access_text(plan: dict, bn: bool) -> str:
    kind = plan.get("type") or plan.get("access_type")
    if bn:
        return {"personal": "কাস্টমার-নির্দিষ্ট অ্যাক্সেস", "team": "টিম / ওয়ার্কস্পেস অ্যাক্সেস",
                "shared": "শেয়ার্ড অ্যাকাউন্ট (একাধিক ব্যবহারকারী)", "official": "অফিসিয়াল প্ল্যান — সেটআপ সহায়তা",
                "bundle": "বান্ডেল"}.get(kind, "অ্যাক্সেস পদ্ধতি নিশ্চিত করুন")
    return {"personal": "Customer-specific access", "team": "Team / Workspace access",
            "shared": "Shared account (multiple users)", "official": "Official plan — setup help",
            "bundle": "Bundle"}.get(kind, "Confirm access method")


def load_catalog(site: Path) -> dict[str, dict]:
    m = JS_CATALOG.search((site / "assets" / "catalog.js").read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("[rich-results] CATALOG literal not found in staged catalog.js")
    return {p["id"]: p for p in json.loads(m.group(1))["products"]}


def priced(products: dict[str, dict]) -> dict[str, dict]:
    return {pid: p for pid, p in products.items()
            if p.get("plans") and not p.get("request_price") and not pid.startswith("aips-")}


def approved_on(pid: str, policy: dict) -> str:
    rule = (policy.get("approved_products") or {}).get(pid) or {}
    return str(rule.get("approved_on") or policy.get("approved_at") or "")[:10]


# ---------------------------------------------------------------- copy

def make_title(name: str, low: int, many: bool, bn: bool) -> str | None:
    p = money(low)
    if bn:
        options = [f"{name} সাবস্ক্রিপশন দাম বাংলাদেশে — {p}{' থেকে' if many else ''} | SAVEONSUB",
                   f"{name} দাম বাংলাদেশে — {p}{' থেকে' if many else ''} | SAVEONSUB",
                   f"{name} দাম — {p}{' থেকে' if many else ''} | SAVEONSUB",
                   f"{name} দাম বাংলাদেশে — {p}{' থেকে' if many else ''}"]
    else:
        # "<x> subscription bd" out-searches "<x> price in bd" ~6:1 in BD (Semrush, 23 Oct 2026);
        # the H1 keeps "Price in Bangladesh", so the title carries the BD + subscription variant.
        options = [f"{name} Subscription Price in BD — {'from ' if many else ''}{p} | SAVEONSUB",
                   f"{name} Price in Bangladesh — {'from ' if many else ''}{p} | SAVEONSUB",
                   f"{name} Price in BD — {'from ' if many else ''}{p} | SAVEONSUB",
                   f"{name} Price in Bangladesh — {'from ' if many else ''}{p}",
                   f"{name} Price in BD — {'from ' if many else ''}{p}"]
    return next((o for o in options if len(o) <= TITLE_MAX), None)


def make_desc(name: str, plans: list[dict], bn: bool) -> str:
    low = min(plans, key=lambda x: x["bdt"])
    kinds = {pl.get("type") or pl.get("access_type") for pl in plans}
    if bn:
        lead = f"বাংলাদেশে {name} {price_text(low, True)} থেকে"
        tail = "। বিকাশ, নগদ বা রকেটে পেমেন্ট, WhatsApp-এ অর্ডার। পেমেন্টের আগে অ্যাক্সেস টাইপ লিখিতভাবে নিশ্চিত।"
        mid = f" — {len(plans)}টি প্ল্যান" if len(plans) > 1 else ""
    else:
        lead = f"{name} in Bangladesh from {price_text(low, False)}"
        mid = f": {len(plans)} plans" + (" (shared and personal)" if {"shared", "personal"} <= kinds else "") if len(plans) > 1 else ""
        tail = ". Pay by bKash, Nagad or Rocket; order on WhatsApp. Access type confirmed before payment."
    out = lead + mid + tail
    if len(out) > DESC_MAX:
        out = lead + tail
    if len(out) > DESC_MAX:
        out = out[:DESC_MAX - 1].rsplit(" ", 1)[0] + "…"
    return out


def plan_list(plans: list[dict], bn: bool) -> str:
    parts = [f"{price_text(pl, bn)} — {esc(pl.get('label', 'Plan'))} · {access_text(pl, bn)}" for pl in plans]
    if len(parts) == 1:
        return parts[0]
    joiner = " অথবা " if bn else " or "
    return "; ".join(parts[:-1]) + ";" + joiner + parts[-1]


def faq_items(name: str, plans: list[dict], date: str, bn: bool) -> list[tuple[str, str]]:
    kinds = {pl.get("type") or pl.get("access_type") for pl in plans}
    if bn:
        items = [
            (f"বাংলাদেশে {name}-এর দাম কত?",
             f"SaveOnSub-এ {name}: {plan_list(plans, True)}। দাম সর্বশেষ হালনাগাদ {date}। পেমেন্টের আগে WhatsApp-এ চূড়ান্ত দাম ও প্ল্যান নিশ্চিত করা হয়।"),
            (f"{name} কীভাবে কিনব ও পেমেন্ট করব?",
             "প্ল্যান বেছে কার্টে যোগ করুন অথবা WhatsApp-এ মেসেজ দিন। বিকাশ, নগদ বা রকেটে পেমেন্ট করুন; ট্রানজ্যাকশন আইডি দিলে অর্ডার নিশ্চিত হয়।"),
        ]
        if "shared" in kinds:
            items.append(("শেয়ার্ড আর পার্সোনাল প্ল্যানের পার্থক্য কী?",
                          "শেয়ার্ড প্ল্যানে একাধিক ব্যবহারকারী একই অ্যাকাউন্ট ব্যবহার করেন, তাই অন্যরা আপনার অ্যাক্টিভিটি দেখতে পারেন এবং প্রোভাইডারের নিয়মে ঝুঁকি থাকে। কাজ বা গোপন তথ্যের জন্য কাস্টমার-নির্দিষ্ট (পার্সোনাল) প্ল্যান নিন।"))
        else:
            items.append((f"{name}-এ কোন ধরনের অ্যাক্সেস পাব?",
                          f"এই পেজের প্রতিটি প্ল্যানের পাশে অ্যাক্সেস টাইপ লেখা আছে: {', '.join(sorted({access_text(pl, True) for pl in plans}))}। পেমেন্টের আগে তা লিখিতভাবে নিশ্চিত করা হয়।"))
        return items
    items = [
        (f"How much is {name} in Bangladesh?",
         f"At SaveOnSub, {name} costs {plan_list(plans, False)}. Prices were last updated on {date}; your final plan and price are confirmed on WhatsApp before you pay."),
        (f"How do I buy {name} and pay in Bangladesh?",
         "Pick a plan and add it to the cart, or message SaveOnSub on WhatsApp. Pay by bKash, Nagad or Rocket and share the transaction ID to confirm the order."),
    ]
    if "shared" in kinds:
        items.append(("What is the difference between a shared and a personal plan?",
                      "On a shared plan several people use one account, so others may see your activity and the provider's terms may restrict sharing. Choose a customer-specific (personal) plan for work or private data."))
    else:
        items.append((f"What kind of access do I get with {name}?",
                      f"Each plan on this page shows its access type: {', '.join(sorted({access_text(pl, False) for pl in plans}))}. It is confirmed in writing before payment."))
    return items


def visible_faq(html_text: str) -> list[tuple[str, str]]:
    """Q/A pairs already rendered in an FAQ section (h3 + p)."""
    m = re.search(r'<h2[^>]*>(?:Frequently asked questions|সাধারণ প্রশ্ন)</h2>(.*?)(?=<h2|</main>|<section)', html_text, re.S)
    if not m:
        return []
    out = []
    for q, a in re.findall(r"<h3[^>]*>(.*?)</h3>\s*<p>(.*?)</p>", m.group(1), re.S):
        out.append((html.unescape(re.sub(r"<[^>]+>", "", q)).strip(), html.unescape(re.sub(r"<[^>]+>", "", a)).strip()))
    return out


# ---------------------------------------------------------------- page

def set_title(t: str, title: str) -> str:
    return re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", t, count=1, flags=re.S)


def set_meta(t: str, attr: str, name: str, content: str) -> str:
    pat = re.compile(rf'<meta\s+{attr}="{re.escape(name)}"[^>]*>')
    tag = f'<meta {attr}="{name}" content="{esc(content)}">'
    return pat.sub(lambda _m: tag, t, count=1) if pat.search(t) else t.replace("</head>", tag + "\n</head>", 1)


def jsonld(obj: dict) -> str:
    raw = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json" data-sos="{MARK}">{raw}</script>\n'


def product_ld(pid: str, p: dict, name: str, url: str, desc: str, image: str | None) -> dict:
    offers = []
    for pl in p["plans"]:
        offers.append({
            "@type": "Offer",
            "name": f"{name} — {pl.get('label', 'Plan')}",
            "price": str(int(pl["bdt"])),
            "priceCurrency": "BDT",
            # No "availability": pages say availability is confirmed on WhatsApp
            # before payment, so a blanket InStock would contradict the visible copy
            # (SOS-P0-009). Add it back per plan only from verified supply data.
            "url": url,
            "seller": {"@type": "Organization", "name": "SaveOnSub", "url": BASE + "/"},
            "description": f"{access_text(pl, False)} · {pl.get('duration', '1 month')}",
        })
    obj = {"@context": "https://schema.org", "@type": "Product", "@id": url + "#product",
           "name": name, "sku": pid, "category": p.get("category", ""), "description": desc,
           "url": url, "offers": offers}
    if image:
        obj["image"] = image
    return obj


def enrich(t: str, pid: str, p: dict, date: str, bn: bool) -> str:
    t = BLOCK.sub("", t)
    name = clean_name(p["name"])
    plans = p["plans"]
    url = f"{BASE}{'/bn' if bn else ''}/p/{pid}"
    low = min(int(pl["bdt"]) for pl in plans)
    title = make_title(name, low, len({pl["bdt"] for pl in plans}) > 1, bn)
    if title:
        t = set_title(t, title)
        t = set_meta(t, "property", "og:title", title)
    desc = make_desc(name, plans, bn)
    t = set_meta(t, "name", "description", desc)
    t = set_meta(t, "property", "og:description", desc)

    qa_label = "দ্রুত উত্তর" if bn else "Quick answer"
    date_txt = (f"দাম সর্বশেষ হালনাগাদ: {date}" if bn else f"Prices last updated: {date}")
    if bn:
        answer = f"বাংলাদেশে SaveOnSub-এ {esc(name)}: {plan_list(plans, True)}। পেমেন্ট বিকাশ, নগদ বা রকেটে।"
    else:
        answer = f"At SaveOnSub, {esc(name)} in Bangladesh costs {plan_list(plans, False)}. Pay by bKash, Nagad or Rocket."
    quick = (f'<section data-sos="{MARK}" class="quick-answer" style="margin:14px 0;padding:12px 14px;'
             f'border-left:4px solid var(--green2,#0d9488);background:var(--card,rgba(13,148,136,.06));border-radius:8px">'
             f'<p style="margin:0"><b>{qa_label}:</b> {answer} <span style="color:var(--muted);font-size:13px">'
             f'({date_txt})</span></p></section>\n')
    anchor = re.search(r'<h2[^>]*>(?:Current public offer|বর্তমান অফার)', t)
    if anchor:
        t = t[:anchor.start()] + quick + t[anchor.start():]
    else:
        t = re.sub(r"(</h1>)", r"\1" + quick.replace("\\", "\\\\"), t, count=1)

    items = faq_items(name, plans, date, bn)
    existing = visible_faq(t)
    have = {q.lower() for q, _ in existing}
    items = [qa for qa in items if qa[0].lower() not in have]
    heading = "দাম ও অর্ডার — প্রশ্নোত্তর" if bn else "Price and ordering FAQ"
    body = "".join(f'<h3 class="mt2" style="font-size:17px">{esc(q)}</h3><p>{a}</p>' for q, a in items)
    faq = f'<section data-sos="{MARK}" class="price-faq"><h2 class="mt3" style="font-size:22px">{heading}</h2>{body}</section>\n'
    t = re.sub(r"(</div>\s*</main>)", lambda m: faq + m.group(1), t, count=1) if re.search(r"</div>\s*</main>", t) \
        else t.replace("</main>", faq + "</main>", 1)

    img = re.search(r'<meta property="og:image" content="([^"]+)"', t)
    lds = jsonld(product_ld(pid, p, name, url, desc, img.group(1) if img else None))
    all_qa = existing + [(q, html.unescape(re.sub(r"<[^>]+>", "", a))) for q, a in items]
    lds += jsonld({"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq",
                   "mainEntity": [{"@type": "Question", "name": q,
                                   "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in all_qa]})
    return t.replace("</head>", lds + "</head>", 1)


# ---------------------------------------------------------------- check

def check(site: Path, products: dict[str, dict]) -> list[str]:
    errors = []
    for pid, p in products.items():
        allowed = {int(pl["bdt"]) for pl in p["plans"]}
        for path in (site / "p" / f"{pid}.html", site / "bn" / "p" / f"{pid}.html"):
            if not path.exists():
                continue
            t = path.read_text(encoding="utf-8")
            rel = path.relative_to(site).as_posix()
            title = html.unescape((re.search(r"<title>(.*?)</title>", t, re.S) or [None, ""])[1])
            if len(title) > TITLE_MAX:
                errors.append(f"{rel}: title {len(title)} > {TITLE_MAX}")
            lds = [json.loads(m) for m in re.findall(
                rf'<script type="application/ld\+json" data-sos="{MARK}">(.*?)</script>', t, re.S)]
            prod = [x for x in lds if x.get("@type") == "Product"]
            faq = [x for x in lds if x.get("@type") == "FAQPage"]
            if len(prod) != 1 or len(faq) != 1:
                errors.append(f"{rel}: expected 1 Product + 1 FAQPage JSON-LD, got {len(prod)}/{len(faq)}")
                continue
            prices = {int(o["price"]) for o in prod[0]["offers"]}
            if prices != allowed:
                errors.append(f"{rel}: Offer prices {sorted(prices)} != approved {sorted(allowed)}")
            if any(o.get("priceCurrency") != "BDT" for o in prod[0]["offers"]):
                errors.append(f"{rel}: Offer currency not BDT")
            if any("availability" in o for o in prod[0]["offers"]):
                errors.append(f"{rel}: Offer availability claimed without verified supply data")
            text = html.unescape(re.sub(r"<[^>]+>", " ", t))
            text = re.sub(r"\s+", " ", text)
            for q in faq[0]["mainEntity"]:
                if re.sub(r"\s+", " ", q["name"]) not in text:
                    errors.append(f"{rel}: FAQ JSON-LD question not visible: {q['name'][:60]}")
            for sec in re.findall(rf'<section data-sos="{MARK}".*?</section>', t, re.S):
                plain = html.unescape(re.sub(r"<[^>]+>", " ", sec))
                if FORBIDDEN.search(plain):
                    errors.append(f"{rel}: forbidden claim in rich-results section: {FORBIDDEN.search(plain).group(0)}")
                shown = {int(x.replace(",", "")) for x in re.findall(r"৳\s?([\d,]+)", plain)}
                if shown - allowed:
                    errors.append(f"{rel}: unapproved price in rich-results section {sorted(shown - allowed)}")
    return errors


def main(argv: list[str]) -> int:
    site = SITE
    if not (site / "assets" / "catalog.js").exists():
        raise SystemExit("[rich-results] _site missing; run the build first")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    products = priced(load_catalog(site))
    if "--check" not in argv:
        n = 0
        for pid, p in products.items():
            date = approved_on(pid, policy)
            for path, bn in ((site / "p" / f"{pid}.html", False), (site / "bn" / "p" / f"{pid}.html", True)):
                if path.exists():
                    path.write_text(enrich(path.read_text(encoding="utf-8"), pid, p, date, bn), encoding="utf-8")
                    n += 1
        print(f"[rich-results] enriched {n} product pages")
    errors = check(site, products)
    if errors:
        print("\n".join(errors[:80]), file=sys.stderr)
        raise SystemExit(f"[rich-results] FAIL — {len(errors)} issue(s)")
    print(f"[rich-results] PASS — {len(products)} priced products: Product/Offer + FAQPage JSON-LD match approved prices and visible FAQ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
