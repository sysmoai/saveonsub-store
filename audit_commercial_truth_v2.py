#!/usr/bin/env python3
"""Fail-closed audit for the 2026-09-17 SaveOnSub commercial projection."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
POLICY = json.loads((ROOT / "ops" / "PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
REV = POLICY["revision"]


def money(bdt: int) -> str:
    return f"৳{int(bdt):,}"


def hold_active() -> bool:
    return (POLICY.get("commercial_hold") or {}).get("status") == "HOLD"


def read(rel: str) -> str:
    path = SITE / rel
    if not path.exists():
        raise SystemExit(f"[commercial-audit] missing {rel}")
    return path.read_text(encoding="utf-8", errors="replace")


def need(text: str, needle: str, where: str) -> None:
    if needle not in text:
        raise SystemExit(f"[commercial-audit] {where} missing {needle!r}")


def forbid(text: str, needle: str, where: str) -> None:
    if needle.lower() in text.lower():
        raise SystemExit(f"[commercial-audit] {where} contains blocked legacy text {needle!r}")


def main() -> int:
    home = read("index.html")
    plus = read("p/chatgpt-plus.html")
    go = read("p/chatgpt-go.html")
    business = read("p/chatgpt-business.html")
    pro = read("p/chatgpt-pro.html")
    google = read("p/google-ai-pro.html")
    public_catalog = read("assets/catalog.js")

    for where, text in {
        "home": home,
        "ChatGPT Plus": plus,
        "ChatGPT Go": go,
        "ChatGPT Business": business,
        "ChatGPT Pro": pro,
        "Google AI Pro": google,
    }.items():
        need(text, REV, where)

    if not hold_active():
        raise SystemExit("[commercial-audit] EXEC-010 commercial HOLD is not active in the pricing policy; "
                         "fixed prices require explicit founder approval and an updated audit")
    for rule_id, rule in POLICY["approved_products"].items():
        if rule.get("mode") != "inquiry" or rule.get("plans"):
            raise SystemExit(f"[commercial-audit] policy rule {rule_id} publishes a fixed price during HOLD")
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    for product in catalog["products"]:
        if not product.get("request_price") or product.get("plans"):
            raise SystemExit(f"[commercial-audit] {product.get('id')} is not Price on Request during HOLD")
    if re.search(r'"bdt"\s*:', public_catalog):
        raise SystemExit("[commercial-audit] public catalog exposes a sell price during HOLD")

    # Every product page, EN and BN: no sell price in <main>, no cart action,
    # no priced Offer, no price in the WhatsApp prefill, no checkout CTA.
    from urllib.parse import unquote
    pages = sorted((SITE / "p").glob("*.html")) + sorted((SITE / "bn" / "p").glob("*.html"))
    if len(pages) != 2 * len(catalog["products"]):
        raise SystemExit(f"[commercial-audit] expected {2 * len(catalog['products'])} product pages, found {len(pages)}")
    for path in pages:
        rel = path.relative_to(SITE).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        need(text, REV, rel)
        main = re.search(r"<main\b.*?</main>", text, re.S | re.I)
        if not main:
            raise SystemExit(f"[commercial-audit] {rel} has no <main>")
        if re.search(r"৳\s?[1-9১-৯]", main.group(0)):
            raise SystemExit(f"[commercial-audit] {rel} shows a ৳ figure in <main> during HOLD")
        if "cartAdd" in text or "checkout.html" in main.group(0):
            raise SystemExit(f"[commercial-audit] {rel} has a cart/checkout action during HOLD")
        if re.search(r'"price"\s*:\s*"?[1-9]', text):
            raise SystemExit(f"[commercial-audit] {rel} has a priced structured-data Offer during HOLD")
        for m in re.findall(r'wa\.me/\d+\?text=([^"\'<>]+)', text):
            if re.search(r"৳\s?[1-9১-৯]", unquote(m)):
                raise SystemExit(f"[commercial-audit] {rel} WhatsApp prefill carries a price during HOLD")
    # Every other staged page: no listing/bundle/Mode sell price, "from ৳N",
    # discount or static cart action while the HOLD is active.
    surface = [
        (re.compile(r'<div class="price"[^>]*>\s*৳\s?[1-9১-৯]'), "listing card price"),
        (re.compile(r"onclick=\"cartAdd\('(?!\$\{)"), "static cart action"),
        (re.compile(r'\b[Ff]rom ৳\s?[1-9]'), "'from ৳N' sell price"),
        (re.compile(r'Mode price: ৳'), "Mode price"),
        (re.compile(r'৳\s?[\d,]+ off\b|৳[০-৯\d,]+ ছাড়'), "discount offer"),
        (re.compile(r'Saves? (?:up to )?৳'), "savings figure"),
    ]
    for path in sorted(SITE.rglob("*.html")):
        rel = path.relative_to(SITE).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, what in surface:
            if pattern.search(text):
                raise SystemExit(f"[commercial-audit] {rel} shows a {what} during HOLD")

    for where, text in {"ChatGPT Plus": plus, "Google AI Pro": google, "ChatGPT Pro": pro, "ChatGPT Go": go, "ChatGPT Business": business}.items():
        need(text, "Confirm current price", where)
    need(plus, "commercial HOLD", "ChatGPT Plus")
    need(google, "Price on Request", "Google AI Pro")
    need(public_catalog, REV, "public catalog")
    need(public_catalog, '"id":"chatgpt-plus"', "public catalog")

    for where, text in {
        "home": home,
        "ChatGPT Plus": plus,
        "ChatGPT Go": go,
        "ChatGPT Business": business,
        "ChatGPT Pro": pro,
        "public catalog": public_catalog,
    }.items():
        for phrase in (
            "SHARED · POLICY RISK",
            "SHARED · WARRANTY COVERED",
            "5–15 min",
            "5-15 min",
            "SAVE 77%",
            "1-hour replacement",
            "Official · Personal · Shared",
        ):
            forbid(text, phrase, where)

    for legacy in ("৳499", "৳999", "৳2,990"):
        forbid(plus, legacy, "ChatGPT Plus")

    # The public browser catalog must not contain credential-shared ChatGPT Plus
    # plans even if the raw historical source catalog still retains them for audit.
    m = re.search(r'\{"id":"chatgpt-plus".*?(?=\},\{"id":|\}\]\})', public_catalog)
    if m and '"type":"shared"' in m.group(0):
        raise SystemExit("[commercial-audit] public ChatGPT Plus catalog still contains shared access")

    print("[commercial-audit] PASS — EXEC-010 HOLD (Price on Request) verified on every product page; legacy-claim blocks verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
