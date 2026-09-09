#!/usr/bin/env python3
"""Final technical-SEO normalization for the staged Cloudflare Pages artifact.

Cloudflare Pages serves HTML on extensionless routes and redirects *.html to the
clean counterpart. This pass makes the public graph agree with that behavior:
canonicals, hreflang, OG/JSON-LD URLs, internal links and sitemap entries all
point directly to clean URLs instead of redirecting forms.

It also fixes favicon MIME metadata and keeps transactional utility pages out of
search results without blocking crawlers from seeing the noindex directive.
The pass is deterministic and fail-closed.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

SITE = Path("_site")
MIGRATION_LASTMOD = "2026-09-09"
NOINDEX_BASENAMES = {"checkout.html", "order.html", "track.html", "offline.html"}

if not SITE.is_dir():
    raise SystemExit("TECH SEO ERROR — _site/ missing; run stage_deploy.py first")


def clean_path(url: str) -> str:
    suffix = ""
    base = url
    m = re.match(r"^(.*?)([?#].*)$", url)
    if m:
        base, suffix = m.group(1), m.group(2)
    if base.endswith("/index.html"):
        base = base[:-10]
    elif base == "index.html":
        base = "./"
    elif base.endswith(".html"):
        base = base[:-5]
    return base + suffix


def rewrite_same_origin_absolute(text: str) -> str:
    pat = re.compile(r"https://saveonsub\.com/[A-Za-z0-9_./%${}\-]+\.html(?:[?#][^\"'<>\s]*)?")
    return pat.sub(lambda m: clean_path(m.group(0)), text)


def rewrite_internal_routes(text: str) -> str:
    # Static quoted routes.
    pat = re.compile(
        r"(?P<q>[\"'])(?P<url>(?!(?:https?:|mailto:|tel:|javascript:|data:|#))"
        r"(?:/|\./|\.\./)?[A-Za-z0-9_./%${}\-]*\.html(?:[?#][^\"']*)?)(?P=q)"
    )
    text = pat.sub(lambda m: m.group("q") + clean_path(m.group("url")) + m.group("q"), text)

    # Generated/template routes can concatenate an expression before .html,
    # e.g. "p/"+p.id+".html" or `p/${p.id}.html`. Removing the suffix is safe
    # because the route itself is already constructed by the surrounding code.
    text = text.replace('.html`', '`')
    text = text.replace('.html"', '"')
    text = text.replace(".html'", "'")
    return text


def ensure_noindex(text: str) -> str:
    if re.search(r'<meta\s+name="robots"', text, re.I):
        return re.sub(
            r'(<meta\s+name="robots"\s+content=")[^"]*(">)',
            r'\1noindex,follow\2', text, count=1, flags=re.I,
        )
    if "</head>" not in text:
        raise SystemExit("TECH SEO ERROR — no </head> on utility HTML")
    return text.replace("</head>", '<meta name="robots" content="noindex,follow">\n</head>', 1)


changed = 0
for page in SITE.rglob("*.html"):
    text = page.read_text(encoding="utf-8", errors="strict")
    original = text
    text = rewrite_same_origin_absolute(text)
    text = rewrite_internal_routes(text)
    text = re.sub(
        r'(<link\s+rel="icon"\s+href="[^"]*favicon-32\.png"\s+type=")image/svg\+xml(")',
        r'\1image/png\2', text, flags=re.I,
    )
    if page.name in NOINDEX_BASENAMES:
        text = ensure_noindex(text)
    if text != original:
        page.write_text(text, encoding="utf-8")
        changed += 1

sitemap = SITE / "sitemap.xml"
if not sitemap.is_file():
    raise SystemExit("TECH SEO ERROR — sitemap.xml missing")
s = rewrite_same_origin_absolute(sitemap.read_text(encoding="utf-8", errors="strict"))
s = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", f"<lastmod>{MIGRATION_LASTMOD}</lastmod>", s)
sitemap.write_text(s, encoding="utf-8")

robots = SITE / "robots.txt"
if not robots.is_file():
    raise SystemExit("TECH SEO ERROR — robots.txt missing")
r = robots.read_text(encoding="utf-8", errors="strict")
r = re.sub(r"(?m)^Disallow:\s*/(?:checkout|order|track|offline)(?:\.html)?\s*$\n?", "", r)
r = re.sub(r"\n{3,}", "\n\n", r).strip() + "\n"
robots.write_text(r, encoding="utf-8")

errors: list[str] = []
for page in SITE.rglob("*.html"):
    text = page.read_text(encoding="utf-8", errors="strict")
    rel = page.relative_to(SITE).as_posix()
    if re.search(r'https://saveonsub\.com/[^\"\s<>]*\.html(?:[?#][^\"\s<>]*)?', text):
        errors.append(f"{rel}: same-origin absolute .html URL survived")
    if re.search(r'(?:href|action)=[\"\'][^\"\']*\.html(?:[?#][^\"\']*)?[\"\']', text, re.I):
        errors.append(f"{rel}: HTML navigation still points at .html")
    if re.search(r'(?:p|c|blog|bn)/[^\s\"\'`<>]*\.html', text):
        errors.append(f"{rel}: generated internal .html route survived")
    if re.search(r'favicon-32\.png"\s+type="image/svg\+xml', text, re.I):
        errors.append(f"{rel}: PNG favicon still declares SVG MIME")
    if page.name in NOINDEX_BASENAMES and not re.search(
        r'<meta\s+name="robots"\s+content="noindex,follow">', text, re.I
    ):
        errors.append(f"{rel}: utility page missing noindex,follow")

s_final = sitemap.read_text(encoding="utf-8", errors="strict")
if re.search(r"https://saveonsub\.com/[^<\s]*\.html", s_final):
    errors.append("sitemap.xml: .html URL survived")
if f"<lastmod>{MIGRATION_LASTMOD}</lastmod>" not in s_final:
    errors.append("sitemap.xml: migration lastmod not applied")

if errors:
    print(f"TECH SEO HARDENING FAILED — {len(errors)} issue(s):", file=sys.stderr)
    for item in errors[:80]:
        print(f"  {item}", file=sys.stderr)
    raise SystemExit(1)

print(
    f"Technical SEO hardening OK — {changed} HTML file(s) normalized; "
    "clean canonicals/internal links/sitemap, utility noindex and PNG favicon MIME enforced."
)
