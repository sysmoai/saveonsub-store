#!/usr/bin/env python3
"""Harden generated _public_v3 for a strict L1 information-only release."""
from __future__ import annotations

import json
import pathlib
import re

from catalog_model import load_catalog
from extend_public_info_v3 import extend_public_info
from routes_v3 import DOMAIN, slugify, strip_price_tokens

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "_public_v3"
ASSETS = PUBLIC / "assets"

APP_JS = r'''/* SAVEONSUB L1 public-information runtime */
const SUPPORT_EMAIL = "support@saveonsub.com";

function navToggle(){
  const links=document.querySelector('.navlinks');
  if(links) links.classList.toggle('open');
}

function supportMailto(subject, body){
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject||'SAVEONSUB support')}&body=${encodeURIComponent(body||'')}`;
}

function copyText(text,label){
  if(!navigator.clipboard) return;
  navigator.clipboard.writeText(text).then(()=>showNotice(label||'Copied'));
}

function showNotice(message){
  let node=document.getElementById('sos-notice');
  if(!node){
    node=document.createElement('div');
    node.id='sos-notice';
    node.setAttribute('role','status');
    node.style.cssText='position:fixed;left:50%;bottom:20px;transform:translateX(-50%);z-index:9999;padding:10px 14px;border-radius:10px;background:#103433;color:#f2fbfa;border:1px solid #14d4b8';
    document.body.appendChild(node);
  }
  node.textContent=message;
  node.hidden=false;
  clearTimeout(node._timer);
  node._timer=setTimeout(()=>{node.hidden=true},2200);
}

function suggestBangla(){
  try{
    if((document.documentElement.lang||'').startsWith('bn')) return;
    if(localStorage.getItem('sos_lang_dismissed')) return;
    const langs=navigator.languages||[navigator.language||''];
    if(!langs.some(l=>(l||'').toLowerCase().startsWith('bn'))) return;
    const alt=document.querySelector('link[hreflang="bn-bd"]');
    if(!alt||!alt.href||alt.href===location.href) return;
    const bar=document.createElement('div');
    bar.setAttribute('role','region');
    bar.setAttribute('aria-label','ভাষা');
    bar.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:9998;max-width:520px;margin:0 auto;background:#103433;border:1px solid #14d4b8;border-radius:14px;padding:12px 14px;display:flex;align-items:center;gap:12px;color:#f2fbfa';
    bar.innerHTML='<span style="flex:1">🇧🇩 বাংলায় দেখতে চান?</span><a class="btn btn-primary btn-sm" href="'+alt.href+'">বাংলায় দেখুন</a><button type="button" aria-label="বন্ধ করুন" style="background:none;border:0;color:inherit;font-size:18px;cursor:pointer">✕</button>';
    bar.querySelector('button').addEventListener('click',()=>{try{localStorage.setItem('sos_lang_dismissed','1')}catch(e){}bar.remove();});
    bar.querySelector('a').addEventListener('click',()=>{try{localStorage.setItem('sos_lang_dismissed','1')}catch(e){}});
    document.body.appendChild(bar);
  }catch(e){}
}

if('serviceWorker' in navigator){
  window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}

document.addEventListener('DOMContentLoaded',suggestBangla);
'''

REDIRECTS = '''/home / 301
/shop /all.html 301
/products /all.html 301
'''

UNSUPPORTED_PROOF_RE = re.compile(
    r"\b[0-9]{2,}\+?\s*(orders|customers|users)\b",
    re.IGNORECASE,
)

FAQ_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": "Can I buy directly from this version of SAVEONSUB?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "No. Product and plan information is public, but order and payment controls remain disabled until eligibility, pricing and payment destinations are verified.",
            },
        },
        {
            "@type": "Question",
            "name": "Why are prices not shown?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "A public selling price is treated as an authority-controlled fact. SAVEONSUB will publish it only when the current approved price registry is populated.",
            },
        },
        {
            "@type": "Question",
            "name": "What if a plan is marked Official provider path?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Use the official provider link on that product or plan page. SAVEONSUB is not offering that plan as reseller commerce in the current state.",
            },
        },
    ],
}


