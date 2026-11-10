#!/usr/bin/env python3
"""Link hygiene for the staged site (build step): clean internal URLs + EN/BN hreflang pairs.

Part 1 — clean internal links.

Why: Cloudflare Pages serves ``/p/x.html`` with a 308 redirect to ``/p/x`` and
``/index.html`` to ``/``. Canonicals, hreflang and sitemap.xml already use the
clean form, but ~450 internal ``href``s still point at the ``.html`` form, so
every crawl of them is a redirect hop (Search Console 10 Nov 2026: 144 pages
"Page with redirect"). This step only changes ``href`` attributes that point
at a page that exists in ``_site``; it adds or removes no page, URL or price.

- ``x.html`` -> ``x``; ``dir/index.html`` -> ``dir/``; ``index.html`` -> ``./``
- relative, root-relative and ``https://saveonsub.com/...`` links
- query strings and #fragments are kept
- external sites, assets and missing targets are left alone

Part 2 — hreflang pairs. Where both ``X.html`` and ``bn/X.html`` are staged, the
EN page's ``bn-bd`` alternate must point at the BN URL (nine info pages pointed
at themselves) and both pages' ``x-default`` must be the EN URL. Only existing
``<link rel="alternate">`` tags are corrected; none are added.

``--check`` re-verifies without writing: fails if any rewritable link or wrong
hreflang pair remains.
"""
from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
HOSTS = ("https://saveonsub.com", "https://www.saveonsub.com")
HREF = re.compile(r'(\bhref=)(["\'])([^"\']*?\.html)([?#][^"\']*)?\2')


def target(page: Path, url: str) -> Path | None:
    """The _site file a link resolves to, or None if external/missing."""
    for host in HOSTS:
        if url.startswith(host + "/"):
            url = url[len(host):]
            break
    if re.match(r"^[a-z][a-z0-9+.-]*:|^//", url, re.I):
        return None
    # browsers clamp ".." above the site root to the root
    base = "/" + page.parent.relative_to(SITE).as_posix()
    rel = posixpath.normpath(url if url.startswith("/") else posixpath.join(base, url)).lstrip("/")
    f = SITE / rel
    return f if f.is_file() else None


def clean(url: str) -> str:
    if url == "index.html":
        return "./"
    if url.endswith("/index.html"):
        return url[: -len("index.html")]
    return url[: -len(".html")]


def process(page: Path) -> tuple[str, int]:
    text = page.read_text(encoding="utf-8")
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        url = m.group(3)
        if url.rsplit("/", 1)[-1] in ("404.html", "offline.html") or target(page, url) is None:
            return m.group(0)
        count += 1
        return f"{m.group(1)}{m.group(2)}{clean(url)}{m.group(4) or ''}{m.group(2)}"

    return HREF.sub(sub, text), count


# 404.html is served at whatever path was missing (/p/x/y), so its relative
# links and assets break below the root. Make them root-absolute.
REL = re.compile(r'(\b(?:href|src)=)(["\'])(?![a-z][a-z0-9+.-]*:|/|#|\$\{)([^"\']*)\2', re.I)


def root_absolute(text: str) -> tuple[str, int]:
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        url = m.group(3)
        url = url[2:] if url.startswith("./") else url
        count += 1
        return f"{m.group(1)}{m.group(2)}/{url}{m.group(2)}"

    return REL.sub(sub, text), count


BASE = HOSTS[0]
ALT = re.compile(r'(<link[^>]+rel=["\']alternate["\'][^>]+hreflang=["\'])([^"\']+)(["\'][^>]+href=["\'])([^"\']+)(["\'])', re.I)


def page_url(rel: str) -> str:
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[:-len('index.html')]}"
    return f"{BASE}/{rel[:-len('.html')]}"


def pair_fix(page: Path, text: str) -> tuple[str, int]:
    rel = page.relative_to(SITE).as_posix()
    if rel.startswith("bn/"):
        en_rel, bn_rel = rel[3:], rel
    else:
        en_rel, bn_rel = rel, "bn/" + rel
    if not ((SITE / en_rel).is_file() and (SITE / bn_rel).is_file()) or rel == "index.html":
        return text, 0
    want = {"en-bd": page_url(en_rel), "bn-bd": page_url(bn_rel), "x-default": page_url(en_rel)}
    fixed = 0

    def sub(m: re.Match) -> str:
        nonlocal fixed
        lang = m.group(2).lower()
        if lang in want and m.group(4) != want[lang]:
            fixed += 1
            return m.group(1) + m.group(2) + m.group(3) + want[lang] + m.group(5)
        return m.group(0)

    return ALT.sub(sub, text), fixed


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not SITE.is_dir():
        print("[link-hygiene] FAIL — _site missing; run build_site.py first")
        return 1
    pages = sorted(SITE.rglob("*.html"))
    total = changed = 0
    pairs = 0
    for page in pages:
        new, n = process(page)
        new, k = pair_fix(page, new)
        if page == SITE / "404.html":
            new, r = root_absolute(new)
            n += r
        if n or k:
            total += n
            pairs += k
            changed += 1
            if not check:
                page.write_text(new, encoding="utf-8")
    if check:
        if total or pairs:
            print(f"[link-hygiene] FAIL — {total} internal .html link(s), {pairs} wrong hreflang tag(s) on {changed} page(s)")
            return 1
        print(f"[link-hygiene] PASS — clean internal links and EN/BN hreflang pairs on {len(pages)} pages")
        return 0
    print(f"[link-hygiene] {total} internal link(s) cleaned, {pairs} hreflang tag(s) corrected on {changed} page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
