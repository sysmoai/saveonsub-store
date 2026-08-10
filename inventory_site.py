#!/usr/bin/env python3
"""Deterministic SAVEONSUB architecture/inventory census.

Read-only. No network calls and no writes outside docs/architecture when
--write is explicitly supplied. Intended to make every future development
change measurable before merge/deploy.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
CATALOG = ROOT / "catalog.json"
SITEMAP = ROOT / "sitemap.xml"
OUT_JSON = ROOT / "docs" / "architecture" / "site_inventory.json"
OUT_MD = ROOT / "docs" / "architecture" / "SAVEONSUB_SITE_INVENTORY.md"

EXCLUDED_DIRS = {".git", "_site", "node_modules", "__pycache__"}


def visible_files(pattern: str):
    out = []
    for path in ROOT.glob(pattern):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.is_file():
            out.append(path)
    return sorted(out)


def stems(pattern: str):
    return {p.stem for p in visible_files(pattern)}


def sitemap_urls():
    tree = ET.parse(SITEMAP)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [node.text.strip() for node in tree.findall("sm:url/sm:loc", ns) if node.text]


def route_group(url: str):
    path = url.split("saveonsub.com", 1)[-1].split("?", 1)[0]
    if path.startswith("/bn/p/"):
        return "product_bn"
    if path.startswith("/p/"):
        return "product_en"
    if path.startswith("/bn/c/"):
        return "category_bn"
    if path.startswith("/c/"):
        return "category_en"
    if path.startswith("/blog/"):
        return "blog"
    return "other_indexable"


def collect():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    products = catalog.get("products", [])
    categories = catalog.get("categories", [])
    category_counts = collections.Counter(p.get("category") for p in products)

    html_files = visible_files("**/*.html")
    py_files = visible_files("*.py")
    js_files = visible_files("**/*.js")
    css_files = visible_files("**/*.css")
    social_png = visible_files("assets/social/*.png")
    urls = sitemap_urls()
    sitemap_groups = collections.Counter(route_group(u) for u in urls)

    catalog_id_list = [p.get("id") for p in products if p.get("id")]
    catalog_ids = set(catalog_id_list)
    duplicate_product_ids = sorted(k for k, v in collections.Counter(catalog_id_list).items() if v > 1)
    product_en = stems("p/*.html")
    product_bn = stems("bn/p/*.html")
    product_social = stems("assets/social/*.png")

    # Plan census. Current v1 catalog plans generally do not yet carry stable
    # plan IDs; these readiness metrics quantify the migration gap without
    # failing the existing site merely because v2 has not been introduced yet.
    plans = []
    for product in products:
        for plan in product.get("plans", []):
            plans.append((product, plan))

    plan_ids = [str(plan.get("id")) for _, plan in plans if plan.get("id")]
    plan_id_counts = collections.Counter(plan_ids)
    duplicate_plan_ids = sorted(k for k, v in plan_id_counts.items() if v > 1)
    plan_type_counts = collections.Counter(str(plan.get("type", "unknown")) for _, plan in plans)
    plan_tos_counts = collections.Counter(str(plan.get("tos", "unknown")) for _, plan in plans)
    product_status_counts = collections.Counter(str(p.get("status", "unknown")) for p in products)

    products_without_plans = sorted(p.get("id") for p in products if not p.get("plans"))
    products_with_media_field = sorted(p.get("id") for p in products if p.get("media"))
    products_with_gallery_field = sorted(p.get("id") for p in products if p.get("gallery"))
    products_with_video_field = sorted(p.get("id") for p in products if p.get("video") or p.get("videos"))

    # Target dedicated plan routes are nested below the existing product slug.
    # These should remain zero until the v3 plan-page generator is introduced.
    plan_pages_en = visible_files("p/*/*.html")
    plan_pages_bn = visible_files("bn/p/*/*.html")

    route_files = {
        "root_html": len(visible_files("*.html")),
        "product_en": len(visible_files("p/*.html")),
        "product_bn": len(visible_files("bn/p/*.html")),
        "plan_en": len(plan_pages_en),
        "plan_bn": len(plan_pages_bn),
        "category_en": len(visible_files("c/*.html")),
        "category_bn": len(visible_files("bn/c/*.html")),
        "blog": len(visible_files("blog/*.html")),
        "mode_detail": len(visible_files("modes/*.html")),
        "bn_general": len(visible_files("bn/*.html")),
    }

    parity = {
        "duplicate_product_ids": duplicate_product_ids,
        "catalog_missing_en_page": sorted(catalog_ids - product_en),
        "en_page_missing_catalog": sorted(product_en - catalog_ids),
        "catalog_missing_bn_page": sorted(catalog_ids - product_bn),
        "bn_page_missing_catalog": sorted(product_bn - catalog_ids),
        "catalog_missing_social_png": sorted(catalog_ids - product_social),
        "social_png_missing_catalog": sorted(product_social - catalog_ids),
    }

    readiness = {
        "products_without_plans": products_without_plans,
        "plans_with_stable_id": len(plan_ids),
        "plans_missing_stable_id": len(plans) - len(plan_ids),
        "duplicate_plan_ids": duplicate_plan_ids,
        "products_with_media_field": len(products_with_media_field),
        "products_with_gallery_field": len(products_with_gallery_field),
        "products_with_video_field": len(products_with_video_field),
        "dedicated_plan_pages_en": len(plan_pages_en),
        "dedicated_plan_pages_bn": len(plan_pages_bn),
    }

    data = {
        "repository": "sysmoai/saveonsub-store",
        "domain": "https://saveonsub.com/",
        "architecture": "Python-generated committed static HTML + browser JS/localStorage + PWA service worker; staged to _site for Cloudflare Pages",
        "counts": {
            "html_files_total": len(html_files),
            "sitemap_urls_total": len(urls),
            "products": len(products),
            "plans": len(plans),
            "categories": len(categories),
            "python_scripts_root": len(py_files),
            "javascript_files": len(js_files),
            "css_files": len(css_files),
            "product_social_png": len(social_png),
        },
        "route_files": route_files,
        "sitemap_groups": dict(sorted(sitemap_groups.items())),
        "category_product_counts": {c: category_counts.get(c, 0) for c in categories},
        "product_status_counts": dict(sorted(product_status_counts.items())),
        "plan_type_counts": dict(sorted(plan_type_counts.items())),
        "plan_tos_counts": dict(sorted(plan_tos_counts.items())),
        "readiness": readiness,
        "parity": parity,
    }
    return data


def markdown(data):
    c = data["counts"]
    lines = [
        "# SAVEONSUB Site Inventory",
        "",
        "> Generated by `python3 inventory_site.py --write`. Do not hand-edit counts.",
        "",
        "## Core census",
        "",
        f"- HTML files: **{c['html_files_total']}**",
        f"- Sitemap/indexable URLs: **{c['sitemap_urls_total']}**",
        f"- Catalog products: **{c['products']}**",
        f"- Catalog plans: **{c['plans']}**",
        f"- Catalog categories: **{c['categories']}**",
        f"- Product social images: **{c['product_social_png']}**",
        f"- Root Python scripts: **{c['python_scripts_root']}**",
        f"- JavaScript files: **{c['javascript_files']}**",
        f"- CSS files: **{c['css_files']}**",
        "",
        "## HTML route files",
        "",
    ]
    for key, value in data["route_files"].items():
        lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## Sitemap groups", ""]
    for key, value in data["sitemap_groups"].items():
        lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## Product distribution", ""]
    for key, value in data["category_product_counts"].items():
        lines.append(f"- {key}: **{value}**")
    lines += ["", "## Plan distribution", ""]
    for key, value in data["plan_type_counts"].items():
        lines.append(f"- type `{key}`: **{value}**")
    for key, value in data["plan_tos_counts"].items():
        lines.append(f"- tos `{key}`: **{value}**")
    lines += ["", "## v3 readiness", ""]
    for key, value in data["readiness"].items():
        if isinstance(value, list):
            lines.append(f"- `{key}`: {', '.join(value) if value else 'none'}")
        else:
            lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## Product parity", ""]
    bad = False
    for key, values in data["parity"].items():
        if values:
            bad = True
            lines.append(f"- `{key}`: {', '.join(values)}")
    if not bad:
        lines.append("- Catalog IDs, EN product pages, BN product pages, and product social PNGs are in parity.")
    lines += [
        "",
        "## Safety rule",
        "",
        "Any future product addition/removal must keep catalog, EN/BN product routes, sitemap, category counts and social assets in parity before merge.",
        "Plan IDs/media fields are readiness metrics until the v3 normalized model is introduced; they become hard gates only after migration activation.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write docs/architecture inventory files")
    args = parser.parse_args()

    data = collect()
    print(json.dumps(data, ensure_ascii=False, indent=2))

    bad_parity = {k: v for k, v in data["parity"].items() if v}
    if args.write:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUT_MD.write_text(markdown(data), encoding="utf-8")
        print(f"wrote {OUT_JSON.relative_to(ROOT)}")
        print(f"wrote {OUT_MD.relative_to(ROOT)}")

    if bad_parity:
        print("inventory parity failure", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())