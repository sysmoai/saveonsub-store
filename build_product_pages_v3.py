#!/usr/bin/env python3
"""Generate preview-only v3 ecommerce product pages.

Run after build_plan_pages_v3.py. Output is written under _preview_v3/p and
_preview_v3/bn/p alongside the dedicated plan previews. stage_deploy.py excludes
the whole preview workspace, so this cannot affect production.

The pages exercise the target information architecture—gallery, product hero,
plan hierarchy, official-provider reference, and bilingual routes—without
publishing prices or commerce controls.
"""
from __future__ import annotations

import html
import pathlib

from catalog_model import load_catalog
from routes_v3 import DOMAIN, strip_price_tokens

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "_preview_v3"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def safe_label(value: object, language: str) -> str:
    value = strip_price_tokens(value)
    return value or ("প্ল্যান" if language == "bn" else "Plan")


def gallery_html(product: dict, language: str) -> str:
    items = []
    for media in product.get("media_v3", []):
        role = media.get("role", "gallery")
        if media.get("type") == "image":
            alt = media.get("alt", {}).get(language) or media.get("alt", {}).get("en") or product.get("name")
            items.append(
                f'<figure class="v3-media" data-media-id="{esc(media.get("media_id"))}" data-role="{esc(role)}">'
                f'<img src="{esc(media.get("src"))}" alt="{esc(alt)}" '
                f'width="{esc(media.get("width") or 1200)}" height="{esc(media.get("height") or 630)}" '
                f'loading="{"eager" if not items else "lazy"}" decoding="async">'
                f'</figure>'
            )
        elif media.get("type") == "video":
            label = "ভিডিও" if language == "bn" else "Video"
            items.append(
                f'<div class="v3-media v3-video" data-media-id="{esc(media.get("media_id"))}" '
                f'data-source="{esc(media.get("source"))}"><strong>{label}</strong><span>{esc(media.get("caption", {}).get(language) or media.get("caption", {}).get("en"))}</span></div>'
            )
    return "".join(items)


def plan_cards(product: dict, language: str) -> str:
    cards = []
    bn = language == "bn"
    for plan in product.get("plans", []):
        label = safe_label(plan.get("label"), language)
        route = plan["routes_v3"][language]
        relative_href = f"{product['id']}/{pathlib.Path(route).name}"
        state = plan.get("commercial_state_v3", "unknown")
        state_text = {
            "allowed": "যাচাইকৃত" if bn else "Verified",
            "direct_provider_only": "অফিসিয়াল প্রোভাইডার" if bn else "Official provider only",
            "blocked": "উপলভ্য নয়" if bn else "Unavailable",
            "unknown": "যাচাই বাকি" if bn else "Verification pending",
        }.get(state, "যাচাই বাকি" if bn else "Verification pending")
        details = "প্ল্যানের বিস্তারিত" if bn else "Plan details"
        duration_label = "সময়কাল" if bn else "Duration"
        cards.append(f"""
        <article class="v3-plan" data-plan-id="{esc(plan['plan_id_v3'])}" data-commercial-state="{esc(state)}">
          <div><h3>{esc(label)}</h3><p><strong>{duration_label}:</strong> {esc(plan.get('duration', ''))}</p><span class="v3-state">{esc(state_text)}</span></div>
          <a class="v3-link" href="{esc(relative_href)}">{details} →</a>
        </article>""")
    return "".join(cards)


