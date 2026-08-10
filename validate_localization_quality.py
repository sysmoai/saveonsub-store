#!/usr/bin/env python3
"""Fail-closed localization contract for SAVEONSUB strict EN/BN discovery."""
from __future__ import annotations

import json
import pathlib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
DOMAIN = "https://saveonsub.com"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.canonical = ""
        self.alternates: dict[str, str] = {}
        self.anchors: list[str] = []
        self.jsonld_parts: list[str] = []
        self.jsonld: list[dict | list] = []
        self.in_jsonld = False

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "html":
            self.lang = a.get("lang", "").lower()
        elif tag == "a" and a.get("href"):
            self.anchors.append(a["href"])
        elif tag == "link":
            rel = {x.lower() for x in a.get("rel", "").split()}
            if "canonical" in rel:
                self.canonical = a.get("href", "")
            if "alternate" in rel and a.get("hreflang"):
                self.alternates[a["hreflang"].lower()] = a.get("href", "")
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.jsonld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.in_jsonld:
            raw = "".join(self.jsonld_parts).strip()
            if raw:
                try:
                    self.jsonld.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    fail(f"malformed JSON-LD in localization page: {exc}")
            self.in_jsonld = False
            self.jsonld_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self.jsonld_parts.append(data)


def parse(rel: str) -> Parser:
    path = SITE / rel
    if not path.is_file():
        fail(f"missing localization page: {rel}")
        return Parser()
    parser = Parser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    return parser


def top_itemlists(documents: list[dict | list]) -> list[dict]:
    found: list[dict] = []
    for doc in documents:
        nodes = doc if isinstance(doc, list) else [doc]
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") == "ItemList":
                found.append(node)
    return found


def sitemap_urls() -> set[str]:
    path = SITE / "sitemap.xml"
    if not path.is_file():
        fail("sitemap.xml missing")
        return set()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.parse(path).getroot()
    return {n.text.strip() for n in root.findall("sm:url/sm:loc", ns) if n.text}


def manifest_value(key: str) -> str | None:
    path = SITE / "BUILD-MANIFEST.txt"
    if not path.is_file():
        fail("BUILD-MANIFEST.txt missing")
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    fail(f"BUILD-MANIFEST.txt missing {key}")
    return None


def validate_catalog_page(rel: str, language: str) -> set[str]:
    parser = parse(rel)
    expected_canonical = f"{DOMAIN}/{rel}"
    expected_en = f"{DOMAIN}/all.html"
    expected_bn = f"{DOMAIN}/bn/all.html"
    if parser.lang != language:
        fail(f"{rel}: html lang={parser.lang!r}, expected {language!r}")
    if parser.canonical != expected_canonical:
        fail(f"{rel}: canonical mismatch")
    if parser.alternates.get("en-bd") != expected_en:
        fail(f"{rel}: en-bd alternate mismatch")
    if parser.alternates.get("bn-bd") != expected_bn:
        fail(f"{rel}: bn-bd alternate mismatch")
    if parser.alternates.get("x-default") != expected_en:
        fail(f"{rel}: x-default alternate mismatch")

    prefix = "/bn/p/" if language == "bn" else "/p/"
    product_links = {
        href for href in parser.anchors
        if href.startswith(prefix) and href.count("/") == prefix.count("/") and href.endswith(".html")
    }
    if len(product_links) != 72:
        fail(f"{rel}: expected 72 distinct product links, found {len(product_links)}")

    itemlists = top_itemlists(parser.jsonld)
    if len(itemlists) != 1:
        fail(f"{rel}: expected exactly one ItemList schema, found {len(itemlists)}")
    else:
        items = itemlists[0].get("itemListElement")
        if not isinstance(items, list) or len(items) != 72:
            fail(f"{rel}: ItemList must contain exactly 72 products")
        else:
            schema_urls = {str(item.get("url") or "") for item in items if isinstance(item, dict)}
            expected_prefix = f"{DOMAIN}{prefix}"
            if len(schema_urls) != 72 or any(not url.startswith(expected_prefix) for url in schema_urls):
                fail(f"{rel}: ItemList URLs do not match {language} product routes")
    return product_links


def validate_bangla_navigation() -> int:
    candidates = [SITE / "bn.html"]
    bn_root = SITE / "bn"
    if bn_root.is_dir():
        candidates.extend(sorted(bn_root.rglob("*.html")))
    checked = 0
    for path in candidates:
        if not path.is_file():
            continue
        checked += 1
        parser = Parser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        if "/all.html" in parser.anchors:
            fail(f"{path.relative_to(SITE)}: Bangla page still links navigation directly to English /all.html")
        if "/bn/all.html" not in parser.anchors and path.relative_to(SITE).as_posix() != "bn/all.html":
            fail(f"{path.relative_to(SITE)}: Bangla page lacks /bn/all.html catalog navigation")
    return checked


def main() -> int:
    if not SITE.is_dir():
        print("localization quality blocked: _site missing")
        return 1

    en_links = validate_catalog_page("all.html", "en")
    bn_links = validate_catalog_page("bn/all.html", "bn")
    if len(en_links) == 72 and len(bn_links) == 72:
        en_ids = {pathlib.PurePosixPath(x).stem for x in en_links}
        bn_ids = {pathlib.PurePosixPath(x).stem for x in bn_links}
        if en_ids != bn_ids:
            fail("EN/BN catalog product identity sets differ")

    urls = sitemap_urls()
    for required in (f"{DOMAIN}/all.html", f"{DOMAIN}/bn/all.html"):
        if required not in urls:
            fail(f"sitemap missing bilingual catalog URL: {required}")
    if len(urls) != 179:
        fail(f"expected 179 sitemap URLs after BN catalog addition, found {len(urls)}")

    if manifest_value("indexable_urls") != "179":
        fail("BUILD-MANIFEST indexable_urls must be 179")

    sw = (SITE / "sw.js").read_text(encoding="utf-8", errors="replace") if (SITE / "sw.js").is_file() else ""
    if "'/all.html'" not in sw or "'/bn/all.html'" not in sw:
        fail("service worker core must include both EN and BN catalog indexes")

    checked_bn = validate_bangla_navigation()

    if errors:
        print(f"LOCALIZATION QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "localization_quality": "PASS",
        "english_catalog_products": 72,
        "bangla_catalog_products": 72,
        "sitemap_urls": 179,
        "bangla_pages_navigation_checked": checked_bn,
        "catalog_hreflang_pairs": 1,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
