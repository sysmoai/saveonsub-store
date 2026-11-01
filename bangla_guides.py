#!/usr/bin/env python3
"""Build Bangla how-to guides from ops/seo/guides/*.md into the staged site.

Each Markdown source (front matter + body) becomes /blog/<slug>.html with
lang="bn", its own title/description/canonical, Article JSON-LD and links to
the related product pages. Entries are added to the blog index and sitemap.

Content rules (enforced): no SaveOnSub price, discount, ranking, guarantee or
credential-sharing claim. `--check` re-verifies the staged artifact.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
SRC = ROOT / "ops" / "seo" / "guides"
CATALOG = ROOT / "catalog.json"
BASE = "https://saveonsub.com"
MARK = 'data-bangla-guide="2026-11-01"'
SHELL_FROM = "coursera-vs-youtube-learning-bd.html"
FORBIDDEN = re.compile(r"৳|cheapest|lowest price|#1\b|lifetime|guarantee|shared account|instant delivery|SaveOnSub", re.I)


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"[bangla-guides] missing front matter: {path.name}")
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        meta[k.strip()] = v
    for key in ("slug", "title", "description", "related"):
        if not meta.get(key):
            raise SystemExit(f"[bangla-guides] {path.name}: missing {key}")
    return meta, m.group(2)


def inline(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener nofollow">\1</a>', s)
    return s


def md_to_html(md: str) -> str:
    out, lines, i = [], md.strip().splitlines(), 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            i += 1  # H1 comes from front matter
            continue
        if line.startswith("### "):
            out.append(f'<h3 class="mt2" style="font-size:18px">{inline(line[4:])}</h3>')
        elif line.startswith("## "):
            out.append(f'<h2 class="mt3" style="font-size:22px">{inline(line[3:])}</h2>')
        elif line.startswith("> "):
            out.append(f'<blockquote class="notice mt2">{inline(line[2:])}</blockquote>')
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif re.match(r"^[০-৯\d]+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"^[০-৯\d]+\.\s", lines[i]):
                items.append(f"<li>{inline(re.sub(r'^[০-৯\d]+\.\s', '', lines[i]))}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-|]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            head = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<div style="overflow-x:auto"><table class="mt2"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            continue
        else:
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|>|- |\||[০-৯\d]+\.\s)", lines[i]):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
            continue
        i += 1
    return "\n".join(out)


def set_once(text: str, pattern: str, repl: str) -> str:
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"[bangla-guides] shell pattern not found: {pattern[:40]}")
    return new


def render(meta: dict, body: str, shell: str, products: dict) -> str:
    slug, title, desc = meta["slug"], meta["title"], meta["description"]
    url = f"{BASE}/blog/{slug}"
    rel = [p for p in meta["related"] if p in products]
    links = "".join(f'<li><a href="../bn/p/{esc(p)}">{esc(products[p]["name"])}</a></li>' for p in rel)
    main = (
        f'<main id="main" {MARK}><div class="wrap" style="max-width:780px">'
        f'<div class="crumbs"><a href="../bn">হোম</a> › <a href="./">গাইড</a> › {esc(title[:40])}</div>'
        f'<span class="pill">📖 বাংলা গাইড</span><h1 style="font-size:clamp(26px,4vw,38px)">{esc(title)}</h1>'
        f'<p class="sub mt2">{esc(desc)}</p>'
        f"{md_to_html(body)}"
        f'<h2 class="mt3" style="font-size:22px">সম্পর্কিত টুল</h2><ul>{links}</ul>'
        "</div></main>"
    )
    t = shell
    t = re.sub(r'<html lang="[^"]*"', '<html lang="bn"', t, count=1)
    t = set_once(t, r"<title>.*?</title>", f"<title>{esc(title)} | SAVEONSUB</title>")
    t = set_once(t, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">')
    t = set_once(t, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">')
    t = set_once(t, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(desc)}">')
    t = set_once(t, r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">')
    t = re.sub(r'<meta property="og:locale" content="[^"]*">', '<meta property="og:locale" content="bn_BD">', t, count=1)
    t = re.sub(r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{esc(title)}">', t, count=1)
    t = re.sub(r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{esc(desc)}">', t, count=1)
    t = set_once(t, r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">')
    t = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\s*', "", t)
    t = t.replace(f'<link rel="canonical" href="{url}">',
                  f'<link rel="canonical" href="{url}">\n<link rel="alternate" hreflang="bn-bd" href="{url}">', 1)
    t = re.sub(r'<script type="application/ld\+json">.*?</script>', "", t, flags=re.S)
    ld = {
        "@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc,
        "inLanguage": "bn-BD", "datePublished": "2026-11-01", "dateModified": "2026-11-01",
        "author": {"@type": "Organization", "name": "SAVEONSUB"},
        "publisher": {"@type": "Organization", "name": "SAVEONSUB", "url": BASE},
        "mainEntityOfPage": url,
    }
    t = t.replace("</head>", f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n</head>', 1)
    t = set_once(t, r"<main\b[^>]*>.*?</main>", main.replace("\\", "\\\\"))
    return t


def add_to_index(guides: list[dict]) -> None:
    idx = SITE / "blog" / "index.html"
    text = idx.read_text(encoding="utf-8")
    if MARK in text:
        return
    cards = "".join(
        f'<a class="pcard" {MARK} href="{esc(g["slug"])}"><h3 style="font-size:16px">{esc(g["title"])}</h3>'
        f'<p class="sub" style="font-size:13.5px">{esc(g["description"][:90])}</p>'
        f'<span class="go" style="color:var(--green2);font-weight:700;font-size:13px">গাইড পড়ুন →</span></a>'
        for g in guides
    )
    anchor = 'grid-template-columns:repeat(2,1fr);gap:16px">'
    if anchor not in text:
        raise SystemExit("[bangla-guides] blog index grid not found")
    idx.write_text(text.replace(anchor, anchor + cards, 1), encoding="utf-8")


def add_to_sitemap(guides: list[dict]) -> None:
    sm = SITE / "sitemap.xml"
    text = sm.read_text(encoding="utf-8")
    add = "".join(
        f"<url><loc>{BASE}/blog/{g['slug']}</loc><lastmod>{date.today().isoformat()}</lastmod>"
        "<changefreq>monthly</changefreq><priority>0.7</priority></url>"
        for g in guides if f"{BASE}/blog/{g['slug']}</loc>" not in text
    )
    sm.write_text(text.replace("</urlset>", add + "</urlset>", 1), encoding="utf-8")


def load():
    products = {p["id"]: p for p in json.loads(CATALOG.read_text(encoding="utf-8"))["products"]}
    guides = []
    for path in sorted(SRC.glob("*.md")):
        meta, body = parse(path)
        if FORBIDDEN.search(body) or FORBIDDEN.search(meta["description"]):
            raise SystemExit(f"[bangla-guides] forbidden claim in {path.name}")
        meta["body"] = body
        guides.append(meta)
    return products, guides


def check(guides: list[dict]) -> list[str]:
    errors = []
    sm = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    idx = (SITE / "blog" / "index.html").read_text(encoding="utf-8")
    for g in guides:
        page = SITE / "blog" / f"{g['slug']}.html"
        if not page.exists():
            errors.append(f"missing {page.name}")
            continue
        t = page.read_text(encoding="utf-8")
        if MARK not in t or '<html lang="bn"' not in t:
            errors.append(f"{page.name}: not a governed Bangla guide")
        if f'<link rel="canonical" href="{BASE}/blog/{g["slug"]}">' not in t:
            errors.append(f"{page.name}: canonical")
        main = re.search(r"<main\b.*?</main>", t, re.S).group(0)
        if FORBIDDEN.search(re.sub(r"<[^>]+>", " ", main)):
            errors.append(f"{page.name}: forbidden claim")
        for href in re.findall(r'href="(\.\./bn/p/[a-z0-9-]+)"', main):
            if not (page.parent / (href + ".html")).resolve().exists():
                errors.append(f"{page.name}: dead {href}")
        if f"{BASE}/blog/{g['slug']}</loc>" not in sm:
            errors.append(f"sitemap missing {g['slug']}")
        if f'href="{g["slug"]}"' not in idx:
            errors.append(f"blog index missing {g['slug']}")
    return errors


def main(argv: list[str]) -> int:
    products, guides = load()
    if "--check" not in argv:
        shell = (SITE / "blog" / SHELL_FROM).read_text(encoding="utf-8")
        for g in guides:
            (SITE / "blog" / f"{g['slug']}.html").write_text(render(g, g["body"], shell, products), encoding="utf-8")
        add_to_index(guides)
        add_to_sitemap(guides)
        print(f"[bangla-guides] built {len(guides)} guide(s)")
    errors = check(guides)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(f"[bangla-guides] FAIL — {len(errors)} issue(s)")
    print("[bangla-guides] PASS — Bangla guides, canonicals, index, sitemap and product links verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
