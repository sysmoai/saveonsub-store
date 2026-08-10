#!/usr/bin/env python3
"""Require safe, visible, non-commercial structured data in SAVEONSUB strict L1."""
from __future__ import annotations

import json
import pathlib
import re
import urllib.parse
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
        self.in_jsonld = False
        self.jsonld_parts: list[str] = []
        self.jsonld: list[dict | list] = []
        self.visible_parts: list[str] = []
        self.hidden_depth = 0
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
            self.jsonld_parts = []
        elif tag in {"script", "style", "noscript", "template"}:
            self.hidden_depth += 1
        elif tag == "link":
            rel = {x.lower() for x in a.get("rel", "").split()}
            if "canonical" in rel:
                self.canonical = a.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self.in_jsonld:
            raw = "".join(self.jsonld_parts).strip()
            if raw:
                try:
                    self.jsonld.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    fail(f"malformed JSON-LD: {exc}")
            self.in_jsonld = False
            self.jsonld_parts = []
        elif tag in {"script", "style", "noscript", "template"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self.jsonld_parts.append(data)
        elif self.hidden_depth == 0:
            self.visible_parts.append(data)

    def visible_text(self) -> str:
        return normalize(" ".join(self.visible_parts))


def normalize(value: object) -> str:
    return " ".join(str(value or "").split()).casefold()


def url_to_rel(url: str) -> str | None:
    parsed = urllib.parse.urlsplit(str(url or ""))
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc and parsed.netloc.lower() != "saveonsub.com":
        return None
    path = urllib.parse.unquote(parsed.path or "/")
    if path == "/":
        return "index.html"
    rel = path.lstrip("/")
    if rel.endswith("/"):
        rel += "index.html"
    return rel


def node_types(data: object) -> set[str]:
    out: set[str] = set()
    stack = [data]
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


def top_level_nodes(documents: list[dict | list], wanted: str) -> list[dict]:
    found: list[dict] = []
    for doc in documents:
        nodes = doc if isinstance(doc, list) else [doc]
        for node in nodes:
            if isinstance(node, dict):
                typ = node.get("@type")
                types = typ if isinstance(typ, list) else [typ]
                if wanted in types:
                    found.append(node)
    return found


def route_family(rel: str) -> str:
    normalized = rel[3:] if rel.startswith("bn/") else rel
    parts = pathlib.PurePosixPath(normalized).parts
    if rel in {"index.html", "bn.html"}:
        return "home"
    if rel == "all.html":
        return "all"
    if rel == "faq.html":
        return "faq"
    if len(parts) == 2 and parts[0] == "p" and parts[1].endswith(".html"):
        return "product"
    if len(parts) == 3 and parts[0] == "p" and parts[2].endswith(".html"):
        return "plan"
    if len(parts) == 2 and parts[0] == "c" and parts[1].endswith(".html"):
        return "category"
    return "other"


def require_visible(value: object, visible: str, rel: str, field: str) -> None:
    needle = normalize(value)
    if needle and needle not in visible:
        fail(f"{rel}: schema {field} is not visibly supported on page: {value!r}")


def validate_target(url: object, rel: str, field: str) -> None:
    target = url_to_rel(str(url or ""))
    if target is None:
        fail(f"{rel}: schema {field} uses unsupported URL: {url!r}")
        return
    if not (SITE / target).is_file():
        fail(f"{rel}: schema {field} target missing: {url!r} -> {target}")


def validate_product(nodes: list[dict], visible: str, canonical: str, rel: str) -> None:
    if len(nodes) != 1:
        fail(f"{rel}: expected exactly one Product schema, found {len(nodes)}")
        return
    node = nodes[0]
    for forbidden in ("offers", "aggregateRating", "review"):
        if forbidden in node:
            fail(f"{rel}: Product schema contains authority-sensitive field {forbidden}")
    require_visible(node.get("name"), visible, rel, "Product.name")
    require_visible(node.get("category"), visible, rel, "Product.category")
    if node.get("url") != canonical:
        fail(f"{rel}: Product.url must equal canonical")


def validate_item_list(nodes: list[dict], rel: str) -> None:
    if len(nodes) != 1:
        fail(f"{rel}: expected exactly one ItemList schema, found {len(nodes)}")
        return
    node = nodes[0]
    items = node.get("itemListElement")
    if not isinstance(items, list) or not items:
        fail(f"{rel}: ItemList must have non-empty itemListElement")
        return
    if node.get("numberOfItems") != len(items):
        fail(f"{rel}: ItemList numberOfItems mismatch")
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            fail(f"{rel}: ItemList entry {index} is not an object")
            continue
        if item.get("position") != index:
            fail(f"{rel}: ItemList positions must be contiguous")
        validate_target(item.get("url") or item.get("item"), rel, f"ItemList[{index}]")


def validate_breadcrumb(nodes: list[dict], visible: str, rel: str) -> None:
    if len(nodes) != 1:
        fail(f"{rel}: expected exactly one BreadcrumbList schema, found {len(nodes)}")
        return
    items = nodes[0].get("itemListElement")
    if not isinstance(items, list) or len(items) < 2:
        fail(f"{rel}: BreadcrumbList must have at least two items")
        return
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            fail(f"{rel}: breadcrumb {index} is not an object")
            continue
        if item.get("position") != index:
            fail(f"{rel}: BreadcrumbList positions must be contiguous")
        require_visible(item.get("name"), visible, rel, f"BreadcrumbList[{index}].name")
        validate_target(item.get("item"), rel, f"BreadcrumbList[{index}].item")


def validate_faq(nodes: list[dict], visible: str, rel: str) -> None:
    if len(nodes) != 1:
        fail(f"{rel}: expected exactly one FAQPage schema, found {len(nodes)}")
        return
    entities = nodes[0].get("mainEntity")
    if not isinstance(entities, list) or len(entities) < 2:
        fail(f"{rel}: FAQPage must contain at least two questions")
        return
    for index, question in enumerate(entities, start=1):
        if not isinstance(question, dict) or question.get("@type") != "Question":
            fail(f"{rel}: FAQ entity {index} is not a Question")
            continue
        require_visible(question.get("name"), visible, rel, f"FAQ[{index}].question")
        answer = question.get("acceptedAnswer")
        if not isinstance(answer, dict) or answer.get("@type") != "Answer":
            fail(f"{rel}: FAQ entity {index} missing accepted Answer")
            continue
        require_visible(answer.get("text"), visible, rel, f"FAQ[{index}].answer")


def validate_page(path: pathlib.Path) -> None:
    rel = path.relative_to(SITE).as_posix()
    family = route_family(rel)
    if family == "other":
        return
    parser = Parser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    visible = parser.visible_text()
    all_types: set[str] = set()
    for document in parser.jsonld:
        all_types.update(node_types(document))
    forbidden = all_types.intersection({"Offer", "AggregateOffer", "AggregateRating", "Review"})
    if forbidden:
        fail(f"{rel}: forbidden commercial/proof schema types: {sorted(forbidden)}")

    required: set[str]
    if family == "home":
        required = {"WebSite"}
    elif family == "all":
        required = {"ItemList"}
    elif family == "faq":
        required = {"FAQPage"}
    elif family == "product":
        required = {"Product", "BreadcrumbList"}
    elif family == "plan":
        required = {"WebPage", "BreadcrumbList"}
    else:
        required = {"ItemList", "BreadcrumbList"}
    missing = required - all_types
    if missing:
        fail(f"{rel}: missing required schema types: {sorted(missing)}")

    if family == "product":
        validate_product(top_level_nodes(parser.jsonld, "Product"), visible, parser.canonical, rel)
        validate_breadcrumb(top_level_nodes(parser.jsonld, "BreadcrumbList"), visible, rel)
    elif family == "plan":
        validate_breadcrumb(top_level_nodes(parser.jsonld, "BreadcrumbList"), visible, rel)
        pages = top_level_nodes(parser.jsonld, "WebPage")
        if len(pages) != 1:
            fail(f"{rel}: expected exactly one WebPage schema, found {len(pages)}")
        elif pages[0].get("url") != parser.canonical:
            fail(f"{rel}: WebPage.url must equal canonical")
    elif family in {"all", "category"}:
        validate_item_list(top_level_nodes(parser.jsonld, "ItemList"), rel)
        if family == "category":
            validate_breadcrumb(top_level_nodes(parser.jsonld, "BreadcrumbList"), visible, rel)
    elif family == "faq":
        validate_faq(top_level_nodes(parser.jsonld, "FAQPage"), visible, rel)
    elif family == "home":
        sites = top_level_nodes(parser.jsonld, "WebSite")
        if len(sites) != 1:
            fail(f"{rel}: expected exactly one WebSite schema, found {len(sites)}")
        elif sites[0].get("url") != parser.canonical:
            fail(f"{rel}: WebSite.url must equal canonical")


def main() -> int:
    if not SITE.is_dir():
        print("schema quality blocked: _site missing")
        return 1
    pages = sorted(SITE.rglob("*.html"))
    checked = 0
    for path in pages:
        if route_family(path.relative_to(SITE).as_posix()) != "other":
            checked += 1
            validate_page(path)
    if errors:
        print(f"SCHEMA QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "schema_quality": "PASS",
        "schema_pages_checked": checked,
        "forbidden_commercial_schema_types": 0,
        "hidden_schema_claims": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
