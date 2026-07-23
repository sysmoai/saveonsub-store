#!/usr/bin/env python3
"""SAVEONSUB SEO keyword engine — generates a comprehensive keyword universe per product
(short-tail + long-tail, English + Bangla + transliteration, transactional + informational).
Writes catalog.json in place with p['seo'] = {primary, secondary[], long_tail[], bangla[], intent_map}.
Run: python3 build_keywords.py"""
import json, re

cat = json.load(open('catalog.json'))

# Bengali transliteration hints for common product-name syllables (kept light + safe)
BN_NAME = {
 "chatgpt": "চ্যাটজিপিটি", "chatgpt plus": "চ্যাটজিপিটি প্লাস", "claude": "ক্লড",
 "google ai pro": "গুগল এআই প্রো", "gemini": "জেমিনি", "grok": "গ্রক", "supergrok": "সুপারগ্রক",
 "perplexity": "পারপ্লেক্সিটি", "midjourney": "মিডজার্নি", "leonardo": "লিওনার্দো",
 "canva": "ক্যানভা", "netflix": "নেটফ্লিক্স", "spotify": "স্পটিফাই", "youtube premium": "ইউটিউব প্রিমিয়াম",
 "grammarly": "গ্রামারলি", "capcut": "ক্যাপকাট", "kling": "ক্লিং", "elevenlabs": "ইলেভেনল্যাবস",
 "notion": "নোশন", "coursera": "কোর্সেরা", "envato": "এনভাটো", "freepik": "ফ্রিপিক",
 "nordvpn": "নর্ডভিপিএন", "hoichoi": "হইচই", "suno": "সুনো", "invideo": "ইনভিডিও",
 "heygen": "হেইজেন", "runway": "রানওয়ে", "adobe firefly": "অ্যাডোবি ফায়ারফ্লাই",
 "prime video": "প্রাইম ভিডিও", "cursor": "কার্সার", "github copilot": "গিটহাব কোপাইলট",
}

def base_name(p):
    n = p['name'].replace('🎁 ', '').replace('🏢 ', '')
    n = re.split(r'\s+—|\s+\(', n)[0].strip()
    return n

def gen_keywords(p):
    name = base_name(p)
    nl = name.lower()
    frm = min(pl['bdt'] for pl in p['plans'])
    is_bundle = p['category'] == 'Bundles'

    # --- English short-tail (transactional) ---
    short = [
        f"{nl} price in bangladesh",
        f"{nl} bangladesh",
        f"{nl} bd price",
        f"{nl} price bd",
        f"buy {nl} bangladesh",
        f"{nl} bkash",
    ]
    if not is_bundle:
        short += [
            f"{nl} subscription bangladesh",
            f"{nl} bd",
            f"{nl} bangladesh price",
            f"{nl} nagad",
        ]

    # --- Long-tail (transactional + comparative + intent) ---
    long_tail = [
        f"buy {nl} in bangladesh with bkash",
        f"{nl} subscription price in bangladesh 2026",
        f"cheap {nl} subscription bangladesh",
        f"{nl} shared account bangladesh",
        f"how to buy {nl} in bangladesh",
        f"{nl} price in taka",
        f"{nl} bangladesh reseller",
        f"is {nl} available in bangladesh",
        f"{nl} personal account bangladesh",
        f"{nl} bkash nagad rocket",
    ]
    if p['category'] in ("AI Assistants", "AI Image & Design", "AI Video", "AI Voice & Music", "AI Code & Dev", "AI Writing"):
        long_tail += [f"{nl} for students bangladesh", f"cheapest {nl} bangladesh"]
    if p['category'] == "Entertainment":
        long_tail += [f"{nl} without credit card bangladesh", f"{nl} bd subscription bkash"]

    # --- Informational (top-funnel) ---
    info = [
        f"is {nl} worth it bangladesh",
        f"{nl} vs free tier",
        f"{nl} review bangladesh",
        f"how much is {nl} in bangladesh",
    ]

    # --- Bangla + transliteration ---
    bn_core = BN_NAME.get(nl)
    bangla = []
    if bn_core:
        bangla = [
            f"{bn_core} দাম বাংলাদেশ",
            f"{bn_core} প্রাইস",
            f"{bn_core} বিকাশ",
            f"{bn_core} সাবস্ক্রিপশন",
            f"{bn_core} কিভাবে কিনবো",
        ]
    # Latin-Bangla transliteration (how many actually type)
    translit = [f"{nl} dam koto", f"{nl} kivabe kinbo", f"{nl} bd taka"]

    primary = f"{nl} price in bangladesh"
    return {
        "primary": primary,
        "short_tail": short,
        "long_tail": long_tail,
        "informational": info,
        "bangla": bangla,
        "transliteration": translit,
        "all": list(dict.fromkeys(short + long_tail + info + bangla + translit)),
    }

for p in cat['products']:
    p['seo'] = gen_keywords(p)
    # keep the flat keywords field in sync (used by llms/meta) — top 6 most valuable
    p['keywords'] = (p['seo']['short_tail'][:4] + p['seo']['long_tail'][:2])

json.dump(cat, open('catalog.json', 'w'), ensure_ascii=False, indent=1)
total = sum(len(p['seo']['all']) for p in cat['products'])
print(f"OK: keyword universe — {len(cat['products'])} products, {total} total keywords ({total//len(cat['products'])} avg/product)")
