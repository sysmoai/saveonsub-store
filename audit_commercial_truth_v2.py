#!/usr/bin/env python3
"""Fail closed if the staged SaveOnSub release regresses commercial truth."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
REVISION = "pricing-v2-2026-09-17"

EXPECTED = {
    "chatgpt-go": (1299, "Customer-specific access"),
    "chatgpt-plus": (3390, "Customer-specific access"),
    "chatgpt-business": (4290, "Team / Workspace access"),
    "claude-pro": (3390, "Customer-specific access"),
    "google-ai-pro": (3390, "Customer-specific access"),
}

FORBIDDEN = [
    "Starter Shared (6–8 users)",
    "Premium Shared (2–3 users)",
    "ChatGPT Plus — ৳499",
    "ChatGPT Plus in Bangladesh from ৳499",
    "SAVEONSUB: ৳499",
    "ChatGPT Go — ৳450",
    "ChatGPT Plus ৳499",
    "Google AI Pro ৳500",
    "SHARED · POLICY RISK",
    "SHARED · WARRANTY COVERED",
    "SHARED · LOW RISK",
    "5–15 min delivery",
    "5–15 minutes",
    "replacement within 1 hour",
    "1-hour replacement",
    "7-day warranty",
    "30-day warranty",
    "100% official",
    "100% authentic",
    "customer-owned",
    "only BD store",
    "Bangladesh's honest subscription store",
    "BANGLADESH'S HONEST SUBSCRIPTION STORE",
    "Pay-after-testing",
]


def fail(msg: str):
    raise SystemExit("[commercial-audit] FAIL: " + msg)


def main() -> int:
    if not SITE.exists():
        fail("_site missing")

    home = (SITE / "index.html").read_text(encoding="utf-8", errors="replace")
    if f'name="saveonsub-commercial-revision" content="{REVISION}"' not in home:
        fail("homepage commercial revision marker missing")
    if f'data-commercial-truth="{REVISION}"' not in home:
        fail("homepage governed body marker missing")

    plus = SITE / "p" / "chatgpt-plus.html"
    if not plus.exists():
        fail("ChatGPT Plus canonical page missing")
    plus_text = plus.read_text(encoding="utf-8", errors="replace")
    if "৳3,390 / month" not in plus_text or "Customer-specific access" not in plus_text:
        fail("ChatGPT Plus approved price/access not rendered")
    if "Starter Shared" in plus_text or "Premium Shared" in plus_text:
        fail("credential-shared ChatGPT Plus offer survived")

    biz = SITE / "p" / "chatgpt-business.html"
    if biz.exists():
        t = biz.read_text(encoding="utf-8", errors="replace")
        if "৳4,290 / user / month" not in t or "Team / Workspace access" not in t:
            fail("ChatGPT Business per-user Team/Workspace semantics missing")

    pro = SITE / "p" / "chatgpt-pro.html"
    if pro.exists():
        t = pro.read_text(encoding="utf-8", errors="replace")
        if "PRICE REVIEW REQUIRED" not in t or re.search(r"Add to cart", t, re.I):
            fail("ChatGPT Pro must remain inquiry-only")

    # The browser catalog is public data. Internal survey/proof/cost metadata must
    # not be shipped to visitors even if it remains in the source catalog.
    public_catalog = (SITE / "assets" / "catalog.js").read_text(encoding="utf-8", errors="replace")
    if REVISION not in public_catalog:
        fail("public catalog revision missing")
    for key in ("market_survey", '"market":', "bestseller_rank", "order_count", "supplier_cost", '"margin":', '"profit":', '"warranty":', '"delivery_slas":'):
        if key in public_catalog:
            fail(f"internal/unsupported public catalog field leaked: {key}")

    hits = []
    for path in SITE.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in FORBIDDEN:
            if phrase.lower() in text.lower():
                hits.append((path.relative_to(SITE).as_posix(), phrase))
                if len(hits) >= 30:
                    break
        if len(hits) >= 30:
            break
    if hits:
        fail("forbidden legacy commercial claims survived: " + "; ".join(f"{p}: {x}" for p, x in hits))

    # Check the highest-value fixed pages exactly. Missing pages are a release
    # error only for the canonical OpenAI/Claude/Google rows used in production QA.
    for pid, (price, access) in EXPECTED.items():
        path = SITE / "p" / f"{pid}.html"
        if not path.exists():
            fail(f"expected governed page missing: {pid}")
        text = path.read_text(encoding="utf-8", errors="replace")
        if f"৳{price:,}" not in text or access not in text:
            fail(f"governed price/access mismatch: {pid}")

    print(f"[commercial-audit] PASS revision={REVISION}; fixed pages and public catalog are governed; legacy shared/claim regressions absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
