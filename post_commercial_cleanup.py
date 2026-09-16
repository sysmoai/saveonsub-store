#!/usr/bin/env python3
"""Remove legacy commercial fragments that live outside governed product bodies."""
from pathlib import Path
import re

SITE = Path(__file__).resolve().parent / "_site"

REPLACE = {
    "Starter Shared (6–8 users)": "Current plan",
    "Premium Shared (2–3 users)": "Current plan",
    "SHARED · LOW RISK": "ACCESS METHOD REQUIRES CONFIRMATION",
    "SHARED · MEDIUM RISK": "ACCESS METHOD REQUIRES CONFIRMATION",
    "SHARED · HIGH RISK": "ACCESS METHOD REQUIRES CONFIRMATION",
    "ChatGPT Plus — ৳499": "ChatGPT Plus — current approved price on product page",
    "ChatGPT Plus in Bangladesh from ৳499": "ChatGPT Plus in Bangladesh — see current approved price",
    "SAVEONSUB: ৳499": "SAVEONSUB: see current approved price",
    "ChatGPT Plus ৳499": "ChatGPT Plus — see current approved price",
    "ChatGPT Go — ৳450": "ChatGPT Go — see current approved price",
    "Google AI Pro ৳500": "Google AI Pro — see current approved price",
    "5–15 min delivery": "delivery timing confirmed before payment",
    "5–15 minutes": "timing confirmed before payment",
    "replacement within 1 hour": "order-specific support terms",
    "1-hour replacement": "order-specific support terms",
    "7-day warranty": "order-specific support terms",
    "30-day warranty": "order-specific support terms",
    "100% official": "clearly labeled",
    "100% authentic": "clearly labeled",
    "customer-owned": "customer-specific",
    "only BD store": "Bangladesh subscription store",
    "Bangladesh's honest subscription store": "Bangladesh subscription store",
    "Pay-after-testing": "Order-specific payment/access confirmation",
}


def main():
    changed = 0
    for path in SITE.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        old = text
        for src, dst in REPLACE.items():
            text = re.sub(re.escape(src), lambda _m, d=dst: d, text, flags=re.I)
        if path.name == "chatgpt-plus.html":
            text = re.sub(
                r'https://wa\.me/8801305869242\?text=[^"\']*ChatGPT\+Plus[^"\']*',
                'https://wa.me/8801305869242?text=Hi%21%20Please%20confirm%20the%20current%20ChatGPT%20Plus%20price%20and%20access%20method.',
                text,
                flags=re.I,
            )
        if text != old:
            path.write_text(text, encoding="utf-8")
            changed += 1
    print(f"[commercial-cleanup] normalized peripheral legacy fragments in {changed} HTML file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
