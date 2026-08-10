#!/usr/bin/env python3
"""Generate preview-only dedicated plan pages for SAVEONSUB v3.

Output lives under _preview_v3/, which stage_deploy.py explicitly excludes.
These pages are intentionally fail-closed:
- no prices;
- no Offer/AggregateOffer schema;
- no cart/order buttons;
- noindex,follow;
- commercial eligibility is shown as unverified unless explicitly authorized.

The purpose is to prove the complete EN/BN ecommerce route/template structure
without changing current public product pages.
"""
from __future__ import annotations

import html
import json
import pathlib
import shutil

from catalog_model import load_catalog
from routes_v3 import DOMAIN, product_url

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "_preview_v3"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def commercial_copy(state: str, language: str) -> tuple[str, str]:
    state = state or "unknown"
    if language == "bn":
        mapping = {
            "allowed": ("যাচাইকৃত", "এই প্ল্যানের বাণিজ্যিক যোগ্যতা আলাদাভাবে যাচাই করা হয়েছে।"),
            "direct_provider_only": ("অফিসিয়াল প্রোভাইডার", "এই প্ল্যানটি শুধুমাত্র অফিসিয়াল প্রোভাইডারের মাধ্যমে নেওয়ার জন্য দেখানো হচ্ছে।"),
            "blocked": ("উপলভ্য নয়", "এই প্ল্যানের বিক্রি বর্তমানে ব্লক করা আছে।"),
            "unknown": ("যাচাই বাকি", "প্রোভাইডার ও বাণিজ্যিক অনুমোদন যাচাই না হওয়া পর্যন্ত এই প্ল্যানের ক্রয় সুবিধা প্রকাশ করা হবে না।"),
        }
    else:
        mapping = {
            "allowed": ("Verified", "Commercial eligibility for this plan has been separately verified."),
            "direct_provider_only": ("Official provider only", "This plan is informational and should be obtained through the official provider."),
            "blocked": ("Unavailable", "Commerce for this plan is currently blocked."),
            "unknown": ("Verification pending", "Purchase controls stay unpublished until provider and commercial authority are verified."),
        }
    return mapping.get(state, mapping["unknown"])


