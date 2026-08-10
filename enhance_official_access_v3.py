#!/usr/bin/env python3
"""Add source-backed EN/BN official AI access landing pages for Bangladesh."""
from __future__ import annotations

import json
import pathlib
import xml.etree.ElementTree as ET

from build_public_info_v3 import DEST, esc, shell
from routes_v3 import DOMAIN

CHECKED_ON = "2026-08-10"
OWNER = "SAVEONSUB Admin"

PROVIDERS = [
    {
        "name": "ChatGPT",
        "status_en": "Official access is supported in Bangladesh.",
        "status_bn": "বাংলাদেশে অফিসিয়াল অ্যাক্সেস সমর্থিত।",
        "source": "https://help.openai.com/en/articles/7947663-chatgpt-supported-countries-and-territories",
        "source_name": "OpenAI — ChatGPT Supported Countries",
        "official": "https://chatgpt.com/",
    },
    {
        "name": "Gemini",
        "status_en": "The Gemini web and mobile apps list Bangladesh as available.",
        "status_bn": "Gemini web ও mobile app-এর availability list-এ বাংলাদেশ রয়েছে।",
        "source": "https://support.google.com/gemini/answer/14579026?hl=en",
        "source_name": "Google — Gemini mobile app availability",
        "official": "https://gemini.google.com/",
    },
    {
        "name": "Claude",
        "status_en": "Anthropic lists Bangladesh among supported Claude.ai locations.",
        "status_bn": "Anthropic-এর supported Claude.ai location list-এ বাংলাদেশ রয়েছে।",
        "source": "https://support.anthropic.com/en/articles/8461763-where-can-i-access-claude-ai",
        "source_name": "Anthropic — Where can I access Claude.ai?",
        "official": "https://claude.ai/",
    },
]


