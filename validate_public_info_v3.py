#!/usr/bin/env python3
"""Validate the generated SAVEONSUB L1 public-information artifact."""
from __future__ import annotations

import json
import pathlib
import re
import xml.etree.ElementTree as ET

from catalog_model import load_catalog

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "_public_v3"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def text_files():
    suffixes = {".html", ".js", ".css", ".xml", ".txt", ".svg", ".webmanifest", ""}
    for path in PUBLIC.rglob("*"):
        if path.is_file() and (path.suffix.lower() in suffixes or path.name in {"_headers", "_redirects"}):
            yield path


def sample_context(text: str, match: re.Match[str], radius: int = 70) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    sample = re.sub(r"\s+", " ", text[start:end]).strip()
    return sample[:220]


def main() -> int:
    if not PUBLIC.is_dir():
        fail("_public_v3 does not exist; run build_public_info_v3.py")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    catalog = load_catalog()
    products = catalog.get("products", [])
    plans = [plan for p in products for plan in p.get("plans", [])]

    expected = {
        "product_en": len(products),
        "product_bn": len(products),
        "plan_en": len(plans),
        "plan_bn": len(plans),
        "category_en": len(catalog.get("categories", [])),
        "category_bn": len(catalog.get("categories", [])),
    }
    actual = {
        "product_en": len(list(PUBLIC.glob("p/*.html"))),
        "product_bn": len(list(PUBLIC.glob("bn/p/*.html"))),
        "plan_en": len(list(PUBLIC.glob("p/*/*.html"))),
        "plan_bn": len(list(PUBLIC.glob("bn/p/*/*.html"))),
        "category_en": len(list(PUBLIC.glob("c/*.html"))),
        "category_bn": len(list(PUBLIC.glob("bn/c/*.html"))),
    }
    for key, value in expected.items():
        if actual[key] != value:
            fail(f"{key}: expected {value}, found {actual[key]}")

    required = [
        "index.html", "bn.html", "all.html", "about.html", "contact.html", "faq.html",
        "privacy.html", "terms.html", "404.html", "robots.txt", "sitemap.xml", "_headers",
        "_redirects", "sw.js", "assets/style.css", "assets/app.js", "assets/favicon.svg",
        "assets/site.webmanifest", "BUILD-MANIFEST.txt",
    ]
    for rel in required:
        if not (PUBLIC / rel).is_file():
            fail(f"missing required public file: {rel}")

    forbidden_patterns = {
        "BDT selling price": re.compile(r"৳\s*[0-9]|\b(?:BDT|Tk\.?)\s*[0-9][0-9,]*", re.I),
        "stale WhatsApp number": re.compile(r"(?:\+?880[ -]?1305[ -]?869242|8801305869242|01305869242)"),
        "WhatsApp destination": re.compile(r"(?:wa\.me/|api\.whatsapp\.com)", re.I),
        "cartAdd function": re.compile(r"cartAdd\s*\(", re.I),
        "checkout route": re.compile(r"checkout\.html", re.I),
        "cart button class": re.compile(r"class=[\"'][^\"']*cartbtn", re.I),
        "Offer schema": re.compile(r"[\"']@type[\"']\s*:\s*[\"'](?:Offer|AggregateOffer)[\"']", re.I),
        "raw catalog": re.compile(r"catalog\.json|assets/catalog\.js", re.I),
        "payment destination": re.compile(r"(?:merchant number|send money to|payment number|bank account number|bKash\s*(?:number|to)|Nagad\s*(?:number|to))", re.I),
        "unsupported proof": re.compile(r"\b[0-9]{2,}\+?\s*(?:orders|customers|users)|bestseller|lifetime orders", re.I),
        "shared commerce": re.compile(r"(?:shared-low|shared-med|buy shared|shared account|shared seat|shared subscription)", re.I),
        "unverified legal operator": re.compile(r"SYSmoAI Private Limited|operated by SYSmoAI|registered company", re.I),
    }

    findings = {name: [] for name in forbidden_patterns}
    examples = {name: [] for name in forbidden_patterns}
    for path in text_files():
        rel = path.relative_to(PUBLIC).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in forbidden_patterns.items():
            match = pattern.search(text)
            if match:
                findings[name].append(rel)
                if len(examples[name]) < 5:
                    examples[name].append({
                        "path": rel,
                        "matched": match.group(0),
                        "context": sample_context(text, match),
                    })

    for name, paths in findings.items():
        if paths:
            fail(f"forbidden {name} in {len(paths)} file(s): {', '.join(paths[:8])}")
            for example in examples[name]:
                print(
                    f"DIAG {name}: path={example['path']} matched={example['matched']!r} "
                    f"context={example['context']!r}"
                )

    json_files = [p.relative_to(PUBLIC).as_posix() for p in PUBLIC.rglob("*.json")]
    if json_files:
        fail(f"public JSON files present: {json_files[:10]}")

    for path in list(PUBLIC.glob("p/*/*.html")) + list(PUBLIC.glob("bn/p/*/*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if '<meta name="robots" content="noindex,follow">' not in text:
            fail(f"plan page missing noindex,follow: {path.relative_to(PUBLIC)}")

    for product in products:
        pid = product["id"]
        for language, rel in (("en", f"p/{pid}.html"), ("bn", f"bn/p/{pid}.html")):
            path = PUBLIC / rel
            if not path.is_file():
                continue
            expected_canonical = f"https://saveonsub.com/{rel}"
            text = path.read_text(encoding="utf-8", errors="replace")
            if f'<link rel="canonical" href="{expected_canonical}">' not in text:
                fail(f"canonical drift: {rel}")

    sitemap = PUBLIC / "sitemap.xml"
    sitemap_urls: list[str] = []
    if sitemap.is_file():
        tree = ET.parse(sitemap)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = [n.text.strip() for n in tree.findall("sm:url/sm:loc", ns) if n.text]
        if len(sitemap_urls) != len(set(sitemap_urls)):
            fail("duplicate sitemap URLs")
        plan_route_re = re.compile(r"/p/[^/]+/[^/]+\.html$")
        if any(plan_route_re.search(url) for url in sitemap_urls):
            fail("plan detail route appears in sitemap despite noindex policy")

    manifest_path = PUBLIC / "BUILD-MANIFEST.txt"
    manifest = {}
    if manifest_path.is_file():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                manifest[key] = value
        if manifest.get("release_mode") != "L1_PUBLIC_INFO_ONLY":
            fail("build manifest release_mode is not L1_PUBLIC_INFO_ONLY")
        for key in ("public_prices", "commerce_controls", "payment_destinations", "whatsapp_destinations"):
            if manifest.get(key) != "0":
                fail(f"build manifest {key} is not zero")

    if errors:
        print("DIAGNOSTIC SUMMARY")
        print(json.dumps({name: {"files": len(paths), "examples": examples[name]} for name, paths in findings.items() if paths}, ensure_ascii=False, indent=2))
        print(f"L1 PUBLIC ARTIFACT INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    print(json.dumps({
        "valid": True,
        "release_mode": "L1_PUBLIC_INFO_ONLY",
        "products": len(products),
        "plans": len(plans),
        "routes": actual,
        "sitemap_urls": len(sitemap_urls),
        "public_prices": 0,
        "commerce_controls": 0,
        "payment_destinations": 0,
        "whatsapp_destinations": 0,
        "forbidden_findings": {k: 0 for k in forbidden_patterns},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