def redact_unsupported_proof(text: str) -> tuple[str, int]:
    return UNSUPPORTED_PROOF_RE.subn(lambda m: m.group(1), text)


def harden_stylesheet() -> int:
    path = ASSETS / "style.css"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    new = text.replace("shared-low", "legacy-risk-low").replace("shared-med", "legacy-risk-med")
    path.write_text(new, encoding="utf-8")
    return int(new != text)


def schema_tag(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{data}</script>'


def breadcrumb(items: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": url}
            for i, (name, url) in enumerate(items, start=1)
        ],
    }


def inject_jsonld(text: str, payloads: list[dict]) -> tuple[str, int]:
    if not payloads or "</head>" not in text:
        return text, 0
    block = "".join(schema_tag(payload) for payload in payloads)
    return text.replace("</head>", f"{block}</head>", 1), len(payloads)


def add_visible_category_breadcrumb(text: str, rel: str) -> tuple[str, int]:
    if not re.fullmatch(r"(?:bn/)?c/[^/]+\.html", rel):
        return text, 0
    if '<div class="crumbs">' in text:
        return text, 0
    match = re.search(r"<h1>(.*?)</h1>", text, re.S)
    if not match:
        return text, 0
    bn = rel.startswith("bn/")
    home_href = "/bn.html" if bn else "/"
    home_label = "হোম" if bn else "Home"
    crumb = f'<div class="crumbs"><a href="{home_href}">{home_label}</a> › {match.group(1)}</div>'
    marker = '<span class="pill">'
    if marker not in text:
        return text, 0
    return text.replace(marker, crumb + marker, 1), 1


