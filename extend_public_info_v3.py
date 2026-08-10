#!/usr/bin/env python3
"""Add safe bilingual discovery extensions to the strict SAVEONSUB L1 artifact."""
from __future__ import annotations

import pathlib
import xml.etree.ElementTree as ET

from build_public_info_v3 import DEST, esc, product_card, shell
from catalog_model import load_catalog
from routes_v3 import DOMAIN


def bn_all_page(catalog: dict) -> str:
    products = catalog.get("products", [])
    cards = "".join(product_card(p, "bn") for p in products)
    desc = f"বাংলাদেশ-কেন্দ্রিক {len(products)}টি ডিজিটাল সাবস্ক্রিপশন তথ্য, ক্যাটাগরি ও প্রোভাইডার-স্ট্যাটাস একসাথে দেখুন।"
    body = (
        '<div class="wrap" style="padding-top:30px;padding-bottom:50px">'
        '<span class="pill">সম্পূর্ণ ক্যাটালগ</span>'
        f'<h1>সব {len(products)}টি সাবস্ক্রিপশন</h1>'
        '<p class="sub">'
        'SAVEONSUB-এর সম্পূর্ণ তথ্যভিত্তিক ক্যাটালগ দেখুন। যাচাইকৃত বিক্রয় মূল্য ও পেমেন্ট কন্ট্রোল আলাদাভাবে অনুমোদিত না হওয়া পর্যন্ত প্রকাশ করা হয় না।'
        '</p>'
        f'<div class="grid g3 mt3">{cards}</div></div>'
    )
    return shell(
        body,
        title=f"সব {len(products)}টি সাবস্ক্রিপশন | SAVEONSUB",
        desc=desc,
        canonical=f"{DOMAIN}/bn/all.html",
        language="bn",
        alternate=f"{DOMAIN}/all.html",
    )


def write_bn_catalog(catalog: dict) -> None:
    path = DEST / "bn" / "all.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bn_all_page(catalog), encoding="utf-8")


def rewire_bangla_catalog_links() -> int:
    changed = 0
    candidates = [DEST / "bn.html"]
    bn_root = DEST / "bn"
    if bn_root.is_dir():
        candidates.extend(sorted(bn_root.rglob("*.html")))
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new = text.replace('href="/all.html"', 'href="/bn/all.html"')
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def fix_english_catalog_hreflang() -> int:
    path = DEST / "all.html"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    old = f'<link rel="alternate" hreflang="bn-bd" href="{DOMAIN}/all.html">'
    new = f'<link rel="alternate" hreflang="bn-bd" href="{DOMAIN}/bn/all.html">'
    if old not in text:
        return 0
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return 1


def add_sitemap_url() -> int:
    path = DEST / "sitemap.xml"
    if not path.is_file():
        return 0
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    tree = ET.parse(path)
    root = tree.getroot()
    url = f"{DOMAIN}/bn/all.html"
    existing = {
        node.text.strip()
        for node in root.findall(f"{{{ns}}}url/{{{ns}}}loc")
        if node.text
    }
    if url in existing:
        return 0
    node = ET.SubElement(root, f"{{{ns}}}url")
    ET.SubElement(node, f"{{{ns}}}loc").text = url
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return 1


def update_build_manifest() -> int:
    path = DEST / "BUILD-MANIFEST.txt"
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    changed = 0
    for line in lines:
        if line.startswith("indexable_urls="):
            try:
                current = int(line.split("=", 1)[1])
            except ValueError:
                current = 0
            desired = max(current, 179)
            new_line = f"indexable_urls={desired}"
            changed += int(new_line != line)
            out.append(new_line)
        else:
            out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def update_service_worker() -> int:
    path = DEST / "sw.js"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    if "'/bn/all.html'" in text:
        return 0
    marker = "'/all.html'"
    if marker not in text:
        return 0
    new = text.replace(marker, "'/all.html','/bn/all.html'", 1)
    path.write_text(new, encoding="utf-8")
    return 1


def extend_public_info() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    catalog = load_catalog()
    write_bn_catalog(catalog)
    result = {
        "bn_catalog_written": 1,
        "bangla_pages_rewired": rewire_bangla_catalog_links(),
        "english_hreflang_fixed": fix_english_catalog_hreflang(),
        "sitemap_urls_added": add_sitemap_url(),
        "manifest_updated": update_build_manifest(),
        "service_worker_updated": update_service_worker(),
    }
    return result


def main() -> int:
    result = extend_public_info()
    print("extended strict L1 bilingual discovery:", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
