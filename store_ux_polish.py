#!/usr/bin/env python3
"""Store usability polish for the staged site (build step, after bn_buyer_copy.py).

1. Language switch: only the English home page linked to Bangla, so a visitor on
   any other page could not change language. Every page with the main menu now
   links to its counterpart (or to that language's home page when none exists).
2. Bangla pages stay in Bangla: links, the cart button and policy links that
   pointed at an English page now point at its Bangla twin when one is staged.
3. Home search: both home pages get a search box that opens the product list with
   the query (the list already reads ``?q=``). It works without JavaScript.

No price, offer, claim or HOLD is added or changed. ``--check`` only verifies.
"""
from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
NAV_OPEN = '<div class="navlinks">'
DIV_TAG = re.compile(r"<(/?)div\b[^>]*>")
SWITCH = re.compile(r">\s*(বাংলা|English)\s*</a>")
HERO_CTAS = '<div class="heroctas">'
SEARCH_MARK = 'class="homesearch"'
HOMES = {"index.html": False, "bn.html": True}
ANCHOR = re.compile(r"<a\b[^>]*>")
HREF = re.compile(r'(\bhref=")([^"]*)(")')
CART = re.compile(r"(onclick=\"location\.href=')([^']*)('\")")
LANG_BN = re.compile(r"<html\b[^>]*\blang=\"bn", re.I)


def is_bn_path(rel: str) -> bool:
    return rel == "bn.html" or rel.startswith("bn/")


def is_bangla(rel: str, text: str) -> bool:
    """Bangla pages: everything under /bn, plus Bangla guides filed elsewhere."""
    return is_bn_path(rel) or bool(LANG_BN.search(text[:600]))


def twin_of(rel: str, pages: set[str]) -> str | None:
    """The same page in the other language, if it is staged."""
    if rel == "index.html":
        other = "bn.html"
    elif rel == "bn.html":
        other = "index.html"
    elif rel.startswith("bn/"):
        other = rel[3:]
    else:
        other = "bn/" + rel
    return other if other in pages else None


def relative_url(target: str, page: str) -> str:
    """Clean relative link from one staged file to another (no .html)."""
    base = posixpath.dirname(page) or "."
    path = target[:-5]
    if path == "index" or path.endswith("/index"):
        folder = posixpath.dirname(path) or "."
        out = posixpath.relpath(folder, base)
        return "./" if out == "." else out + "/"
    out = posixpath.relpath(posixpath.dirname(path) or ".", base)
    name = posixpath.basename(path)
    return name if out == "." else f"{out}/{name}"


def resolve(href: str, page: str, pages: set[str]) -> str | None:
    """Staged file an internal link opens, else None."""
    path = re.split(r"[?#]", href, maxsplit=1)[0]
    if not path or re.match(r"^[a-z][a-z0-9+.-]*:", path, re.I) or path.startswith("//"):
        return None
    if path.startswith("/"):
        joined = posixpath.normpath(path.lstrip("/") or ".")
    else:
        joined = posixpath.normpath(posixpath.join(posixpath.dirname(page), path))
    if joined == ".":
        return "index.html" if "index.html" in pages else None
    for candidate in (joined, joined + ".html", joined + "/index.html"):
        if candidate.endswith(".html") and candidate in pages:
            return candidate
    return None


def bangla_href(href: str, page: str, pages: set[str]) -> str:
    target = resolve(href, page, pages)
    if target is None or is_bn_path(target):
        return href
    twin = twin_of(target, pages)
    if twin is None:
        return href
    tail = href[len(re.split(r"[?#]", href, maxsplit=1)[0]):]
    return relative_url(twin, page) + tail


def keep_bangla(text: str, rel: str, pages: set[str]) -> str:
    if not is_bangla(rel, text):
        return text

    def anchor(m: re.Match) -> str:
        tag = m.group(0)
        if 'lang="en"' in tag:  # a deliberate switch to English
            return tag
        return HREF.sub(lambda h: h.group(1) + bangla_href(h.group(2), rel, pages) + h.group(3), tag, count=1)

    text = ANCHOR.sub(anchor, text)
    return CART.sub(lambda m: m.group(1) + bangla_href(m.group(2), rel, pages) + m.group(3), text)


def nav_span(text: str) -> tuple[int, int] | None:
    """(start, index of the closing tag) of the main menu, counting nested divs."""
    start = text.find(NAV_OPEN)
    if start < 0:
        return None
    depth = 0
    for m in DIV_TAG.finditer(text, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start, m.start()
    return None


def add_switch(text: str, rel: str, pages: set[str]) -> str:
    span = nav_span(text)
    if span is None or SWITCH.search(text, *span):
        return text
    bangla = is_bangla(rel, text)
    twin = twin_of(rel, pages)
    # A Bangla guide filed outside /bn has no true twin: send readers to the English home.
    if twin is None or (bangla and not is_bn_path(rel)):
        twin = "index.html" if bangla else "bn.html"
    href = relative_url(twin, rel)
    if bangla:
        link = f'<a class="langsw" href="{href}" lang="en" hreflang="en-BD">English</a>'
    else:
        link = f'<a class="langsw" href="{href}" lang="bn" hreflang="bn-BD">বাংলা</a>'
    end = span[1]
    return text[:end] + "  " + link + "\n  " + text[end:]


def search_form(bangla: bool) -> str:
    action = "/bn/all" if bangla else "/all"
    label = "সাবস্ক্রিপশন খুঁজুন" if bangla else "Search subscriptions"
    hint = "ChatGPT, Canva, Netflix…"
    button = "খুঁজুন" if bangla else "Search"
    return (f'<form {SEARCH_MARK} action="{action}" method="get" role="search">'
            f'<input type="search" name="q" maxlength="80" aria-label="{label}" placeholder="{hint}" '
            f'autocomplete="off" required><button class="btn btn-primary btn-sm" type="submit">{button}</button></form>')


def add_search(text: str, rel: str) -> str:
    if rel not in HOMES or SEARCH_MARK in text or HERO_CTAS not in text:
        return text
    return text.replace(HERO_CTAS, search_form(HOMES[rel]) + HERO_CTAS, 1)


def polish(text: str, rel: str, pages: set[str]) -> str:
    return add_search(add_switch(keep_bangla(text, rel, pages), rel, pages), rel)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not SITE.is_dir():
        print("[store-ux] FAIL — _site missing; run build_site.py")
        return 1
    files = sorted(SITE.rglob("*.html"))
    pages = {p.relative_to(SITE).as_posix() for p in files}
    changed, errors = 0, []
    for p in files:
        rel = p.relative_to(SITE).as_posix()
        text = p.read_text(encoding="utf-8")
        new = polish(text, rel, pages)
        if check:
            if new != text:
                errors.append(f"{rel}: language switch, Bangla link or home search missing")
        elif new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
    for rel in HOMES:
        path = SITE / rel
        if not path.is_file() or SEARCH_MARK not in path.read_text(encoding="utf-8"):
            errors.append(f"{rel}: home search box not present")
    if errors:
        for item in errors[:20]:
            print(f"[store-ux] FAIL — {item}")
        return 1
    print(f"[store-ux] PASS — {'checked' if check else f'{changed} page(s) updated'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
