#!/usr/bin/env python3
"""Remove other business units' (aips-*) pages and links from the staged site (SOS-P0-003).

CEO decision 2026-11-11: SaveOnSub stays separate from AIPS; the aips-* pages
are removed and their old URLs 301 to /all (EN) or /bn/all (BN) via _redirects.
Source files stay in the repository; only the public artifact (_site) changes.

Runs last in build_site.py. On _site it:
  - deletes every staged file whose name starts with "aips-"
  - drops aips-* products from assets/catalog.js
  - removes product cards, plain links, ItemList entries, sitemap <url>s and
    llms.txt lines that point at aips-* pages
  - maps the /modes picker away from aips-* ids to SaveOnSub bundles
`--check` re-verifies without writing: no "aips-" may remain anywhere in _site
except the redirect rules.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
TOKEN = "aips-"
CATALOG = re.compile(r"(const CATALOG = )(\{.*?\})(;\s*)$", re.S | re.M)
DIV_CARD = re.compile(r'<div class="pcard"[^>]*>(?:(?!<div class="pcard").)*?href="[^"]*aips-[^"]*".*?</div></div>', re.S)
A_CARD = re.compile(r'<a class="pcard" href="[^"]*aips-[^"]*">.*?</a>', re.S)
A_LINK = re.compile(r'<a href="[^"]*aips-[^"]*"[^>]*>.*?</a>', re.S)
LDJSON = re.compile(r'(<script[^>]+application/ld\+json[^>]*>)(.*?)(</script>)', re.S)
SITEMAP_URL = re.compile(r"\s*<url>(?:(?!</url>).)*?aips-.*?</url>", re.S)
# The /modes picker pointed at aips-* bundles; SaveOnSub bundles of similar intent.
MODE_SWAP = {"aips-student-essentials": "bundle-starter", "aips-freelancer-bundle": "bundle-creator",
             "aips-university-pro": "bundle-research", "aips-business-package": "bundle-dev"}
TEXT_SUFFIX = {".html", ".js", ".txt", ".xml", ".json", ".webmanifest"}


def strip_ld(raw: str) -> str:
    try:
        data = json.loads(raw.replace("<\\/", "</"))
    except ValueError:
        return raw

    def walk(node):
        if isinstance(node, dict):
            if node.get("@type") == "ItemList" and isinstance(node.get("itemListElement"), list):
                kept = [e for e in node["itemListElement"] if TOKEN not in json.dumps(e, ensure_ascii=False)]
                for i, e in enumerate(kept, 1):
                    if isinstance(e, dict) and "position" in e:
                        e["position"] = i
                node["itemListElement"] = kept
                if "numberOfItems" in node:
                    node["numberOfItems"] = len(kept)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def clean_html(t: str) -> str:
    for old, new in MODE_SWAP.items():
        t = t.replace(f"'{old}'", f"'{new}'")
    t = DIV_CARD.sub("", t)
    t = A_CARD.sub("", t)
    t = A_LINK.sub("", t)
    return LDJSON.sub(lambda m: m.group(1) + strip_ld(m.group(2)) + m.group(3) if TOKEN in m.group(2) else m.group(0), t)


def clean_catalog(t: str) -> tuple[str, int, int]:
    m = CATALOG.search(t)
    if not m:
        raise SystemExit("[cross-unit] CATALOG literal not found in catalog.js")
    cat = json.loads(m.group(2))
    before = len(cat["products"])
    cat["products"] = [p for p in cat["products"] if not str(p.get("id", "")).startswith(TOKEN)]
    body = json.dumps(cat, ensure_ascii=False, separators=(",", ":"))
    return t[:m.start(2)] + body + t[m.end(2):], before, len(cat["products"])


def count_patterns(n: int) -> list[str]:
    return [f"All {n} ", f"{n} subscriptions", f"{n} premium subscriptions", f'"numberOfItems":{n},']


def fix_counts(site: Path, old: int, new: int) -> None:
    """Product-count copy ("All 72 Products", ItemList numberOfItems) must match the catalog."""
    if old == new:
        return
    for f in site.rglob("*.html"):
        t = f.read_text(encoding="utf-8")
        u = t
        for a, b in zip(count_patterns(old), count_patterns(new)):
            u = u.replace(a, b)
        if u != t:
            f.write_text(u, encoding="utf-8")


def stage(site: Path) -> int:
    removed = 0
    cat_js = site / "assets" / "catalog.js"
    new_js, old_n, new_n = clean_catalog(cat_js.read_text(encoding="utf-8"))
    cat_js.write_text(new_js, encoding="utf-8")
    fix_counts(site, old_n, new_n)
    for f in sorted(site.rglob(f"{TOKEN}*")):
        if f.is_file():
            f.unlink()
            removed += 1
    for f in site.rglob("*"):
        if not f.is_file() or f.suffix not in TEXT_SUFFIX or f.name == "_redirects":
            continue
        t = f.read_text(encoding="utf-8")
        if TOKEN not in t:
            continue
        rel = f.relative_to(site).as_posix()
        if rel == "assets/catalog.js":
            continue
        if f.suffix == ".xml":
            new = SITEMAP_URL.sub("", t)
        elif f.suffix == ".txt":
            new = "".join(line for line in t.splitlines(keepends=True) if TOKEN not in line)
        else:
            new = clean_html(t)
        f.write_text(new, encoding="utf-8")
    refresh_sw_cache(site)
    return removed


def refresh_sw_cache(site: Path) -> None:
    """catalog.js changed after motion_polish versioned sw.js; re-version it the same way."""
    sw = site / "sw.js"
    if not sw.is_file():
        return
    import motion_polish as mp
    saved, mp.SITE = mp.SITE, site
    try:
        sw.write_text(mp.sw_version(sw.read_text(encoding="utf-8")), encoding="utf-8")
    finally:
        mp.SITE = saved


def check(site: Path) -> list[str]:
    errors = []
    for f in site.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(site).as_posix()
        if f.name.startswith(TOKEN):
            errors.append(f"{rel}: other-unit file staged")
            continue
        if f.name == "_redirects" or f.suffix not in TEXT_SUFFIX:
            continue
        if TOKEN in f.read_text(encoding="utf-8", errors="ignore"):
            errors.append(f"{rel}: still references aips-*")
    m = CATALOG.search((site / "assets" / "catalog.js").read_text(encoding="utf-8"))
    n = len(json.loads(m.group(2))["products"]) if m else -1
    for f in (site / "all.html", site / "bn" / "all.html"):
        t = f.read_text(encoding="utf-8") if f.exists() else ""
        for found in re.findall(r'"numberOfItems":(\d+),"itemListOrder"', t):
            if int(found) != n:
                errors.append(f"{f.relative_to(site).as_posix()}: numberOfItems {found} != catalog {n}")
    red = (site / "_redirects").read_text(encoding="utf-8") if (site / "_redirects").exists() else ""
    for rule in ("/p/aips-* /all 301", "/bn/p/aips-* /bn/all 301", "/modes/aips-* /all 301"):
        if rule not in red:
            errors.append(f"_redirects: missing '{rule}'")
    return errors


def main(argv: list[str]) -> int:
    if not (SITE / "assets" / "catalog.js").exists():
        raise SystemExit("[cross-unit] _site missing; run the build first")
    if "--check" not in argv:
        n = stage(SITE)
        print(f"[cross-unit] removed {n} aips-* file(s) and their links from _site")
    errors = check(SITE)
    if errors:
        print("\n".join(errors[:40]), file=sys.stderr)
        raise SystemExit(f"[cross-unit] FAIL — {len(errors)} issue(s)")
    print("[cross-unit] PASS — no aips-* file or reference in _site; old URLs 301 to /all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