def schema_payloads(catalog: dict) -> dict[str, list[dict]]:
    payloads: dict[str, list[dict]] = {
        "index.html": [{
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "SAVEONSUB",
            "url": f"{DOMAIN}/",
            "inLanguage": ["en-BD", "bn-BD"],
        }],
        "bn.html": [{
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "SAVEONSUB",
            "url": f"{DOMAIN}/bn.html",
            "inLanguage": "bn-BD",
        }],
        "faq.html": [FAQ_SCHEMA],
    }
    products = catalog.get("products", [])
    all_items = []
    all_items_bn = []
    for pos, product in enumerate(products, start=1):
        pid = product["id"]
        name = str(product.get("name") or pid).replace("🎁 ", "")
        category = str(product.get("category") or "")
        category_slug = slugify(category)
        all_items.append({
            "@type": "ListItem",
            "position": pos,
            "url": f"{DOMAIN}/p/{pid}.html",
            "name": name,
        })
        all_items_bn.append({
            "@type": "ListItem",
            "position": pos,
            "url": f"{DOMAIN}/bn/p/{pid}.html",
            "name": name,
        })
        for language in ("en", "bn"):
            bn = language == "bn"
            rel = f"bn/p/{pid}.html" if bn else f"p/{pid}.html"
            product_url = f"{DOMAIN}/{rel}"
            category_url = f"{DOMAIN}/bn/c/{category_slug}.html" if bn else f"{DOMAIN}/c/{category_slug}.html"
            home_url = f"{DOMAIN}/bn.html" if bn else f"{DOMAIN}/"
            product_schema = {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": name,
                "category": category,
                "url": product_url,
                "description": (
                    f"{name} plan and provider-status information for Bangladesh."
                    if not bn else
                    f"বাংলাদেশের জন্য {name} প্ল্যান ও প্রোভাইডার-স্ট্যাটাস তথ্য।"
                ),
            }
            payloads[rel] = [
                product_schema,
                breadcrumb([
                    ("হোম" if bn else "Home", home_url),
                    (category, category_url),
                    (name, product_url),
                ]),
            ]
            for plan in product.get("plans", []):
                route = plan["routes_v3"][language]
                plan_url = f"{DOMAIN}/{route}"
                label = strip_price_tokens(plan.get("label") or "Plan") or ("প্ল্যান" if bn else "Plan")
                payloads[route] = [
                    {
                        "@context": "https://schema.org",
                        "@type": "WebPage",
                        "name": f"{name} — {label}",
                        "url": plan_url,
                        "isPartOf": {"@type": "WebSite", "name": "SAVEONSUB", "url": f"{DOMAIN}/"},
                    },
                    breadcrumb([
                        (name, product_url),
                        (label, plan_url),
                    ]),
                ]
    payloads["all.html"] = [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "SAVEONSUB subscription catalog",
        "numberOfItems": len(all_items),
        "itemListElement": all_items,
    }]
    payloads["bn/all.html"] = [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "SAVEONSUB সম্পূর্ণ সাবস্ক্রিপশন ক্যাটালগ",
        "numberOfItems": len(all_items_bn),
        "itemListElement": all_items_bn,
    }]
    for category in catalog.get("categories", []):
        category_slug = slugify(category)
        items = [p for p in products if p.get("category") == category]
        for language in ("en", "bn"):
            bn = language == "bn"
            rel = f"bn/c/{category_slug}.html" if bn else f"c/{category_slug}.html"
            category_url = f"{DOMAIN}/{rel}"
            home_url = f"{DOMAIN}/bn.html" if bn else f"{DOMAIN}/"
            item_list = {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": f"{category} — SAVEONSUB",
                "numberOfItems": len(items),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i,
                        "url": f"{DOMAIN}/{'bn/' if bn else ''}p/{p['id']}.html",
                        "name": str(p.get("name") or p["id"]).replace("🎁 ", ""),
                    }
                    for i, p in enumerate(items, start=1)
                ],
            }
            payloads[rel] = [
                item_list,
                breadcrumb([
                    ("হোম" if bn else "Home", home_url),
                    (category, category_url),
                ]),
            ]
    return payloads


def harden_html() -> tuple[int, int, int, int]:
    replacements = 0
    robots_hardened = 0
    schemas_added = 0
    category_crumbs_added = 0
    payload_map = schema_payloads(load_catalog())
    for path in PUBLIC.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        new, count = redact_unsupported_proof(text)
        replacements += count
        rel = path.relative_to(PUBLIC).as_posix()
        if rel == "404.html":
            new, robots_count = re.subn(
                r'<meta name="robots" content="index,follow">',
                '<meta name="robots" content="noindex,follow">',
                new,
                count=1,
            )
            robots_hardened += robots_count
        new, crumb_count = add_visible_category_breadcrumb(new, rel)
        category_crumbs_added += crumb_count
        new, schema_count = inject_jsonld(new, payload_map.get(rel, []))
        schemas_added += schema_count
        if new != text:
            path.write_text(new, encoding="utf-8")
    return replacements, robots_hardened, schemas_added, category_crumbs_added


def main() -> int:
    if not PUBLIC.is_dir():
        raise SystemExit("_public_v3 missing; run build_public_info_v3.py first")
    extension = extend_public_info()
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "app.js").write_text(APP_JS, encoding="utf-8")
    (PUBLIC / "_redirects").write_text(REDIRECTS, encoding="utf-8")
    css_hardened = harden_stylesheet()
    proof_redactions, robots_hardened, schemas_added, category_crumbs_added = harden_html()
    print(
        "hardened _public_v3: information-only app.js + non-commerce redirects + "
        f"css_hardened={css_hardened} unsupported_proof_redactions={proof_redactions} "
        f"robots_hardened={robots_hardened} schemas_added={schemas_added} "
        f"category_crumbs_added={category_crumbs_added} i18n_extension={extension}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
