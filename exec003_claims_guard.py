#!/usr/bin/env python3
"""Fail-closed customer-facing claims guard for the staged artifact (_site).

This guard FAILS the build; it never rewrites. It runs after every rewriting
stage, so whatever it sees is exactly what would be published.

Blocked claim families (EN + BN):
  traction counts ("3000 customers served", "156+ orders", "#1 seller"),
  same-day promises, warranty-with-replacement / timed replacement promises,
  minute-range delivery SLAs, BN "ওয়ারেন্টিসহ", Pay-After-Testing offers,
  price-match promises, SAVE N% badges, "100% customer-owned"/"Every
  subscription is official", and prose rewrites that leaked into link targets.

The only exemption is REFUND_PAGES: the exact table cells of the existing
refund rights (refund.html / bn/refund.html), which stay untouched until the
founder approves a narrower refund draft (EXEC-010 D3). Exemptions match whole
cell text exactly; anything else on those pages is still checked.

Usage: python3 exec003_claims_guard.py [SITE_DIR]
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent

RULES: dict[str, re.Pattern] = {
    "traction": re.compile(
        r"\b\d[\d,]*\+?\s*(?:happy\s+|satisfied\s+)?(?:customers|clients|buyers|orders|subscribers|Bangladeshis)\b"
        r"|\b\d[\d,]*\+\s*(?:users|students)\b"
        r"|(?<![%\w])(?:[০-৯\d][০-৯\d,]*\+|[০-৯\d]{3,}[০-৯\d,]*)\s*(?:জন\s*)?(?:গ্রাহক|অর্ডার|ক্রেতা)"
        r"|#\s?1\s+(?:seller|store|choice)|#\s?১|\bbest[- ]?sell(?:er|ing)\b|\bmarket[- ]leader\b|বেস্ট\s?সেলার",
        re.I),
    "same_day": re.compile(r"\bsame[- ]day\b|একই\s*দিনে|সেম[- ]ডে", re.I),
    "warranty_replacement": re.compile(
        r"(?:warranty|guarantee|ওয়ারেন্টি|ওয়ারেন্টি|গ্যারান্টি)[^.।!?\n]{0,80}(?:replace|রিপ্লেসমেন্ট)"
        r"|(?:replace|রিপ্লেসমেন্ট)\w*[^.।!?\n]{0,60}(?:warranty|guarantee|ওয়ারেন্টি|ওয়ারেন্টি|গ্যারান্টি)"
        r"|\breplace\w*\s+(?:\w+\s+){0,3}within\s+\d+\s*(?:min|minutes|hours?|h)\b"
        r"|\b\d+[- ]hour\s+replacement\b"
        r"|[০-৯\d]+\s*ঘণ্টার\s*(?:মধ্যে\s*)?(?:রিপ্লেসমেন্ট|replacement)"
        r"|\b\d+[- ]day\s+(?:warranty|guarantee|coverage)\b"
        r"|[০-৯\d]+\s*দিন(?:ের)?\s*(?:ওয়ারেন্টি|ওয়ারেন্টি|গ্যারান্টি)",
        re.I),
    "minute_sla": re.compile(
        r"\b\d+\s*[–-]\s*\d+\s*(?:min|mins|minutes)\b|[০-৯]+\s*[–-]\s*[০-৯]+\s*মিনিট"
        r"|\bwithin\s+\d+\s*(?:min|mins|minutes)\b|[০-৯\d]+\s*মিনিটের\s*মধ্যে",
        re.I),
    "bn_warranty_included": re.compile(r"ওয়ারেন্টিসহ|ওয়ারেন্টিসহ|ওয়ারেন্টি\s+সহ"),
    "pay_after_testing": re.compile(r"pay[- ]?after[- ]?testing|পে[- ]?আফটার[- ]?টেস্টিং", re.I),
    "price_match": re.compile(r"price[- ]?match|beat any price|lowest price guarantee|প্রাইস[- ]?ম্যাচ|আমরা ম্যাচ করব|দাম মিলিয়ে|\bwe match it\b", re.I),
    "save_percent": re.compile(r"\bSAVE\s+\d{1,3}\s?%|\b\d{1,3}\s?%\s*(?:off|cheaper|সাশ্রয়|ছাড়)|-\d{1,3}%\s*সাশ্রয়|অফিসিয়াল দামের চেয়ে অনেক কম", re.I),
    "customer_owned_official": re.compile(r"100%\s*customer[- ]owned|Every subscription is official|১০০%\s*গ্রাহক[- ]নিয়ন্ত্রিত|১০০%\s*অফিসিয়াল|100%\s*official", re.I),
}

LINK_TARGET = re.compile(r'\b(?:href|src|action)\s*=\s*"[^"]*support terms', re.I)

# Exact refund-rights cells (EXEC-010 D3 pending founder approval). Whole-cell
# text match only; keys are page paths relative to the site root.
REFUND_PAGES: dict[str, frozenset[str]] = {
    "refund.html": frozenset({
        "Not delivered within 24h of payment",
        "Same day, to your bKash/Nagad",
        "Same day",
        "Within 24h of failed replacement",
        "Within 1 hour",
    }),
    "bn/refund.html": frozenset({
        "পেমেন্টের ২৪ ঘণ্টায় ডেলিভারি না হলে",
        "পূর্ণ রিফান্ড, একই দিনে",
    }),
}

# TEMPORARY, founder-gated (T018-16 / EXEC-010 D3): the refund pages' existing
# <title>/meta copy restates the same-day refund right. It may not be edited
# until Emon approves a narrow refund draft, so these exact head strings are
# skipped on these two pages only. Delete this table in the same change that
# applies the approved refund draft.
REFUND_D3_PENDING_HEAD: dict[str, tuple[str, ...]] = {
    "refund.html": (
        "Refund Policy — Same-Day, No Games | SAVEONSUB",
        "Paid back to your bKash same day.",
    ),
    "bn/refund.html": (
        "রিফান্ড নীতি — একই দিনে, কোনো ফাইন-প্রিন্ট নয় | SAVEONSUB",
        "একই দিনে আপনার বিকাশ/নগদে ফেরত।",
    ),
}

CELL = re.compile(r"<td\b[^>]*>(.*?)</td>", re.I | re.S)


def visible_text(raw: str) -> str:
    """Body text plus customer-visible metadata, JSON-LD and decoded WA prefills."""
    parts = []
    for m in re.finditer(r'<meta\s+[^>]*(?:name|property)="(?:description|og:title|og:description|twitter:title|twitter:description)"[^>]*content="([^"]*)"', raw, re.I):
        parts.append(m.group(1))
    for m in re.finditer(r'<title>(.*?)</title>', raw, re.I | re.S):
        parts.append(m.group(1))
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', raw, re.I | re.S):
        parts.append(m.group(1))
    for m in re.finditer(r'wa\.me/\d+\?text=([^"\'<>]+)', raw):
        parts.append(unquote(html.unescape(m.group(1))))
    body = re.sub(r"<script\b(?![^>]*ld\+json)[^>]*>.*?</script>|<style\b.*?</style>|<!--.*?-->", " ", raw, flags=re.S | re.I)
    body = re.sub(r"<script[^>]*ld\+json[^>]*>.*?</script>", " ", body, flags=re.S | re.I)
    parts.append(re.sub(r"<[^>]+>", " ", body))
    return re.sub(r"\s+", " ", html.unescape(" \n ".join(parts)))


def strip_exempt_cells(rel: str, raw: str) -> str:
    allowed = REFUND_PAGES.get(rel)
    if not allowed:
        return raw
    head_end = raw.lower().find("</head>")
    if head_end > 0:
        head = raw[:head_end]
        for exact in REFUND_D3_PENDING_HEAD.get(rel, ()):
            head = head.replace(exact, "")
        raw = head + raw[head_end:]

    def repl(m: "re.Match") -> str:
        cell = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()
        return "<td></td>" if cell in allowed else m.group(0)

    return CELL.sub(repl, raw)


def scan_text(rel: str, text: str) -> list[tuple[str, str, str]]:
    hits = []
    for name, pat in RULES.items():
        for m in pat.finditer(text):
            hits.append((rel, name, text[max(0, m.start() - 50):m.end() + 30].strip()))
    return hits


def scan_site(site: Path) -> list[tuple[str, str, str]]:
    hits: list[tuple[str, str, str]] = []
    for path in sorted(site.rglob("*.html")):
        rel = path.relative_to(site).as_posix()
        raw = path.read_text(encoding="utf-8", errors="replace")
        for m in LINK_TARGET.finditer(raw):
            hits.append((rel, "rewritten_link_target", m.group(0)))
        hits.extend(scan_text(rel, visible_text(strip_exempt_cells(rel, raw))))
    llms = site / "llms.txt"
    if llms.exists():
        hits.extend(scan_text("llms.txt", llms.read_text(encoding="utf-8", errors="replace")))
    return hits


def main(argv: list[str]) -> int:
    site = Path(argv[1]) if len(argv) > 1 else ROOT / "_site"
    if not site.is_dir():
        print(f"[claims-guard] {site} is missing; build first", file=sys.stderr)
        return 1
    hits = scan_site(site)
    if hits:
        print(f"[claims-guard] FAIL — {len(hits)} blocked claim(s):")
        for rel, name, ctx in hits[:60]:
            print(f"  {rel}: {name}: …{ctx}…")
        if len(hits) > 60:
            print(f"  … and {len(hits) - 60} more")
        return 1
    print("[claims-guard] PASS — no blocked traction/SLA/warranty/PAT/price-match/savings/ownership claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
