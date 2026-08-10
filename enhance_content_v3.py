#!/usr/bin/env python3
"""Generate source-backed EN/BN SAVEONSUB resource pages from editorial records."""
from __future__ import annotations

import json
import pathlib
import xml.etree.ElementTree as ET

from build_public_info_v3 import DEST, esc, shell
from routes_v3 import DOMAIN, slugify
from site_config import SUPPORT_EMAIL, support_mailto

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "content" / "resources_v1.json"


def load_resources() -> dict:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("schema") != "saveonsub-resources-v1":
        raise RuntimeError("unsupported resource schema")
    if data.get("editorial_owner") != "SAVEONSUB Admin":
        raise RuntimeError("resource editorial owner must be SAVEONSUB Admin")
    if not data.get("articles"):
        raise RuntimeError("resource article list is empty")
    return data


def inject_jsonld(page: str, payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tag = f'<script type="application/ld+json">{raw}</script>'
    if "</head>" not in page:
        raise RuntimeError("resource page missing head close")
    return page.replace("</head>", f"{tag}</head>", 1)


def render_sources(article: dict, language: str, checked_on: str) -> str:
    bn = language == "bn"
    items = "".join(
        f'<li><a href="{esc(source["url"])}" target="_blank" rel="noopener noreferrer">{esc(source["name"])}</a></li>'
        for source in article.get("sources", [])
    )
    if not items:
        return ""
    return (
        f'<section class="mt3"><h2>{"সোর্স ও আরও পড়ুন" if bn else "Sources and further reading"}</h2>'
        f'<ul>{items}</ul><p class="fine">'
        f'{"লিংকগুলো SAVEONSUB Admin যাচাই করেছে" if bn else "Links were checked by SAVEONSUB Admin on"} '
        f'<time datetime="{esc(checked_on)}">{esc(checked_on)}</time>. '
        f'{"কোনো সোর্স গুরুত্বপূর্ণভাবে পরিবর্তিত হলে পেজের updated date-ও পরিবর্তন করা হবে।" if bn else "If a source materially changes, the page updated date should change with it."}'
        f'</p></section>'
    )


def render_categories(article: dict, language: str) -> str:
    categories = article.get("related_categories", [])
    if not categories:
        return ""
    bn = language == "bn"
    prefix = "/bn/c/" if bn else "/c/"
    links = "".join(
        f'<a class="btn btn-ghost btn-sm" href="{prefix}{esc(slugify(category))}.html">{esc(category)}</a>'
        for category in categories
    )
    return (
        f'<section class="mt3"><h2>{"সম্পর্কিত ক্যাটাগরি" if bn else "Related catalog categories"}</h2>'
        f'<p class="sub">{"এই গাইড পড়ার পরে প্রাসঙ্গিক তথ্যভিত্তিক ক্যাটাগরি দেখুন।" if bn else "Explore the relevant information-only catalog categories after reading this guide."}</p>'
        f'<div class="ctas">{links}</div></section>'
    )


def render_article(article: dict, language: str, checked_on: str, owner: str) -> str:
    bn = language == "bn"
    localized = article[language]
    slug = article["slug"]
    rel = f"bn/resources/{slug}.html" if bn else f"resources/{slug}.html"
    peer_rel = f"resources/{slug}.html" if bn else f"bn/resources/{slug}.html"
    canonical = f"{DOMAIN}/{rel}"
    alternate = f"{DOMAIN}/{peer_rel}"

    sections = []
    for section in localized.get("sections", []):
        paragraphs = "".join(f'<p>{esc(p)}</p>' for p in section.get("paragraphs", []))
        bullets = section.get("bullets", [])
        bullet_html = "" if not bullets else "<ul>" + "".join(f'<li>{esc(item)}</li>' for item in bullets) + "</ul>"
        sections.append(f'<section class="mt3"><h2>{esc(section["heading"])}</h2>{paragraphs}{bullet_html}</section>')

    hub = "/bn/resources/index.html" if bn else "/resources/index.html"
    home = "/bn.html" if bn else "/"
    methodology = "/bn/resources/saveonsub-editorial-methodology.html" if bn else "/resources/saveonsub-editorial-methodology.html"
    byline = (
        f'<div class="notice mt2"><b>{"সম্পাদনা" if bn else "Editorial"}: {esc(owner)}</b>'
        f'<p>{"প্রকাশ/যাচাই" if bn else "Published / checked"}: <time datetime="{esc(checked_on)}">{esc(checked_on)}</time>. '
        f'{"এই রিসোর্স তথ্য ও decision support-এর জন্য; এটি কোনো paid ranking নয়।" if bn else "This resource is for information and decision support; it is not a paid ranking."} '
        f'<a href="{methodology}">{"Editorial method" if bn else "Editorial method"}</a>.</p></div>'
    )
    correction = (
        f'<section class="mt3"><div class="notice"><b>{"কোনো ভুল দেখেছেন?" if bn else "Found something outdated?"}</b>'
        f'<p>{"SAVEONSUB Admin-কে verified support email-এ জানান; factual correction হলে source record এবং public page একসঙ্গে update করা হবে।" if bn else "Tell SAVEONSUB Admin through the verified support email. A factual correction should update the source record and public page together."} '
        f'<a href="{esc(support_mailto("SAVEONSUB resource correction"))}">{esc(SUPPORT_EMAIL)}</a></p></div></section>'
    )
    body = (
        f'<article class="wrap" style="max-width:900px;padding-top:30px;padding-bottom:50px">'
        f'<div class="crumbs"><a href="{home}">{"হোম" if bn else "Home"}</a> › <a href="{hub}">{"রিসোর্স" if bn else "Resources"}</a> › {esc(localized["title"])}</div>'
        f'<span class="pill">{"BANGLADESH AI RESOURCE" if not bn else "বাংলাদেশ AI রিসোর্স"}</span>'
        f'<h1>{esc(localized["title"])}</h1><p class="sub">{esc(localized["summary"])}</p>{byline}'
        f'{"".join(sections)}{render_categories(article, language)}{render_sources(article, language, checked_on)}{correction}'
        f'</article>'
    )
    page = shell(
        body,
        title=f'{localized["title"]} | SAVEONSUB',
        desc=localized["description"],
        canonical=canonical,
        language="bn" if bn else "en",
        alternate=alternate,
        page_type="article",
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": localized["title"],
        "description": localized["summary"],
        "datePublished": checked_on,
        "dateModified": checked_on,
        "inLanguage": "bn-BD" if bn else "en-BD",
        "mainEntityOfPage": canonical,
        "author": {"@type": "Organization", "name": owner, "url": f"{DOMAIN}{methodology}"},
        "publisher": {"@type": "Organization", "name": "SAVEONSUB", "url": f"{DOMAIN}/"},
    }
    return inject_jsonld(page, schema)


def render_hub(data: dict, language: str) -> str:
    bn = language == "bn"
    cards = []
    for article in data["articles"]:
        local = article[language]
        prefix = "/bn/resources/" if bn else "/resources/"
        cards.append(
            f'<article class="tcard"><span class="cat">{esc(article.get("audience", "resource"))}</span>'
            f'<h2>{esc(local["title"])}</h2><p>{esc(local["summary"])}</p>'
            f'<a class="btn btn-primary btn-sm" href="{prefix}{esc(article["slug"])}.html">{"গাইড পড়ুন" if bn else "Read guide"} →</a></article>'
        )
    canonical = f"{DOMAIN}/bn/resources/index.html" if bn else f"{DOMAIN}/resources/index.html"
    alternate = f"{DOMAIN}/resources/index.html" if bn else f"{DOMAIN}/bn/resources/index.html"
    body = (
        f'<div class="wrap" style="padding-top:30px;padding-bottom:50px"><span class="pill">{"রিসোর্স লাইব্রেরি" if bn else "RESOURCE LIBRARY"}</span>'
        f'<h1>{"বাংলাদেশ AI রিসোর্স লাইব্রেরি" if bn else "Bangladesh AI Resource Library"}</h1>'
        f'<p class="sub">{"শিক্ষার্থী, ফ্রিল্যান্সার, টিম ও AI ব্যবহারকারীদের জন্য source-backed practical guide। প্রতিটি পেজ SAVEONSUB Admin-এর editorial method ও release gate অনুসরণ করে।" if bn else "Source-backed practical guides for students, freelancers, teams and AI users in Bangladesh. Every page follows SAVEONSUB Admin editorial methodology and the same release gates as the catalog."}</p>'
        f'<div class="notice mt2"><b>Editorial owner: SAVEONSUB Admin</b><p>{"শেষ source check" if bn else "Latest source check"}: <time datetime="{esc(data["checked_on"])}">{esc(data["checked_on"])}</time>. '
        f'<a href="{"/bn/resources/saveonsub-editorial-methodology.html" if bn else "/resources/saveonsub-editorial-methodology.html"}">{"Methodology দেখুন" if bn else "Read the methodology"}</a>.</p></div>'
        f'<div class="grid g2 mt3">{"".join(cards)}</div></div>'
    )
    return shell(
        body,
        title="বাংলাদেশ AI রিসোর্স | SAVEONSUB" if bn else "Bangladesh AI Resources | SAVEONSUB",
        desc="বাংলাদেশের জন্য source-backed AI guide, study workflow, freelance workflow, comparison methodology ও responsible-use checklist।" if bn else "Source-backed Bangladesh AI guides for study, freelance workflows, tool comparison, responsible use and SAVEONSUB editorial methodology.",
        canonical=canonical,
        language="bn" if bn else "en",
        alternate=alternate,
    )


def write(rel: str, content: str) -> None:
    path = DEST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add_sitemap_urls(urls: list[str]) -> int:
    path = DEST / "sitemap.xml"
    if not path.is_file():
        raise RuntimeError("sitemap.xml missing before content generation")
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    tree = ET.parse(path)
    root = tree.getroot()
    existing = {
        node.text.strip()
        for node in root.findall(f"{{{ns}}}url/{{{ns}}}loc")
        if node.text
    }
    added = 0
    for url in urls:
        if url in existing:
            continue
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = url
        existing.add(url)
        added += 1
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return added


def inject_resource_navigation() -> int:
    changed = 0
    en_nav_old = '<div class="navlinks"><a href="/all.html">Subscriptions</a><a href="/#categories">Categories</a><a href="/faq.html">FAQ</a>'
    en_nav_new = '<div class="navlinks"><a href="/all.html">Subscriptions</a><a href="/#categories">Categories</a><a href="/resources/index.html">Resources</a><a href="/faq.html">FAQ</a>'
    en_footer_old = '<div><b>Browse</b><a href="/all.html">All subscriptions</a><a href="/#categories">Categories</a></div>'
    en_footer_new = '<div><b>Browse</b><a href="/all.html">All subscriptions</a><a href="/#categories">Categories</a><a href="/resources/index.html">Resources</a></div>'
    bn_nav_old = '<div class="navlinks"><a href="/all.html">সব সাবস্ক্রিপশন</a><a href="/bn.html#categories">ক্যাটাগরি</a><a href="/faq.html">প্রশ্নোত্তর</a>'
    bn_nav_new = '<div class="navlinks"><a href="/all.html">সব সাবস্ক্রিপশন</a><a href="/bn.html#categories">ক্যাটাগরি</a><a href="/bn/resources/index.html">রিসোর্স</a><a href="/faq.html">প্রশ্নোত্তর</a>'
    bn_footer_old = '<div><b>ব্রাউজ</b><a href="/all.html">সব সাবস্ক্রিপশন</a><a href="/bn.html#categories">ক্যাটাগরি</a></div>'
    bn_footer_new = '<div><b>ব্রাউজ</b><a href="/all.html">সব সাবস্ক্রিপশন</a><a href="/bn.html#categories">ক্যাটাগরি</a><a href="/bn/resources/index.html">রিসোর্স</a></div>'

    for path in sorted(DEST.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if '<html lang="bn">' in text:
            new = text.replace(bn_nav_old, bn_nav_new, 1).replace(bn_footer_old, bn_footer_new, 1)
        else:
            new = text.replace(en_nav_old, en_nav_new, 1).replace(en_footer_old, en_footer_new, 1)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def enhance_content() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    data = load_resources()
    checked_on = data["checked_on"]
    owner = data["editorial_owner"]
    urls: list[str] = []

    write("resources/index.html", render_hub(data, "en"))
    write("bn/resources/index.html", render_hub(data, "bn"))
    urls += [f"{DOMAIN}/resources/index.html", f"{DOMAIN}/bn/resources/index.html"]

    for article in data["articles"]:
        slug = article["slug"]
        write(f"resources/{slug}.html", render_article(article, "en", checked_on, owner))
        write(f"bn/resources/{slug}.html", render_article(article, "bn", checked_on, owner))
        urls += [f"{DOMAIN}/resources/{slug}.html", f"{DOMAIN}/bn/resources/{slug}.html"]

    added = add_sitemap_urls(urls)
    nav_changed = inject_resource_navigation()
    return {
        "resource_articles": len(data["articles"]),
        "resource_pages_written": len(urls),
        "resource_sitemap_urls_added": added,
        "resource_navigation_pages_changed": nav_changed,
    }


def main() -> int:
    print("enhanced strict L1 resource library:", enhance_content())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
