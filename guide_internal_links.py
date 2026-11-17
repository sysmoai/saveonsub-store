#!/usr/bin/env python3
"""Internal links between guides and product pages (build step, _site only).

GSC 17 Nov 2026: four new guides sat in "Discovered, not indexed" and every guide
had a single inbound link (the blog index); only 17 of 67 product pages linked to
any guide. This step adds plain crawlable links, no claims and no prices:
  - "Related guides" (3-4 topic-matched guides) at the end of every guide
  - "Guides" (2-3 topic-matched guides) on every EN /p and BN /bn/p page that
    has no guide link yet
Anchor text is the guide's own <h1>. Idempotent via data-sos marker.
`--check` verifies without writing.
"""
from __future__ import annotations

import html
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
MARK = "guide-links-2026-11-17"
BLOCK = re.compile(rf'<section[^>]*data-sos="{MARK}"[^>]*>.*?</section>\s*', re.S)
GUIDE_LINK = re.compile(r'href="(?:https://saveonsub\.com)?(?:\.\./|/)blog/[a-z0-9]')

# topic -> keywords found in the guide slug
TOPICS = {
    "chatgpt": ("chatgpt",), "claude": ("claude",), "google": ("gemini", "google-ai"),
    "grok": ("grok",), "deepseek": ("deepseek",), "canva": ("canva",),
    "image": ("midjourney",), "video": ("video", "capcut"), "stream": ("netflix",),
    "money": ("bkash", "kenar-age", "bangladesh-theke", "renewal", "shared", "parthokko", "sourc"),
    "learn": ("student", "porashona", "prompt", "shikhte", "coursera", "free-ai"),
}
GENERIC = ["shared-personal-official-plan-parthokko-bangla", "how-to-pay-for-ai-tools-with-bkash",
           "ai-subscription-kenar-age-7ti-proshno", "shared-vs-personal-ai-subscriptions-honest-guide",
           "how-we-source-subscriptions-transparency", "bangladesh-theke-ai-subscription-kivabe-kinben",
           "ai-subscription-renewal-cancel-checklist-bangla"]
# product id fragment -> topics
PRODUCT_TOPICS = [
    ("chatgpt", ["chatgpt"]), ("claude", ["claude"]), ("google-ai", ["google"]), ("gemini", ["google"]),
    ("grok", ["grok"]), ("deepseek", ["deepseek"]), ("canva", ["canva"]),
    ("midjourney", ["image"]), ("leonardo", ["image"]), ("ideogram", ["image"]),
    ("netflix", ["stream"]), ("spotify", ["stream"]), ("youtube", ["stream"]), ("prime", ["stream"]),
    ("hoichoi", ["stream"]), ("capcut", ["video"]), ("invideo", ["video"]), ("runway", ["video"]),
    ("kling", ["video"]), ("heygen", ["video"]), ("synthesia", ["video"]), ("descript", ["video"]),
]


def text(frag: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", frag))).strip()


def guides() -> dict[str, str]:
    out = {}
    for f in sorted((SITE / "blog").glob("*.html")):
        if f.stem == "index":
            continue
        m = re.search(r"<h1[^>]*>(.*?)</h1>", f.read_text(encoding="utf-8"), re.S)
        if m and text(m.group(1)):
            out[f.stem] = text(m.group(1))
    return out


def topics_of(slug: str) -> set[str]:
    return {t for t, keys in TOPICS.items() if any(k in slug for k in keys)}


def pick(want: set[str], exclude: str, g: dict[str, str], n: int, seed: str = "") -> list[str]:
    ranked = sorted((s for s in g if s != exclude and want & topics_of(s)),
                    key=lambda s: (-len(want & topics_of(s)), s))
    chosen = ranked[:n]
    off = zlib.crc32((seed or exclude).encode()) % len(GENERIC)
    for s in GENERIC[off:] + GENERIC[:off]:
        if len(chosen) >= n:
            break
        if s in g and s != exclude and s not in chosen:
            chosen.append(s)
    return chosen


def section(slugs: list[str], g: dict[str, str], bn: bool) -> str:
    head = "আরও গাইড" if bn else "Related guides"
    items = "".join(f'<li><a href="/blog/{s}">{html.escape(g[s])}</a></li>' for s in slugs)
    return (f'<section data-sos="{MARK}" class="related-guides"><h2 class="mt3" style="font-size:22px">{head}</h2>'
            f'<ul style="line-height:1.9;padding-left:20px">{items}</ul></section>\n')


def insert(t: str, sec: str) -> str:
    i = t.rfind("</div></main>")
    if i == -1:
        i = t.rfind("</main>")
    return t[:i] + sec + t[i:] if i != -1 else t


def run() -> int:
    g = guides()
    n_blog = n_prod = 0
    for f in sorted((SITE / "blog").glob("*.html")):
        if f.stem == "index":
            continue
        t = BLOCK.sub("", f.read_text(encoding="utf-8"))
        have = {m.split("/")[-1].removesuffix(".html") for m in re.findall(r'href="([^"#?]+)"', t)} & set(g)
        if len(have - {f.stem}) >= 2:
            continue
        slugs = pick(topics_of(f.stem), f.stem, g, 4)
        if slugs:
            f.write_text(insert(t, section(slugs, g, False)), encoding="utf-8")
            n_blog += 1
    for base, bn in ((SITE / "p", False), (SITE / "bn" / "p", True)):
        for f in sorted(base.glob("*.html")):
            t = BLOCK.sub("", f.read_text(encoding="utf-8"))
            if GUIDE_LINK.search(t):
                f.write_text(t, encoding="utf-8")
                continue
            want = set()
            for frag, tops in PRODUCT_TOPICS:
                if frag in f.stem:
                    want |= set(tops)
            slugs = pick(want, "", g, 3, f.stem)
            if slugs:
                f.write_text(insert(t, section(slugs, g, bn)), encoding="utf-8")
                n_prod += 1
    print(f"[guide-links] PASS — related-guide blocks on {n_blog} guides and {n_prod} product pages")
    return 0


def check() -> int:
    n = sum(1 for f in (SITE / "blog").glob("*.html") if BLOCK.search(f.read_text(encoding="utf-8")))
    m = sum(1 for d in (SITE / "p", SITE / "bn" / "p") for f in d.glob("*.html") if BLOCK.search(f.read_text(encoding="utf-8")))
    if n < 20 or m < 60:
        print(f"[guide-links] FAIL — blocks on {n} guides, {m} product pages")
        return 1
    print(f"[guide-links] PASS — blocks on {n} guides, {m} product pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(check() if "--check" in sys.argv else run())