def page(product: dict, plan: dict, language: str) -> str:
    bn = language == "bn"
    name = product.get("name", product["id"])
    label = plan.get("label", "Plan")
    duration = plan.get("duration", "")
    category = product.get("category", "")
    plan_id = plan["plan_id_v3"]
    plan_slug = plan["plan_slug_v3"]
    route = plan["routes_v3"][language]
    self_url = f"{DOMAIN}/{route}"
    parent_url = product_url(product["id"], language)
    alternate_language = "en" if bn else "bn"
    alternate_url = f"{DOMAIN}/{plan['routes_v3'][alternate_language]}"
    status_title, status_text = commercial_copy(plan.get("commercial_state_v3"), language)
    media = product.get("media_v3", [])[0] if product.get("media_v3") else None
    media_html = ""
    if media and media.get("type") == "image":
        alt = media.get("alt", {}).get(language) or media.get("alt", {}).get("en") or name
        width = media.get("width") or 1200
        height = media.get("height") or 630
        media_html = (
            f'<figure class="sos-v3-media"><img src="{esc(media.get("src"))}" '
            f'alt="{esc(alt)}" width="{esc(width)}" height="{esc(height)}" '
            f'loading="eager" decoding="async"></figure>'
        )

    official_url = product.get("official_url")
    official_link = ""
    if official_url:
        official_label = "অফিসিয়াল প্রোভাইডার যাচাই করুন ↗" if bn else "Verify at official provider ↗"
        official_link = f'<a class="btn btn-secondary" href="{esc(official_url)}" target="_blank" rel="noopener nofollow">{official_label}</a>'

    if bn:
        title = f"{name} — {label} | SAVEONSUB"
        desc = f"{name} {label} প্ল্যানের তথ্য, সময়কাল, ডেলিভারি ও প্রোভাইডার স্ট্যাটাস। ক্রয় সুবিধা যাচাই সাপেক্ষ।"
        lang_attr = "bn"
        breadcrumb = f'<a href="{esc(parent_url)}">{esc(name)}</a> › {esc(label)}'
        sections = f"""
        <section class="notice"><strong>{esc(status_title)}</strong><p>{esc(status_text)}</p></section>
        <section><h2>প্ল্যানের তথ্য</h2><dl class="sos-v3-specs">
          <div><dt>প্ল্যান আইডি</dt><dd><code>{esc(plan_id)}</code></dd></div>
          <div><dt>সময়কাল</dt><dd>{esc(duration)}</dd></div>
          <div><dt>ক্যাটাগরি</dt><dd>{esc(category)}</dd></div>
          <div><dt>ডেলিভারি SLA</dt><dd>{esc(plan.get('sla', 'যাচাই বাকি'))}</dd></div>
        </dl></section>
        <section><h2>কেন এই পেজ আলাদা?</h2><p>প্রতিটি SAVEONSUB প্ল্যানের নিজস্ব স্থায়ী পরিচয়, রুট, মিডিয়া এবং ভবিষ্যৎ অর্ডার রেফারেন্স থাকবে। মূল প্রোডাক্ট পেজ অপরিবর্তিত থাকবে।</p></section>
        <section class="sos-v3-actions"><a class="btn" href="{esc(parent_url)}">{esc(name)} প্রোডাক্ট পেজ</a>{official_link}</section>
        """
    else:
        title = f"{name} — {label} | SAVEONSUB"
        desc = f"Dedicated information page for the {name} {label} plan: duration, delivery and provider status. Purchase controls are verification-gated."
        lang_attr = "en"
        breadcrumb = f'<a href="{esc(parent_url)}">{esc(name)}</a> › {esc(label)}'
        sections = f"""
        <section class="notice"><strong>{esc(status_title)}</strong><p>{esc(status_text)}</p></section>
        <section><h2>Plan information</h2><dl class="sos-v3-specs">
          <div><dt>Plan ID</dt><dd><code>{esc(plan_id)}</code></dd></div>
          <div><dt>Duration</dt><dd>{esc(duration)}</dd></div>
          <div><dt>Category</dt><dd>{esc(category)}</dd></div>
          <div><dt>Delivery SLA</dt><dd>{esc(plan.get('sla', 'verification pending'))}</dd></div>
        </dl></section>
        <section><h2>Why this page is separate</h2><p>Every SAVEONSUB plan gets a stable identity, route, media association and future order reference while the existing parent product URL remains permanent.</p></section>
        <section class="sos-v3-actions"><a class="btn" href="{esc(parent_url)}">Back to {esc(name)}</a>{official_link}</section>
        """

    return f"""<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{esc(self_url)}">
<link rel="alternate" hreflang="{'bn-bd' if bn else 'en-bd'}" href="{esc(self_url)}">
<link rel="alternate" hreflang="{'en-bd' if bn else 'bn-bd'}" href="{esc(alternate_url)}">
<link rel="alternate" hreflang="x-default" href="{esc(plan['routes_v3']['en'] if plan['routes_v3']['en'].startswith('http') else DOMAIN + '/' + plan['routes_v3']['en'])}">
<link rel="stylesheet" href="/assets/style.css">
<meta name="theme-color" content="#06181a">
</head>
<body data-v3-preview="true" data-product-id="{esc(product['id'])}" data-plan-id="{esc(plan_id)}" data-plan-slug="{esc(plan_slug)}">
<main id="main"><div class="wrap" style="max-width:980px;padding-top:28px;padding-bottom:48px">
  <div class="crumbs">{breadcrumb}</div>
  <div class="sos-v3-hero" style="display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,1fr);gap:28px;align-items:center">
    <div>{media_html}</div>
    <div><span class="cat">{esc(category)}</span><h1>{esc(name)}</h1><h2 style="margin-top:8px">{esc(label)}</h2><p>{esc(desc)}</p></div>
  </div>
  {sections}
</div></main>
</body>
</html>
"""


def main() -> int:
    catalog = load_catalog()
    if DEST.exists():
        shutil.rmtree(DEST)
    en_count = 0
    bn_count = 0

    for product in catalog.get("products", []):
        for plan in product.get("plans", []):
            for language in ("en", "bn"):
                rel = pathlib.Path(plan["routes_v3"][language])
                out = DEST / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(page(product, plan, language), encoding="utf-8")
                if language == "en":
                    en_count += 1
                else:
                    bn_count += 1

    manifest = {
        "preview_only": True,
        "products": len(catalog.get("products", [])),
        "plans": sum(len(p.get("plans", [])) for p in catalog.get("products", [])),
        "en_plan_pages": en_count,
        "bn_plan_pages": bn_count,
        "public_deploy_excluded": True,
    }
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
