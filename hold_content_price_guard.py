#!/usr/bin/env python3
"""Fail-closed guard: no SaveOnSub sale price may survive in any staged HTML page.

Under EXEC-010 every SaveOnSub SKU is commercial HOLD / price on request. The
product pages are already governed, but blog, category, student, FAQ and quiz
pages are hand-written HTML that still quoted historical SaveOnSub prices
(e.g. "We sell it at ৳500", "shared seat ৳499/month").

This step runs on the final staged ``_site`` only (source HTML is untouched so
history stays auditable). It:

1. applies a small set of reviewed sentence rewrites where a mechanical
   replacement would read badly or would still advertise a HOLD offer
   (shared seats);
2. masks taka amounts that are *not* SaveOnSub offers: official provider
   prices, approximate official conversions (~৳), surveyed market ranges,
   quiz budget bands and a quoted scam example;
3. replaces every remaining ``৳<amount>`` with "price on request";
4. re-scans every staged HTML file and exits non-zero if any unmasked
   taka amount remains.

Run with ``--check`` to only verify (no writes).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"

G = r"(?:\s|<[^>]*>)*"  # whitespace and/or tags between words
AMOUNT = r"৳\s?[1-9][0-9]*(?:,[0-9]{3})*"
SUFFIX = r"(?:/mo(?:nth)?)?"
REPLACEMENT = "price on request"
# Under a CEO selective unlock, editorial pages point to the governed product
# page instead of repeating a possibly stale amount.
UNLOCK_REPLACEMENT = "current price on the product page"

# (regex, replacement). Reviewed rewrites; order matters.
REWRITES: list[tuple[str, str]] = [
    # Google AI Pro explainer (URL kept for SEO continuity).
    (r"Google AI Pro at ৳500(?: in Bangladesh)? — [Hh]ow [Ii]s [Ii]t [Pp]ossib\w*(?:, honestly)?\??",
     "Google AI Pro in Bangladesh — honest explainer"),
    (r'Google AI Pro at <span class="grad-text">৳500</span> — how is it possible\?',
     'Google AI Pro in Bangladesh — <span class="grad-text">honest explainer</span>'),
    (r"We sell it at ৳500 on your own Gmail\.",
     "SaveOnSub lists it as price on request (commercial review) for your own Gmail."),
    (r"How is Google AI Pro only ৳500 in Bangladesh\?",
     "What does Google AI Pro cost in Bangladesh?"),
    (r"Is the ৳500 Google AI Pro safe\?", "Is Google AI Pro on your own Gmail safe?"),
    (r"Get Google AI Pro — ৳500 →", "Ask about Google AI Pro →"),
    (r"Google AI Pro at ৳500", "Google AI Pro"),
    (r"And the ৳500 reflects current regional pricing", "Any quote reflects current regional pricing"),
    # ChatGPT Plus price guide: never advertise a shared seat.
    (r"Real BD options compared: shared ৳499, personal ৳2,990, bKash payment",
     "Real BD options compared, with bKash payment"),
    (r"Via SAVEONSUB: shared seat ৳499/month or personal account ৳2,990/month, paid with bKash/Nagad\.",
     "SaveOnSub does not sell shared ChatGPT seats; help with a personal account is price on request while under commercial review."),
    (r"(Shared seat \(6–8 users\)</a></td><td>)৳499/mo", r"\1not offered (HOLD)"),
    (r"Upgrade to ৳499 shared or a personal plan", "Upgrade to a personal plan"),
    (r"usually cheaper \(৳499 vs ৳2,200\)", "usually cheaper (vs ~৳2,200 official)"),
    # Midjourney / Leonardo (Midjourney shared is CEO HOLD).
    (r"Midjourney ৳499 vs Leonardo ৳599 in BD", "Midjourney vs Leonardo in BD"),
    (r"Midjourney shared starts at ৳499/month, Leonardo at ৳599/month via SAVEONSUB with bKash\.",
     "Midjourney and Leonardo are price on request at SaveOnSub while under commercial review."),
    (r"Both sell for under ৳600 here \(156 and customer orders respectively on our legacy store\)\.",
     "Both are price on request here while under commercial review."),
    (r"Many BD creators run both for under ৳1,100 total\.", "Many BD creators run both."),
]

# Taka amounts that are NOT SaveOnSub offers. Matched spans are protected.
ALLOWED: list[str] = [
    r"~" + AMOUNT,                                              # approx official conversion
    r"[Oo]fficial(?:ly)?[^৳<>]{0,30}" + AMOUNT,                 # "official BD ৳109"
    AMOUNT + SUFFIX + r"\s+official",                          # "৳109 official"
    r"Google lists it at ৳2,500",
    r"(?i:individual|student|duo|family)\s+৳(?:219|109|299|379)\b",   # Spotify BD official
    r"৳(?:219|109|299|379)(?:/month)?\s+(?i:individual|student|duo|family)",
    r"Spotify ৳109\b",
    AMOUNT + r"\s?–\s?[0-9][0-9,]*",                          # surveyed range "৳399–1,249"
    r"market starts around " + AMOUNT,
    r"Under ৳500", r"৳500 – ৳1,000", r"৳1,000\+",              # quiz budget bands
    r"Lifetime ChatGPT ৳999",                                  # scam example
    r"seller offers (?:'|&#x27;|&#39;)ChatGPT ৳350",            # market example
    r"Official \(own card/friend abroad\)" + G + AMOUNT + SUFFIX,
]

AMOUNT_RE = re.compile(AMOUNT + SUFFIX)
ALLOWED_RE = re.compile("|".join(f"(?:{p})" for p in ALLOWED))
MASK = "\x00{}\x00"


def _mask(text: str) -> tuple[str, list[str]]:
    kept: list[str] = []

    def keep(m: re.Match) -> str:
        kept.append(m.group(0))
        return MASK.format(len(kept) - 1)

    return ALLOWED_RE.sub(keep, text), kept


def _unmask(text: str, kept: list[str]) -> str:
    return re.sub("\x00(\\d+)\x00", lambda m: kept[int(m.group(1))], text)


def unlock_book() -> dict[str, set[int]] | None:
    """Approved BDT amounts per product id, or None while the global HOLD applies."""
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if (policy.get("commercial_hold") or {}).get("status") != "SELECTIVE_UNLOCK":
        return None
    return {
        pid: {int(p["bdt"]) for p in rule.get("plans") or []}
        for pid, rule in (policy.get("approved_products") or {}).items()
        if rule.get("mode") == "fixed"
    }


def page_product(rel: str) -> str | None:
    m = re.fullmatch(r"(?:bn/)?p/([a-z0-9-]+)\.html", rel.replace("\\", "/"))
    return m.group(1) if m else None


def _amount(token: str) -> int:
    return int(re.sub(r"[^0-9]", "", token.split("/")[0]))


CARD = re.compile(r'<div class="pcard">(?:(?!<div class="pcard">).)*?href="/?(?:bn/)?p/([a-z0-9-]+)(?:\.html)?"', re.S)
CARD_PRICE = re.compile(r'(<div class="price">)([^<]*)(</div>)')


def _mask_cards(text: str, book: dict[str, set[int]], kept: list[str]) -> str:
    """Listing cards may show a CEO-approved price of the product they link to."""
    def card(m: re.Match) -> str:
        allowed = book.get(m.group(1), set())

        def price(pm: re.Match) -> str:
            amounts = [_amount(a) for a in AMOUNT_RE.findall(pm.group(2))]
            if amounts and all(a in allowed for a in amounts):
                kept.append(pm.group(2))
                return pm.group(1) + MASK.format(len(kept) - 1) + pm.group(3)
            return pm.group(0)

        return CARD_PRICE.sub(price, m.group(0))

    return CARD.sub(card, text)


def sanitize(text: str, approved: set[int] | None = None, unlock: bool = False,
             book: dict[str, set[int]] | None = None) -> str:
    if not unlock:
        for pattern, repl in REWRITES:
            text = re.sub(pattern, repl, text)
    masked, kept = _mask(text)
    if book:
        masked = _mask_cards(masked, book, kept)

    def repl(m: re.Match) -> str:
        if approved and _amount(m.group(0)) in approved:
            return m.group(0)
        return UNLOCK_REPLACEMENT if unlock else REPLACEMENT

    masked = AMOUNT_RE.sub(repl, masked)
    return _unmask(masked, kept)


def residues(text: str, approved: set[int] | None = None,
             book: dict[str, set[int]] | None = None) -> list[str]:
    masked, kept = _mask(text)
    if book:
        masked = _mask_cards(masked, book, kept)
    plain = re.sub(r"\s+", " ", masked)
    out = []
    for m in AMOUNT_RE.finditer(plain):
        if approved and _amount(m.group(0)) in approved:
            continue
        out.append(plain[max(0, m.start() - 50): m.end() + 20])
    return out


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    if not SITE.is_dir():
        raise SystemExit("[hold-content-price] missing _site; run build_site.py")
    book = unlock_book()
    unlock = book is not None
    changed, failures = 0, []
    for path in sorted(SITE.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        pid = page_product(str(path.relative_to(SITE)))
        approved = (book or {}).get(pid) if pid else None
        if not check_only:
            new = sanitize(text, approved, unlock, book)
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
                text = new
        for ctx in residues(text, approved, book):
            failures.append(f"{path.relative_to(SITE)}: …{ctx}…")
    if failures:
        print("[hold-content-price] FAIL — SaveOnSub sale price still present under EXEC-010 HOLD:")
        for f in failures[:50]:
            print("  " + f)
        return 1
    mode = "checked" if check_only else f"sanitized {changed} page(s);"
    if unlock:
        print(f"[hold-content-price] PASS — {mode} only CEO-approved prices on their own product pages")
    else:
        print(f"[hold-content-price] PASS — {mode} no SaveOnSub sale price in staged HTML")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
