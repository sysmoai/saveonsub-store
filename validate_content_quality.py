#!/usr/bin/env python3
"""Fail-closed quality contract for SAVEONSUB source-backed resource content."""
from __future__ import annotations

import json
import pathlib
import re
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from routes_v3 import DOMAIN, slugify

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
SOURCE = ROOT / "content" / "resources_v1.json"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def normalize(value: object) -> str:
    return " ".join(str(value or "").split())


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.canonical = ""
        self.alternates: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []
        self.visible_parts: list[str] = []
        self.jsonld_docs: list[object] = []
        self.in_jsonld = False
        self.jsonld_parts: list[str] = []
        self.hidden_depth = 0
        self.h1 = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "html":
            self.lang = a.get("lang", "").lower()
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.links.append((a["href"], a.get("rel", "")))
        elif tag == "link":
            rel = {x.lower() for x in a.get("rel", "").split()}
            if "canonical" in rel:
                self.canonical = a.get("href", "")
            if "alternate" in rel and a.get("hreflang"):
                self.alternates[a["hreflang"].lower()] = a.get("href", "")
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.jsonld_parts = []
        elif tag in {"script", "style", "noscript", "template"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self.in_jsonld:
            raw = "".join(self.jsonld_parts).strip()
            if raw:
                try:
                    self.jsonld_docs.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    fail(f"resource JSON-LD invalid: {exc}")
            self.in_jsonld = False
            self.jsonld_parts = []
        elif tag in {"script", "style", "noscript", "template"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self.jsonld_parts.append(data)
        elif self.hidden_depth == 0:
            self.visible_parts.append(data)

    def visible(self) -> str:
        return normalize(" ".join(self.visible_parts))


def load_source() -> dict:
    if not SOURCE.is_file():
        fail("content/resources_v1.json missing")
        return {}
    try:
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"resource source JSON invalid: {exc}")
        return {}
    if data.get("schema") != "saveonsub-resources-v1":
        fail("resource schema mismatch")
    if data.get("editorial_owner") != "SAVEONSUB Admin":
        fail("editorial owner must be SAVEONSUB Admin")
    if not re.fullmatch(r"2026-\d{2}-\d{2}", str(data.get("checked_on") or "")):
        fail("checked_on must be an explicit 2026 ISO date")
    return data


def top_nodes(documents: list[object], wanted: str) -> list[dict]:
    found: list[dict] = []
    for doc in documents:
        stack = list(doc) if isinstance(doc, list) else [doc]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                typ = node.get("@type")
                types = typ if isinstance(typ, list) else [typ]
                if wanted in types:
                    found.append(node)
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return found


def all_types(documents: list[object]) -> set[str]:
    out: set[str] = set()
    stack = list(documents)
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            typ = node.get("@type")
            if isinstance(typ, str):
                out.add(typ)
            elif isinstance(typ, list):
                out.update(str(x) for x in typ)
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return out


def parse_page(rel: str) -> ResourceParser:
    path = SITE / rel
    if not path.is_file():
        fail(f"resource page missing: {rel}")
        return ResourceParser()
    parser = ResourceParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    return parser


def validate_source_article(article: dict, checked_on: str) -> None:
    slug = str(article.get("slug") or "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        fail(f"invalid resource slug: {slug!r}")
    if not article.get("sources"):
        fail(f"{slug}: sources required")
    for source in article.get("sources", []):
        url = str(source.get("url") or "")
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc:
            fail(f"{slug}: source must be absolute HTTPS URL: {url}")
        if not normalize(source.get("name")):
            fail(f"{slug}: source name missing")
    for language in ("en", "bn"):
        local = article.get(language) or {}
        title = normalize(local.get("title"))
        desc = normalize(local.get("description"))
        summary = normalize(local.get("summary"))
        sections = local.get("sections") or []
        if not title or len(title) < 20:
            fail(f"{slug}/{language}: title too short")
        if len(desc) < 80:
            fail(f"{slug}/{language}: description too short")
        if len(summary) < 100:
            fail(f"{slug}/{language}: summary too short")
        if len(sections) < 4:
            fail(f"{slug}/{language}: at least four sections required")
        words = []
        for section in sections:
            if not normalize(section.get("heading")):
                fail(f"{slug}/{language}: section heading missing")
            if len(section.get("paragraphs") or []) < 1:
                fail(f"{slug}/{language}: section paragraph missing")
            for paragraph in section.get("paragraphs") or []:
                words.extend(str(paragraph).split())
            for bullet in section.get("bullets") or []:
                words.extend(str(bullet).split())
        if len(words) < 220:
            fail(f"{slug}/{language}: content depth too low ({len(words)} words/tokens)")
        if checked_on not in str(checked_on):
            fail(f"{slug}/{language}: checked date invalid")


def validate_article_page(article: dict, language: str, checked_on: str) -> None:
    bn = language == "bn"
    slug = article["slug"]
    rel = f"bn/resources/{slug}.html" if bn else f"resources/{slug}.html"
    peer = f"resources/{slug}.html" if bn else f"bn/resources/{slug}.html"
    canonical = f"{DOMAIN}/{rel}"
    alternate = f"{DOMAIN}/{peer}"
    parser = parse_page(rel)
    visible = parser.visible()
    if parser.lang != ("bn" if bn else "en"):
        fail(f"{rel}: html language mismatch")
    if parser.h1 != 1:
        fail(f"{rel}: expected one h1, found {parser.h1}")
    if parser.canonical != canonical:
        fail(f"{rel}: canonical mismatch")
    if parser.alternates.get("en-bd") != (alternate if bn else canonical):
        fail(f"{rel}: en-bd hreflang mismatch")
    if parser.alternates.get("bn-bd") != (canonical if bn else alternate):
        fail(f"{rel}: bn-bd hreflang mismatch")
    if "SAVEONSUB Admin" not in visible:
        fail(f"{rel}: visible SAVEONSUB Admin credit missing")
    if checked_on not in visible:
        fail(f"{rel}: visible checked date missing")
    if normalize(article[language]["title"]) not in visible:
        fail(f"{rel}: source title not visible")

    hrefs = [href for href, _ in parser.links]
    expected_sources = [source["url"] for source in article.get("sources", [])]
    for url in expected_sources:
        if hrefs.count(url) != 1:
            fail(f"{rel}: source link parity failure for {url}")
    for category in article.get("related_categories", []):
        expected = f"/bn/c/{slugify(category)}.html" if bn else f"/c/{slugify(category)}.html"
        if expected not in hrefs:
            fail(f"{rel}: related category link missing: {expected}")

    article_nodes = top_nodes(parser.jsonld_docs, "Article")
    if len(article_nodes) != 1:
        fail(f"{rel}: expected one Article schema, found {len(article_nodes)}")
    else:
        node = article_nodes[0]
        if node.get("headline") != article[language]["title"]:
            fail(f"{rel}: Article headline mismatch")
        if node.get("datePublished") != checked_on or node.get("dateModified") != checked_on:
            fail(f"{rel}: Article dates mismatch")
        if node.get("mainEntityOfPage") != canonical:
            fail(f"{rel}: Article mainEntityOfPage mismatch")
        author = node.get("author") if isinstance(node.get("author"), dict) else {}
        if author.get("name") != "SAVEONSUB Admin":
            fail(f"{rel}: Article author credit mismatch")
        publisher = node.get("publisher") if isinstance(node.get("publisher"), dict) else {}
        if publisher.get("name") != "SAVEONSUB":
            fail(f"{rel}: Article publisher mismatch")

    forbidden_types = all_types(parser.jsonld_docs).intersection({"Offer", "AggregateOffer", "AggregateRating", "Review"})
    if forbidden_types:
        fail(f"{rel}: forbidden commercial/proof schema types: {sorted(forbidden_types)}")
    lower_visible = visible.lower()
    for token in ("whatsapp.com", "wa.me/", "checkout.html", "cartadd("):
        if token in lower_visible:
            fail(f"{rel}: forbidden commerce/contact token: {token}")


def validate_hub(data: dict, language: str) -> None:
    bn = language == "bn"
    rel = "bn/resources/index.html" if bn else "resources/index.html"
    canonical = f"{DOMAIN}/{rel}"
    alternate = f"{DOMAIN}/resources/index.html" if bn else f"{DOMAIN}/bn/resources/index.html"
    parser = parse_page(rel)
    visible = parser.visible()
    if parser.h1 != 1:
        fail(f"{rel}: expected one h1")
    if parser.canonical != canonical:
        fail(f"{rel}: canonical mismatch")
    if parser.alternates.get("bn-bd") != (canonical if bn else alternate):
        fail(f"{rel}: bn-bd alternate mismatch")
    if parser.alternates.get("en-bd") != (alternate if bn else canonical):
        fail(f"{rel}: en-bd alternate mismatch")
    if "SAVEONSUB Admin" not in visible or data["checked_on"] not in visible:
        fail(f"{rel}: editorial owner/date missing")
    hrefs = [href for href, _ in parser.links]
    for article in data["articles"]:
        expected = f"/bn/resources/{article['slug']}.html" if bn else f"/resources/{article['slug']}.html"
        if hrefs.count(expected) != 1:
            fail(f"{rel}: hub article link parity failure: {expected}")


def sitemap_urls() -> set[str]:
    path = SITE / "sitemap.xml"
    if not path.is_file():
        fail("sitemap.xml missing")
        return set()
    root = ET.parse(path).getroot()
    return {node.text.strip() for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc" and node.text}


def manifest_indexable() -> int | None:
    path = SITE / "BUILD-MANIFEST.txt"
    if not path.is_file():
        fail("BUILD-MANIFEST.txt missing")
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("indexable_urls="):
            try:
                return int(line.split("=", 1)[1])
            except ValueError:
                fail("BUILD-MANIFEST indexable_urls invalid")
                return None
    fail("BUILD-MANIFEST indexable_urls missing")
    return None


def main() -> int:
    if not SITE.is_dir():
        print("content quality blocked: _site missing")
        return 1
    data = load_source()
    if not data:
        return 1
    articles = data.get("articles") or []
    slugs = [str(article.get("slug") or "") for article in articles]
    if len(slugs) != len(set(slugs)):
        fail("resource slugs must be unique")
    checked_on = data["checked_on"]
    for article in articles:
        validate_source_article(article, checked_on)
        validate_article_page(article, "en", checked_on)
        validate_article_page(article, "bn", checked_on)
    validate_hub(data, "en")
    validate_hub(data, "bn")

    expected_urls = {f"{DOMAIN}/resources/index.html", f"{DOMAIN}/bn/resources/index.html"}
    for slug in slugs:
        expected_urls.add(f"{DOMAIN}/resources/{slug}.html")
        expected_urls.add(f"{DOMAIN}/bn/resources/{slug}.html")
    actual_sitemap = sitemap_urls()
    missing = expected_urls - actual_sitemap
    if missing:
        fail(f"resource sitemap URLs missing: {sorted(missing)}")
    expected_total = 179 + len(expected_urls)
    if len(actual_sitemap) != expected_total:
        fail(f"sitemap total mismatch: {len(actual_sitemap)} != {expected_total}")
    manifest_count = manifest_indexable()
    if manifest_count != len(actual_sitemap):
        fail(f"manifest/sitemap count mismatch: {manifest_count} != {len(actual_sitemap)}")

    if errors:
        print(f"CONTENT QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "content_quality": "PASS",
        "editorial_owner": data["editorial_owner"],
        "checked_on": checked_on,
        "resource_articles": len(articles),
        "resource_pages": len(expected_urls),
        "bilingual_article_pages": len(articles) * 2,
        "resource_hubs": 2,
        "sitemap_urls": len(actual_sitemap),
        "article_schema_errors": 0,
        "source_link_errors": 0,
        "commerce_schema_types": 0,
        "unsupported_admin_credits": 0,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