def page(product: dict, language: str) -> str:
    bn = language == "bn"
    name = product.get("name", product["id"])
    category = product.get("category", "")
    current_url = f"{DOMAIN}/{product['routes_v3'][language]}"
    alternate_language = "en" if bn else "bn"
    alternate_url = f"{DOMAIN}/{product['routes_v3'][alternate_language]}"
    x_default_url = f"{DOMAIN}/{product['routes_v3']['en']}"
    official_url = product.get("official_url")

    if bn:
        title = f"{name} — প্রোডাক্ট ও প্ল্যান | SAVEONSUB"
        desc = f"{name} এর প্রোডাক্ট তথ্য, মিডিয়া ও আলাদা প্ল্যান পেজের v3 প্রিভিউ। বাণিজ্যিক সুবিধা যাচাই সাপেক্ষ।"
        verification = "প্রোভাইডার/বাণিজ্যিক যাচাই শেষ না হওয়া পর্যন্ত এই প্রিভিউতে দাম বা অর্ডার কন্ট্রোল প্রকাশ করা হয় না।"
        plans_title = "প্ল্যানসমূহ"
        media_title = "প্রোডাক্ট মিডিয়া"
        official_label = "অফিসিয়াল প্রোভাইডার যাচাই করুন ↗"
        architecture_title = "v3 প্রোডাক্ট আর্কিটেকচার"
        architecture_copy = "এই পেজটি বর্তমান প্রোডাক্ট URL, বাংলা/ইংরেজি SEO কাঠামো এবং Python/static stack অপরিবর্তিত রেখে ভবিষ্যৎ ecommerce gallery ও plan hierarchy পরীক্ষা করে।"
    else:
        title = f"{name} — Product & Plans | SAVEONSUB"
        desc = f"V3 preview for {name}: ecommerce media gallery, product information and dedicated plan pages. Commerce remains verification-gated."
        verification = "Prices and order controls are intentionally unpublished here until provider and commercial verification is complete."
        plans_title = "Available plan identities"
        media_title = "Product media"
        official_label = "Verify at official provider ↗"
        architecture_title = "V3 product architecture"
        architecture_copy = "This preview tests the future ecommerce gallery and plan hierarchy while preserving the current product URL, bilingual SEO structure and Python/static stack."

    official_link = ""
    if official_url:
        official_link = f'<a class="v3-btn" href="{esc(official_url)}" target="_blank" rel="noopener nofollow">{official_label}</a>'

    styles = """
    <style>
    .v3-shell{max-width:1120px;margin:auto;padding:28px 18px 64px}.v3-badge{display:inline-block;padding:6px 10px;border:1px solid currentColor;border-radius:999px;font-size:12px}.v3-hero{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(300px,.95fr);gap:34px;align-items:center;margin-top:20px}.v3-gallery{display:grid;grid-template-columns:1fr;gap:12px}.v3-media{margin:0;border-radius:18px;overflow:hidden;background:#0b2224}.v3-media img{display:block;width:100%;height:auto}.v3-video{padding:32px;min-height:180px;display:flex;flex-direction:column;justify-content:center}.v3-section{margin-top:36px}.v3-plans{display:grid;gap:12px}.v3-plan{border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:18px;display:flex;justify-content:space-between;gap:18px;align-items:center}.v3-plan h3{margin:0 0 8px}.v3-state{font-size:12px;opacity:.75}.v3-link,.v3-btn{display:inline-block;padding:10px 14px;border-radius:10px;text-decoration:none;border:1px solid rgba(255,255,255,.2)}.v3-notice{padding:16px;border-radius:14px;background:rgba(255,182,72,.08);border:1px solid rgba(255,182,72,.3)}@media(max-width:760px){.v3-hero{grid-template-columns:1fr}.v3-plan{align-items:flex-start;flex-direction:column}}
    </style>
    """

    return f"""<!DOCTYPE html>
<html lang="{'bn' if bn else 'en'}">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{esc(current_url)}">
<link rel="alternate" hreflang="{'bn-bd' if bn else 'en-bd'}" href="{esc(current_url)}">
<link rel="alternate" hreflang="{'en-bd' if bn else 'bn-bd'}" href="{esc(alternate_url)}">
<link rel="alternate" hreflang="x-default" href="{esc(x_default_url)}">
<link rel="stylesheet" href="/assets/style.css">{styles}
<meta name="theme-color" content="#06181a">
</head>
<body data-v3-preview="true" data-product-id="{esc(product['id'])}">
<main><div class="v3-shell">
  <span class="v3-badge">{esc(category)}</span>
  <div class="v3-hero">
    <div class="v3-gallery" aria-label="{esc(media_title)}">{gallery_html(product, language)}</div>
    <div><h1>{esc(name)}</h1><p>{esc(desc)}</p><div class="v3-notice">{esc(verification)}</div><p>{official_link}</p></div>
  </div>
  <section class="v3-section"><h2>{esc(plans_title)}</h2><div class="v3-plans">{plan_cards(product, language)}</div></section>
  <section class="v3-section"><h2>{esc(architecture_title)}</h2><p>{esc(architecture_copy)}</p></section>
</div></main>
</body>
</html>
"""


def main() -> int:
    if not DEST.exists():
        raise SystemExit("_preview_v3 does not exist; run build_plan_pages_v3.py first")
    catalog = load_catalog()
    en = 0
    bn = 0
    for product in catalog.get("products", []):
        for language in ("en", "bn"):
            rel = pathlib.Path(product["routes_v3"][language])
            out = DEST / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(product, language), encoding="utf-8")
            if language == "en": en += 1
            else: bn += 1
    print(f"v3 product preview pages: EN={en} BN={bn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
