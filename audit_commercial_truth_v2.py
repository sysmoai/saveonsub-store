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


def approved_price(sku: str) -> str:
    # Previously hardcoded literal prices here went stale the moment Pricing V2
    # changed (exactly what happened to chatgpt-go after the 2026-10-23 reprice
    # and to google-ai-pro after it moved to inquiry-only) — read the current
    # approval instead of duplicating it.
    rule = POLICY["approved_products"][sku]
    return money(rule["plans"][0]["bdt"])


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

    need(plus, approved_price("chatgpt-plus"), "ChatGPT Plus")
    need(plus, "Customer-specific access", "ChatGPT Plus")
    need(go, approved_price("chatgpt-go"), "ChatGPT Go")
    need(business, f'{approved_price("chatgpt-business")} / user / month', "ChatGPT Business")
    need(business, "Team / Workspace access", "ChatGPT Business")
    need(pro, "Confirm current price", "ChatGPT Pro")
    need(google, approved_price("google-ai-pro"), "Google AI Pro")
    need(public_catalog, REV, "public catalog")
    need(public_catalog, '"id":"chatgpt-plus"', "public catalog")
    need(public_catalog, f'"bdt":{POLICY["approved_products"]["chatgpt-plus"]["plans"][0]["bdt"]}', "public catalog")

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

    print("[commercial-audit] PASS — approved prices, access semantics and legacy-claim blocks verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
