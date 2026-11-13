#!/usr/bin/env python3
"""Add original Bangla buyer-intent guidance to exactly three product pages.

Pages: /bn/p/chatgpt-plus, /bn/p/chatgpt-go, /bn/p/google-ai-pro.
One section per page, inserted before "কীভাবে অর্ডার হয়": task-based use cases,
a Free/Go/Plus (or Gemini) chooser, and a 10-minute self-test prompt.

Rules (CEO brief 14 Nov 2026): no price (cards stay the only price source), no
unverified feature or limit, no provider authorization, no profit or customer
outcome claim, no new FAQ markup (the generated FAQ + FAQPage schema stay the
single FAQ). Internal links are added only if the target exists in the artifact.

Usage: python3 bn_buyer_copy.py [SITE_DIR] [--check]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = 'data-bn-buyer-copy="1"'
ANCHOR = re.compile(r'<h2[^>]*>\s*কীভাবে অর্ডার হয়\s*</h2>')
BOX = ('style="border:1px solid var(--line,rgba(255,255,255,.12));border-radius:12px;padding:12px 14px;'
       'margin:8px 0 12px;font-size:15px;line-height:1.7;overflow-wrap:anywhere"')

PAGES = {
    "chatgpt-plus": {
        "h2": "ChatGPT Plus কোন কাজে লাগে, আর কখন Free বা Go-ই যথেষ্ট",
        "uses": [
            "<b>শিক্ষার্থী:</b> একটি অধ্যায়ের নোট থেকে সারাংশ ও অনুশীলনী বানানো। গুরুত্বপূর্ণ তথ্য মূল বই বা শিক্ষকের সাথে মিলিয়ে নিন।",
            "<b>ফ্রিল্যান্সার:</b> ক্লায়েন্টের ব্রিফ বিশ্লেষণ করে কাজের চেকলিস্ট ও প্রথম খসড়া তৈরি।",
            "<b>ছোট ব্যবসা:</b> কাস্টমার রিপ্লাই ও পণ্যের বিবরণের খসড়া, আপনার যাচাই-করা তথ্য দিয়ে।",
            "<b>ডেভেলপার:</b> কোড ব্যাখ্যা, ত্রুটি খোঁজার পথ ও টেস্ট-কেসের ধারণা।",
        ],
        "choose": [
            "হালকা বা মাঝেমধ্যের কাজে আগে <b>Free</b> দিয়ে শুরু করুন।",
            "Free-র সীমায় নিয়মিত আটকালে <b>Go</b> দেখুন।",
            "দীর্ঘ গবেষণা, ফাইলভিত্তিক কাজ বা নিয়মিত বেশি ব্যবহার হলে <b>Plus</b> ভাবুন।",
        ],
        "note": "বেশি দাম মানেই আপনার কাজে বেশি উপকার নয়। মডেল, টুল ও ব্যবহারসীমা OpenAI সময়ে সময়ে বদলায়, তাই আপনার অ্যাকাউন্টে বর্তমান তালিকা দেখে নিন।",
        "tut_h": "প্রথম ১০ মিনিটের কাজ",
        "tut": "“আমি একজন ফ্রিল্যান্সার। আমার কাজ [আপনার কাজ]। ক্লায়েন্টের ব্রিফ: [ব্যক্তিগত তথ্য ছাড়া সংক্ষিপ্ত ব্রিফ]। প্রথমে প্রয়োজনীয় ৫টি প্রশ্ন করো, তারপর ৭ দিনের বাস্তব কাজের পরিকল্পনা দাও। প্রতিটি ধাপের শেষে আমি কীভাবে আউটপুট যাচাই করব লিখো।”",
        "after": "পরিকল্পনার প্রথম কাজটি ছোট করে পরীক্ষা করুন। ভুল হলে সংশোধন চেয়ে আবার প্রশ্ন করুন। উত্তর ক্লায়েন্টকে দেওয়ার আগে নিজে দেখে নিন।",
        "links": [("blog/chatgpt-free-go-plus-konta-niben-bangla", "Free, Go নাকি Plus — বিস্তারিত গাইড"),
                  ("blog/chatgpt-plus-naki-gemini-konta-niben", "ChatGPT Plus নাকি Gemini — তুলনা"),
                  ("p/chatgpt-go", "ChatGPT Go পাতা")],
    },
    "chatgpt-go": {
        "h2": "ChatGPT Go: কার জন্য, আর কখন Plus ভাবা উচিত",
        "uses": [
            "<b>পড়ার অভ্যাস:</b> প্রতিদিন একটি বিষয়ে প্রশ্ন, সারাংশ ও অনুশীলন।",
            "<b>লেখা:</b> বাংলা ও ইংরেজিতে ইমেইল বা ক্লায়েন্ট মেসেজের প্রথম খসড়া, তারপর নিজের ভাষায় ঠিক করা।",
            "<b>ছোট কাজের সহায়তা:</b> ডকুমেন্ট বা ডেটা বোঝা, যতটা আপনার প্ল্যানের ফাইল ও ব্যবহারসীমা অনুমতি দেয়।",
        ],
        "choose": [
            "Free দিয়েই কাজ চললে এখনই টাকা দেওয়ার দরকার নেই।",
            "Free-র সীমায় প্রায়ই আটকালে এবং কাজ হালকা থাকলে <b>Go</b> বিবেচনা করুন।",
            "Go-তে Plus-এর সব সুবিধা নেই। দীর্ঘ গবেষণা বা বেশি ব্যবহারে <b>Plus</b> তুলনা করুন।",
        ],
        "note": "কেনার আগে নিজেকে জিজ্ঞেস করুন: এই মাসে কোন ৩টি কাজ করব? ব্যবহারসীমা ও সুবিধা OpenAI বদলাতে পারে, তাই OpenAI-এর Go পাতায় বর্তমান তালিকা দেখুন।",
        "tut_h": "পড়াশোনার জন্য ১০ মিনিটের অনুশীলন",
        "tut": "“আমি [বিষয়]-এর [অধ্যায়] পড়ছি। প্রথমে এটি দশম শ্রেণির উপযোগী সহজ বাংলায় বোঝাও। তারপর ৫টি ছোট প্রশ্ন দাও। আমার উত্তর দেওয়ার আগে সমাধান দেখিও না। ভুল হলে ইঙ্গিত দিয়ে বুঝিয়ে দাও।”",
        "after": "এভাবে AI উত্তরদাতা নয়, অনুশীলনের সঙ্গী হয়। পরীক্ষার গুরুত্বপূর্ণ তথ্য পাঠ্যবই বা শিক্ষকের সাথে মিলিয়ে নিন।",
        "links": [("blog/chatgpt-free-go-plus-konta-niben-bangla", "Free, Go নাকি Plus — বিস্তারিত গাইড"),
                  ("p/chatgpt-plus", "ChatGPT Plus পাতা")],
    },
    "google-ai-pro": {
        "h2": "Google AI Pro: কাজ অনুযায়ী কীভাবে ব্যবহার শুরু করবেন",
        "uses": [
            "<b>শিক্ষার্থী ও গবেষক:</b> বড় বিষয় বোঝা, তথ্য সাজানো ও প্রশ্ন বানানো। Gemini-র দেওয়া তথ্য নিজে যাচাই করুন।",
            "<b>Gmail ও Docs-নির্ভর কাজ:</b> আপনার অ্যাকাউন্টে যে Gemini ফিচার চালু আছে তা দিয়ে খসড়া ও এডিটিং।",
            "<b>কনটেন্ট ক্রিয়েটর:</b> ছবি বা ভিডিওর আইডিয়া। ক্রেডিট ও সীমা অ্যাকাউন্ট ও দেশভেদে আলাদা।",
            "<b>ডেভেলপার:</b> কোড পরিকল্পনা ও ডকুমেন্টেশনের খসড়া।",
        ],
        "choose": [
            "Gmail, Docs ও Drive-ভিত্তিক কাজ বেশি হলে Gemini দেখুন।",
            "ChatGPT-র নির্দিষ্ট টুল দরকার হলে আলাদাভাবে তুলনা করুন।",
            "দুটোই দরকার মনে হলে এক মাস একটি ব্যবহার করে দেখুন, তারপর সিদ্ধান্ত নিন।",
        ],
        "note": "কোনো একটি সব কাজে সবার জন্য সেরা নয়। আপনার অ্যাকাউন্টে কোন সুবিধা কতটা চালু হবে তা পেমেন্টের আগে লিখিতভাবে নিশ্চিত করুন, এবং Google-এর পেজে বর্তমান তালিকা মিলিয়ে নিন।",
        "tut_h": "গবেষণার একটি কাজ, ১০ মিনিটে",
        "tut": "“আমি বাংলাদেশের [আপনার বিষয়] নিয়ে একটি রিপোর্ট তৈরি করছি। প্রথমে বিষয়টি বোঝার ৮টি গুরুত্বপূর্ণ প্রশ্ন তৈরি করো। প্রতিটি প্রশ্নের জন্য কোন ধরনের প্রাথমিক সূত্র যাচাই করব তা জানাও। নির্ভরযোগ্য তথ্য না পেলে অনুমান করো না। শেষে ১ পৃষ্ঠার রিপোর্ট-রূপরেখা দাও এবং কোন তথ্য আমি নিজে যাচাই করব তা লেখো।”",
        "after": "Gemini-র দেওয়া সূত্র ও সংখ্যা নিজে খুলে দেখুন, তারপর রিপোর্টে ব্যবহার করুন।",
        "links": [("blog/chatgpt-plus-naki-gemini-konta-niben", "ChatGPT Plus নাকি Gemini — তুলনা"),
                  ("p/chatgpt-go", "ChatGPT Go পাতা")],
    },
}


def esc_keep(s: str) -> str:
    return s  # copy is static, authored here


def section(site: Path, page: Path, c: dict) -> str:
    links = []
    for path, label in c["links"]:
        if path.startswith("blog/"):
            if (site / f"{path}.html").exists():
                links.append(f'<a href="../../{path}">{label}</a>')
        elif (site / "bn" / f"{path}.html").exists():
            links.append(f'<a href="{path.split("/")[-1]}">{label}</a>')
    li = lambda items: "".join(f"<li>{x}</li>" for x in items)
    more = f'<p style="font-size:14px;margin:8px 0 0">আরও: {" · ".join(links)}</p>' if links else ""
    return (
        f'<section class="mt3" id="kaje-lage" {MARK}>'
        f'<h2 class="mt3" style="font-size:22px">{c["h2"]}</h2>'
        f'<ul style="margin:8px 0 12px 18px;padding:0;font-size:15px;line-height:1.7">{li(c["uses"])}</ul>'
        f'<h3 style="font-size:17px;margin:10px 0 4px">কোনটা বেছে নেবেন</h3>'
        f'<ul style="margin:6px 0 8px 18px;padding:0;font-size:15px;line-height:1.7">{li(c["choose"])}</ul>'
        f'<p style="font-size:15px;line-height:1.7;margin:0 0 8px">{c["note"]}</p>'
        f'<h3 style="font-size:17px;margin:10px 0 4px">{c["tut_h"]}</h3>'
        f'<div {BOX}>{c["tut"]}</div>'
        f'<p style="font-size:15px;line-height:1.7;margin:0">{c["after"]}</p>{more}'
        "</section>\n  "
    )


def apply(site: Path) -> int:
    for slug, c in PAGES.items():
        f = site / "bn" / "p" / f"{slug}.html"
        if not f.exists():
            print(f"[bn-buyer-copy] FAIL — missing {f.relative_to(site)}")
            return 1
        t = f.read_text(encoding="utf-8")
        if MARK in t:
            continue
        m = ANCHOR.search(t)
        if not m:
            print(f"[bn-buyer-copy] FAIL — anchor 'কীভাবে অর্ডার হয়' not found in {slug}")
            return 1
        f.write_text(t[: m.start()] + section(site, f, c) + t[m.start():], encoding="utf-8")
    print("[bn-buyer-copy] PASS — Bangla buyer guidance added to chatgpt-plus, chatgpt-go, google-ai-pro (no price, feature or authorization claim)")
    return 0


def check(site: Path) -> int:
    bad = [s for s in PAGES if MARK not in (site / "bn" / "p" / f"{s}.html").read_text(encoding="utf-8")]
    if bad:
        print("[bn-buyer-copy] FAIL — missing on:", ", ".join(bad))
        return 1
    print("[bn-buyer-copy] CHECK PASS")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    site = Path(args[0]) if args else ROOT / "_site"
    return check(site) if "--check" in sys.argv else apply(site)


if __name__ == "__main__":
    sys.exit(main())
