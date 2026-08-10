#!/usr/bin/env python3
"""Fail-closed static quality checks for the staged SAVEONSUB strict artifact."""
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
QUALITY = ROOT / "_release_meta" / "quality-manifest.json"
DOMAIN = "https://saveonsub.com"

MAX_TOTAL_BYTES = 5 * 1024 * 1024
MAX_HTML_BYTES = 128 * 1024
MAX_CSS_BYTES = 160 * 1024
MAX_JS_BYTES = 100 * 1024
MAX_IMAGE_BYTES = 512 * 1024

errors: list[str] = []
warnings: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def aggregate(entries: list[dict[str, object]]) -> str:
    h = hashlib.sha256()
    for item in sorted(entries, key=lambda x: str(x["path"])):
        h.update(str(item["path"]).encode("utf-8"))
        h.update(b"\0")
        h.update(str(item["size"]).encode("ascii"))
        h.update(b"\0")
        h.update(str(item["sha256"]).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang = ""
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.anchors: list[dict[str, str]] = []
        self.scripts: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.buttons: list[dict[str, object]] = []
        self.in_button: dict[str, object] | None = None
        self.h1_count = 0
        self.main_ids: list[str] = []
        self.skip_main = False
        self.jsonld: list[str] = []
        self.in_jsonld = False
        self.jsonld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "html":
            self.html_lang = a.get("lang", "").strip().lower()
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.meta.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "a":
            self.anchors.append(a)
            classes = set(a.get("class", "").split())
            if a.get("href") == "#main" and "skip" in classes:
                self.skip_main = True
        elif tag == "script":
            self.scripts.append(a)
            if a.get("type", "").lower() == "application/ld+json":
                self.in_jsonld = True
                self.jsonld_parts = []
        elif tag == "img":
            self.images.append(a)
        elif tag == "button":
            self.in_button = {"attrs": a, "text": []}
            self.buttons.append(self.in_button)
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_ids.append(a.get("id", ""))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "button":
            self.in_button = None
        elif tag == "script" and self.in_jsonld:
            self.jsonld.append("".join(self.jsonld_parts).strip())
            self.in_jsonld = False
            self.jsonld_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_button is not None:
            self.in_button["text"].append(data)
        if self.in_jsonld:
            self.jsonld_parts.append(data)

    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())

    def meta_value(self, key: str, value: str) -> str | None:
        key = key.lower()
        value = value.lower()
        for item in self.meta:
            if item.get(key, "").lower() == value:
                return item.get("content", "")
        return None

    def canonical(self) -> str | None:
        for item in self.links:
            rel = {x.lower() for x in item.get("rel", "").split()}
            if "canonical" in rel:
                return item.get("href", "")
        return None

    def alternates(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for item in self.links:
            rel = {x.lower() for x in item.get("rel", "").split()}
            if "alternate" in rel and item.get("hreflang"):
                out[item["hreflang"].lower()] = item.get("href", "")
        return out

    def refs(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for item in self.anchors:
            if item.get("href"):
                out.append(("href", item["href"]))
        for item in self.scripts:
            if item.get("src"):
                out.append(("src", item["src"]))
        for item in self.images:
            if item.get("src"):
                out.append(("src", item["src"]))
        for item in self.links:
            href = item.get("href", "")
            rel = {x.lower() for x in item.get("rel", "").split()}
            if href and rel.intersection({"stylesheet", "icon", "manifest", "preload"}):
                out.append(("href", href))
        return out


def rel_to_url(rel: str) -> str:
    if rel == "index.html":
        return f"{DOMAIN}/"
    return f"{DOMAIN}/{rel}"


def url_to_rel(url: str) -> str | None:
    parsed = urllib.parse.urlsplit(url)
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
    if pathlib.PurePosixPath(rel).suffix == "":
        html_candidate = f"{rel}.html"
        if (SITE / html_candidate).is_file():
            return html_candidate
    return rel


def bilingual_peer(rel: str) -> tuple[str, str] | None:
    if rel == "index.html":
        return ("index.html", "bn.html")
    if rel == "bn.html":
        return ("index.html", "bn.html")
    if rel.startswith("bn/p/"):
        return (rel[3:], rel)
    if rel.startswith("p/"):
        return (rel, f"bn/{rel}")
    if rel.startswith("bn/c/"):
        return (rel[3:], rel)
    if rel.startswith("c/"):
        return (rel, f"bn/{rel}")
    return None


def is_plan_route(rel: str) -> bool:
    normalized = rel[3:] if rel.startswith("bn/") else rel
    parts = pathlib.PurePosixPath(normalized).parts
    return len(parts) == 3 and parts[0] == "p" and parts[-1].endswith(".html")


def sitemap_set() -> set[str]:
    p = SITE / "sitemap.xml"
    if not p.is_file():
        fail("sitemap.xml is missing")
        return set()
    try:
        root = ET.parse(p).getroot()
    except ET.ParseError as exc:
        fail(f"sitemap.xml is malformed: {exc}")
        return set()
    out: set[str] = set()
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text:
            loc = node.text.strip()
            if loc in out:
                fail(f"duplicate sitemap URL: {loc}")
            out.add(loc)
    return out


def validate_manifest() -> dict:
    if not QUALITY.is_file():
        fail("private quality manifest is missing")
        return {}
    try:
        manifest = json.loads(QUALITY.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"quality manifest is invalid JSON: {exc}")
        return {}
    output = manifest.get("output") or {}
    current_files = []
    for p in sorted(x for x in SITE.rglob("*") if x.is_file()):
        current_files.append({
            "path": p.relative_to(SITE).as_posix(),
            "size": p.stat().st_size,
            "sha256": sha256_file(p),
        })
    actual_tree = aggregate(current_files)
    if output.get("tree_sha256") != actual_tree:
        fail("quality manifest output tree hash does not match staged artifact")
    if output.get("file_count") != len(current_files):
        fail("quality manifest output file count does not match staged artifact")
    listed = {str(x.get("path")): x for x in output.get("files") or []}
    for item in current_files:
        prior = listed.get(str(item["path"]))
        if prior != item:
            fail(f"quality manifest file mismatch: {item['path']}")
            break
    return manifest


def validate_performance(files: list[pathlib.Path]) -> None:
    total = sum(p.stat().st_size for p in files)
    if total > MAX_TOTAL_BYTES:
        fail(f"artifact exceeds total size budget: {total} > {MAX_TOTAL_BYTES}")
    for p in files:
        size = p.stat().st_size
        rel = p.relative_to(SITE).as_posix()
        suffix = p.suffix.lower()
        limit = None
        if suffix == ".html":
            limit = MAX_HTML_BYTES
        elif suffix == ".css":
            limit = MAX_CSS_BYTES
        elif suffix == ".js":
            limit = MAX_JS_BYTES
        elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico"}:
            limit = MAX_IMAGE_BYTES
        if limit is not None and size > limit:
            fail(f"performance budget exceeded: {rel} is {size} bytes > {limit}")


def validate_page(path: pathlib.Path, sitemap: set[str]) -> None:
    rel = path.relative_to(SITE).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = PageParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        fail(f"HTML parser failed for {rel}: {exc}")
        return

    if parser.html_lang not in {"en", "bn", "en-bd", "bn-bd"}:
        fail(f"{rel}: missing/invalid html lang")
    if not parser.title():
        fail(f"{rel}: missing title")
    if parser.meta_value("name", "viewport") is None:
        fail(f"{rel}: missing viewport meta")
    desc = parser.meta_value("name", "description")
    if not desc or not desc.strip():
        fail(f"{rel}: missing meta description")
    robots = (parser.meta_value("name", "robots") or "").lower().replace(" ", "")
    if not robots:
        fail(f"{rel}: missing robots meta")
    if parser.h1_count != 1:
        fail(f"{rel}: expected exactly one h1, found {parser.h1_count}")
    if "main" not in parser.main_ids:
        fail(f"{rel}: missing <main id=\"main\">")
    if not parser.skip_main:
        fail(f"{rel}: missing skip link to #main")

    for image in parser.images:
        if "alt" not in image:
            fail(f"{rel}: image missing alt attribute: {image.get('src','')}")

    for button in parser.buttons:
        attrs = button.get("attrs") or {}
        label = str(attrs.get("aria-label", "")).strip()
        text_value = " ".join("".join(button.get("text") or []).split())
        if not label and not text_value:
            fail(f"{rel}: button lacks accessible text/aria-label")

    canonical = parser.canonical()
    if not canonical:
        fail(f"{rel}: missing canonical")
    else:
        parsed = urllib.parse.urlsplit(canonical)
        if parsed.scheme != "https" or parsed.netloc.lower() != "saveonsub.com":
            fail(f"{rel}: canonical must use https://saveonsub.com")
        canonical_rel = url_to_rel(canonical)
        if canonical_rel != rel:
            fail(f"{rel}: canonical points to {canonical_rel!r}, expected self")

    peer = bilingual_peer(rel)
    if peer:
        en_rel, bn_rel = peer
        en_path, bn_path = SITE / en_rel, SITE / bn_rel
        if not en_path.is_file() or not bn_path.is_file():
            fail(f"{rel}: bilingual peer missing ({en_rel}, {bn_rel})")
        alts = parser.alternates()
        expected_en = rel_to_url(en_rel)
        expected_bn = rel_to_url(bn_rel)
        if alts.get("en-bd") != expected_en:
            fail(f"{rel}: hreflang en-bd mismatch")
        if alts.get("bn-bd") != expected_bn:
            fail(f"{rel}: hreflang bn-bd mismatch")
        if alts.get("x-default") != expected_en:
            fail(f"{rel}: hreflang x-default mismatch")

    for kind, ref in parser.refs():
        ref = ref.strip()
        if not ref or ref.startswith(("mailto:", "tel:", "data:")):
            continue
        if ref.lower().startswith("javascript:"):
            fail(f"{rel}: javascript URL is forbidden: {ref}")
            continue
        parsed = urllib.parse.urlsplit(ref)
        if parsed.scheme in {"http", "https"} and parsed.netloc.lower() != "saveonsub.com":
            continue
        target_rel = url_to_rel(ref)
        if target_rel is None:
            continue
        if not (SITE / target_rel).is_file():
            fail(f"{rel}: broken internal {kind} target {ref} -> {target_rel}")

    for script in parser.jsonld:
        if not script:
            continue
        try:
            data = json.loads(script)
        except json.JSONDecodeError as exc:
            fail(f"{rel}: malformed JSON-LD: {exc}")
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                typ = node.get("@type")
                types = typ if isinstance(typ, list) else [typ]
                if any(t in {"Offer", "AggregateOffer"} for t in types):
                    fail(f"{rel}: commerce schema type is forbidden in L1: {typ}")
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    page_url = rel_to_url(rel)
    if page_url in sitemap and "noindex" in robots:
        fail(f"{rel}: sitemap URL is marked noindex")
    if is_plan_route(rel):
        if "noindex" not in robots:
            fail(f"{rel}: dedicated plan page must remain noindex in L1")
        if page_url in sitemap:
            fail(f"{rel}: noindex plan page must not be in sitemap")
    if rel == "404.html" and "noindex" not in robots:
        fail("404.html must be noindex")


def validate_sitemap_targets(sitemap: set[str]) -> None:
    for url in sorted(sitemap):
        if not url.startswith(f"{DOMAIN}/") and url != f"{DOMAIN}/":
            fail(f"foreign sitemap URL: {url}")
            continue
        rel = url_to_rel(url)
        if not rel or not (SITE / rel).is_file():
            fail(f"sitemap URL has no staged target: {url}")


def validate_journey() -> None:
    required = ["index.html", "bn.html", "all.html", "about.html", "contact.html", "faq.html", "privacy.html", "terms.html", "404.html"]
    for rel in required:
        if not (SITE / rel).is_file():
            fail(f"journey required page missing: {rel}")
    en_products = sorted((SITE / "p").glob("*.html")) if (SITE / "p").is_dir() else []
    bn_products = sorted((SITE / "bn" / "p").glob("*.html")) if (SITE / "bn" / "p").is_dir() else []
    if not en_products or not bn_products:
        fail("journey has no EN/BN product pages")
        return
    sample = en_products[0]
    pid = sample.stem
    if not (SITE / "bn" / "p" / f"{pid}.html").is_file():
        fail(f"journey sample product lacks BN peer: {pid}")
    en_plan_dir = SITE / "p" / pid
    bn_plan_dir = SITE / "bn" / "p" / pid
    en_plans = sorted(en_plan_dir.glob("*.html")) if en_plan_dir.is_dir() else []
    if en_plans:
        plan_name = en_plans[0].name
        if not (bn_plan_dir / plan_name).is_file():
            fail(f"journey sample plan lacks BN peer: {pid}/{plan_name}")


def main() -> int:
    if not SITE.is_dir():
        print("quality gate blocked: _site missing")
        return 1

    files = sorted(p for p in SITE.rglob("*") if p.is_file())
    html_paths = [p for p in files if p.suffix.lower() == ".html"]
    sitemap = sitemap_set()
    manifest = validate_manifest()
    validate_performance(files)
    for p in html_paths:
        validate_page(p, sitemap)
    validate_sitemap_targets(sitemap)
    validate_journey()

    if manifest:
        output = manifest.get("output") or {}
        if output.get("html_route_count") != len(html_paths):
            fail("quality manifest HTML route count mismatch")
        if output.get("sitemap_url_count") != len(sitemap):
            fail("quality manifest sitemap URL count mismatch")

    for message in warnings:
        print(f"WARN: {message}")
    if errors:
        print(f"QUALITY GATE BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1

    print(json.dumps({
        "quality_gate": "PASS",
        "html_pages": len(html_paths),
        "sitemap_urls": len(sitemap),
        "artifact_bytes": sum(p.stat().st_size for p in files),
        "broken_internal_links": 0,
        "canonical_errors": 0,
        "hreflang_errors": 0,
        "accessibility_static_errors": 0,
        "performance_budget_errors": 0,
        "schema_errors": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