def inject_jsonld(page: str, payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return page.replace("</head>", f'<script type="application/ld+json">{raw}</script></head>', 1)


def provider_cards(language: str) -> str:
    bn = language == "bn"
    cards = []
    for provider in PROVIDERS:
        cards.append(
            '<article class="tcard">'
            f'<h2>{esc(provider["name"])}</h2>'
            f'<p>{esc(provider["status_bn"] if bn else provider["status_en"])}</p>'
            '<div class="ctas">'
            f'<a class="btn btn-primary btn-sm" href="{esc(provider["official"])}" target="_blank" rel="noopener noreferrer nofollow">'
            f'{"অফিসিয়াল সাইট" if bn else "Official site"} ↗</a>'
            f'<a class="btn btn-ghost btn-sm" href="{esc(provider["source"])}" target="_blank" rel="noopener noreferrer">'
            f'{"availability source" if bn else "Availability source"} ↗</a>'
            '</div></article>'
        )
    return ''.join(cards)


def render(language: str) -> str:
    bn = language == "bn"
    rel = "bn/resources/official-ai-access-bangladesh.html" if bn else "resources/official-ai-access-bangladesh.html"
    peer = "resources/official-ai-access-bangladesh.html" if bn else "bn/resources/official-ai-access-bangladesh.html"
    canonical = f"{DOMAIN}/{rel}"
    alternate = f"{DOMAIN}/{peer}"
    hub = "/bn/resources/index.html" if bn else "/resources/index.html"
    home = "/bn.html" if bn else "/"

    if bn:
        title = "বাংলাদেশে অফিসিয়াল AI টুল অ্যাক্সেস | SAVEONSUB"
        desc = "বাংলাদেশ থেকে ChatGPT, Gemini ও Claude-এর অফিসিয়াল availability যাচাই করুন এবং provider-এর নিজস্ব সাইটে যাওয়ার নিরাপদ পথ দেখুন।"
        heading = "বাংলাদেশে AI টুলের অফিসিয়াল অ্যাক্সেস কীভাবে যাচাই করবেন"
        summary = "কোনো reseller claim, shared account বা অযাচাইকৃত payment route-এর উপর নির্ভর না করে প্রথমে provider-এর বর্তমান availability এবং official sign-in/upgrade path যাচাই করুন।"
        checklist = [
            "Provider-এর official availability page-এ Bangladesh আছে কি না দেখুন।",
            "নিজের account-এ sign in করে provider-এর দেখানো upgrade option দেখুন।",
            "Checkout-এ যে currency, tax ও payment method দেখায় সেটিকেই current truth ধরুন; SAVEONSUB এখানে কোনো price বা payment destination প্রকাশ করে না।",
            "Shared login, unknown workspace invite বা credential-sharing offer গ্রহণের আগে provider terms পড়ুন।",
            "Provider page ও third-party claim-এর মধ্যে conflict হলে provider source-কে অগ্রাধিকার দিন।",
        ]
        caveat = "Availability মানেই প্রতিটি paid plan, feature বা payment method সব account-এ একই হবে—এমন নয়। Provider eligibility, app-store rules, account type এবং rollout বদলাতে পারে।"
        source_heading = "যাচাইকৃত provider source"
    else:
        title = "Official AI Access in Bangladesh | SAVEONSUB"
        desc = "Verify official Bangladesh availability for ChatGPT, Gemini and Claude, then follow the provider's own access path without relying on shared-account or reseller claims."
        heading = "How to verify official AI-tool access in Bangladesh"
        summary = "Start with the provider's current availability page and official sign-in or upgrade path instead of relying on reseller claims, shared accounts or an unverified payment route."
        checklist = [
            "Confirm Bangladesh appears on the provider's current availability page.",
            "Sign in to your own account and inspect the upgrade options the provider presents to you.",
            "Treat the currency, tax and payment methods shown at provider checkout as current truth; SAVEONSUB does not publish a selling price or payment destination here.",
            "Read provider terms before accepting a shared login, unknown workspace invite or credential-sharing offer.",
            "If a third-party claim conflicts with the provider page, prefer the provider source.",
        ]
        caveat = "Availability does not mean every paid plan, feature or payment method is identical for every account. Eligibility, app-store rules, account type and rollouts can change."
        source_heading = "Verified provider sources"

    bullets = ''.join(f'<li>{esc(item)}</li>' for item in checklist)
    sources = ''.join(
        f'<li><a href="{esc(p["source"])}" target="_blank" rel="noopener noreferrer">{esc(p["source_name"])}</a></li>'
        for p in PROVIDERS
    )
    body = (
        '<article class="wrap" style="max-width:960px;padding-top:30px;padding-bottom:50px">'
        f'<div class="crumbs"><a href="{home}">{"হোম" if bn else "Home"}</a> › <a href="{hub}">{"রিসোর্স" if bn else "Resources"}</a> › {esc(heading)}</div>'
        f'<span class="pill">{"অফিসিয়াল অ্যাক্সেস গাইড" if bn else "OFFICIAL ACCESS GUIDE"}</span>'
        f'<h1>{esc(heading)}</h1><p class="sub">{esc(summary)}</p>'
        f'<div class="notice mt2"><b>{"সম্পাদনা" if bn else "Editorial"}: {OWNER}</b><p>{"Source check" if bn else "Sources checked"}: <time datetime="{CHECKED_ON}">{CHECKED_ON}</time>. '
        f'{"এই পেজ তথ্যভিত্তিক; কোনো provider partnership, selling price বা payment destination দাবি করে না।" if bn else "This page is informational and does not claim a provider partnership, selling price or payment destination."}</p></div>'
        f'<section class="mt3"><h2>{"Provider অনুযায়ী বর্তমান availability" if bn else "Current availability by provider"}</h2><div class="grid g3 mt2">{provider_cards(language)}</div></section>'
        f'<section class="mt3"><h2>{"Upgrade করার আগে ৫টি যাচাই" if bn else "Five checks before upgrading"}</h2><ol>{bullets}</ol></section>'
        f'<section class="mt3"><div class="notice"><b>{"গুরুত্বপূর্ণ সীমা" if bn else "Important limitation"}</b><p>{esc(caveat)}</p></div></section>'
        f'<section class="mt3"><h2>{source_heading}</h2><ul>{sources}</ul></section>'
        '</article>'
    )
    page = shell(body, title=title, desc=desc, canonical=canonical, language="bn" if bn else "en", alternate=alternate, page_type="article")
    return inject_jsonld(page, {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": heading,
        "description": summary,
        "datePublished": CHECKED_ON,
        "dateModified": CHECKED_ON,
        "inLanguage": "bn-BD" if bn else "en-BD",
        "mainEntityOfPage": canonical,
        "author": {"@type": "Organization", "name": OWNER},
        "publisher": {"@type": "Organization", "name": "SAVEONSUB", "url": f"{DOMAIN}/"},
    })


def add_sitemap(urls: list[str]) -> int:
    path = DEST / "sitemap.xml"
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    tree = ET.parse(path)
    root = tree.getroot()
    existing = {n.text.strip() for n in root.findall(f"{{{ns}}}url/{{{ns}}}loc") if n.text}
    added = 0
    for url in urls:
        if url not in existing:
            node = ET.SubElement(root, f"{{{ns}}}url")
            ET.SubElement(node, f"{{{ns}}}loc").text = url
            existing.add(url)
            added += 1
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return added


def inject_hub_cta() -> int:
    changed = 0
    targets = [
        (DEST / "resources/index.html", False),
        (DEST / "bn/resources/index.html", True),
    ]
    for path, bn in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        href = "/bn/resources/official-ai-access-bangladesh.html" if bn else "/resources/official-ai-access-bangladesh.html"
        if href in text:
            continue
        marker = '<div class="grid g2 mt3">'
        card = (
            '<article class="tcard"><span class="cat">official-access</span>'
            f'<h2>{"বাংলাদেশে AI টুলের অফিসিয়াল অ্যাক্সেস যাচাই" if bn else "Verify official AI access in Bangladesh"}</h2>'
            f'<p>{"ChatGPT, Gemini ও Claude-এর provider availability source এবং নিজের account থেকে safe upgrade path যাচাই করুন।" if bn else "Check provider availability sources for ChatGPT, Gemini and Claude and follow the safe official path from your own account."}</p>'
            f'<a class="btn btn-primary btn-sm" href="{href}">{"গাইড পড়ুন" if bn else "Read guide"} →</a></article>'
        )
        if marker in text:
            path.write_text(text.replace(marker, marker + card, 1), encoding="utf-8")
            changed += 1
    return changed


def enhance_official_access() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    en = DEST / "resources/official-ai-access-bangladesh.html"
    bn = DEST / "bn/resources/official-ai-access-bangladesh.html"
    en.parent.mkdir(parents=True, exist_ok=True)
    bn.parent.mkdir(parents=True, exist_ok=True)
    en.write_text(render("en"), encoding="utf-8")
    bn.write_text(render("bn"), encoding="utf-8")
    urls = [f"{DOMAIN}/resources/official-ai-access-bangladesh.html", f"{DOMAIN}/bn/resources/official-ai-access-bangladesh.html"]
    return {"official_access_pages": 2, "official_access_sitemap_urls_added": add_sitemap(urls), "official_access_hubs_changed": inject_hub_cta()}


if __name__ == "__main__":
    print("enhanced official access:", enhance_official_access())
