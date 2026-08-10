#!/usr/bin/env python3
"""Release gate for the strict SAVEONSUB L1 public-information artifact.

This is intentionally separate from validate_release.py, which continues to
report legacy/current-source commerce problems during migration. A deployment
may use this gate only when it builds and stages the strict _public_v3 artifact.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

from authority_model import load_authority

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "_public_v3"
errors: list[str] = []


def fail(code: str, message: str) -> None:
    errors.append(f"{code}: {message}")


def main() -> int:
    authority = load_authority()
    launch = authority["launch"]
    pricing = authority["pricing"]
    payment = authority["payment"]
    contact = authority["contact"]
    legal = authority["legal"]

    if launch.get("state") != "L1_PUBLIC_INFO_ONLY":
        fail("L1-STATE", f"launch state is {launch.get('state')!r}, expected L1_PUBLIC_INFO_ONLY")
    if launch.get("launch_authorization") != "PROVEN_FOR_L1_PUBLIC_INFORMATION":
        fail("L1-AUTH", "L1 launch authorization is not proven")
    if launch.get("indexing_authorized") is not True:
        fail("L1-INDEX", "informational indexing is not authorized")
    if launch.get("commerce_authorized") is not False:
        fail("L1-COMMERCE", "commerce must be false in L1")
    if launch.get("public_price_authorized") is not False:
        fail("L1-PRICE", "public price must be false in L1")
    if launch.get("payment_instructions_authorized") is not False:
        fail("L1-PAYMENT", "payment instructions must be false in L1")

    if pricing.get("public_price_authorized") is not False or pricing.get("active_prices"):
        fail("L1-PRICE-REGISTRY", "pricing registry is not fail-closed")
    if payment.get("destinations") or payment.get("destinations_status") == "VERIFIED":
        fail("L1-PAYMENT-REGISTRY", "payment registry unexpectedly contains active destinations")
    if contact.get("whatsapp", {}).get("value") is not None:
        fail("L1-CONTACT", "unverified WhatsApp value is present")
    if legal.get("legal_operator", {}).get("name") is not None:
        fail("L1-LEGAL", "unverified legal operator is present")

    if not PUBLIC.is_dir():
        fail("L1-BUILD", "_public_v3 does not exist")
    else:
        manifest = PUBLIC / "BUILD-MANIFEST.txt"
        if not manifest.is_file():
            fail("L1-MANIFEST", "BUILD-MANIFEST.txt is missing")
        else:
            text = manifest.read_text(encoding="utf-8", errors="replace")
            for line in (
                "release_mode=L1_PUBLIC_INFO_ONLY",
                "public_prices=0",
                "commerce_controls=0",
                "payment_destinations=0",
                "whatsapp_destinations=0",
            ):
                if line not in text:
                    fail("L1-MANIFEST", f"missing {line}")

        forbidden_paths = [
            "catalog.json", "aips-live.json", "assets/catalog.js", "checkout.html",
            "track.html", "order.html", "orders.html", "commerce-worker", "docs",
            "_preview_v3",
        ]
        for rel in forbidden_paths:
            if (PUBLIC / rel).exists():
                fail("L1-PATH", f"forbidden path present: {rel}")

        combined = []
        for path in PUBLIC.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".ico", ".woff", ".woff2"}:
                continue
            combined.append(path.read_text(encoding="utf-8", errors="replace"))
        text = "\n".join(combined)
        forbidden = {
            "selling price": r"৳\s*[0-9]|\b(?:BDT|Tk\.?)\s*[0-9][0-9,]*",
            "stale WhatsApp": r"(?:\+?880[ -]?1305[ -]?869242|8801305869242|01305869242|wa\.me/)",
            "commerce control": r"cartAdd\s*\(|checkout\.html|class=[\"'][^\"']*cartbtn",
            "offer schema": r"[\"']@type[\"']\s*:\s*[\"'](?:Offer|AggregateOffer)[\"']",
            "payment destination": r"merchant number|send money to|payment number|bank account number",
            "raw catalog": r"catalog\.json|assets/catalog\.js",
        }
        for name, pattern in forbidden.items():
            if re.search(pattern, text, re.I):
                fail("L1-CONTENT", f"forbidden {name} present in public artifact")

    if errors:
        print(f"L1 RELEASE BLOCKED: {len(errors)} failure(s)")
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print(json.dumps({
        "release_gate": "PASS",
        "release_mode": "L1_PUBLIC_INFO_ONLY",
        "commerce": False,
        "public_prices": False,
        "payment_instructions": False,
        "whatsapp_destination": None,
        "legal_operator": None,
        "indexing": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
