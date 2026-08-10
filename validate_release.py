#!/usr/bin/env python3
"""Fail-closed integrity gate for the deployable SAVEONSUB release artifact.

Historical July commerce HTML/catalog data remains in the repository solely as
migration evidence. This gate does not pretend that evidence is current truth;
it proves that no legacy commerce path can enter the staged release and that the
actual `_site` artifact obeys the current launch/authority state.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
LAUNCH = ROOT / "docs" / "control" / "launch_state.json"
CATALOG = ROOT / "catalog.json"
TERMS = ROOT / "terms.html"
DEPLOY = ROOT / ".github" / "workflows" / "deploy.yml"
VERCEL = ROOT / "vercel.json"
BUILD_ALL = ROOT / "build_all.sh"

errors: list[tuple[str, str]] = []
warnings: list[tuple[str, str]] = []


def fail(code: str, message: str) -> None:
    errors.append((code, message))


def warn(code: str, message: str) -> None:
    warnings.append((code, message))


def text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


launch = json.loads(text(LAUNCH) or "{}")
state = launch.get("state")
commerce_authorized = launch.get("commerce_authorized") is True
public_price_authorized = launch.get("public_price_authorized") is True
payment_authorized = launch.get("payment_instructions_authorized") is True

if state not in {"L0_BOOTSTRAP_PRIVATE", "L1_PUBLIC_INFO_ONLY", "L2_LIMITED_COMMERCE", "L3_FULL_APPROVED_COMMERCE"}:
    fail("P0-LAUNCH-STATE-INVALID", f"unrecognized launch state: {state!r}")

# Every automated/public build path must use the strict artifact, never repo root.
deploy_text = text(DEPLOY)
vercel_text = text(VERCEL)
build_text = text(BUILD_ALL)
required_deploy = ("build_public_info_v3.py", "harden_public_info_v3.py", "stage_deploy.py --public-v3", "output")
for token in required_deploy[:3]:
    if token not in deploy_text:
        fail("P0-DEPLOY-PATH-UNSAFE", f"Cloudflare deploy workflow missing strict token: {token}")
if "wrangler pages deploy _site" not in deploy_text:
    fail("P0-DEPLOY-PATH-UNSAFE", "Cloudflare deploy workflow does not deploy staged _site")
if re.search(r"wrangler\s+pages\s+deploy\s+\.\s", deploy_text):
    fail("P0-DEPLOY-PATH-UNSAFE", "Cloudflare deploy workflow can deploy repository root")

for token in ("build_public_info_v3.py", "harden_public_info_v3.py", "stage_deploy.py --public-v3", '"outputDirectory": "_site"'):
    if token not in vercel_text:
        fail("P0-VERCEL-PREVIEW-UNSAFE", f"Vercel configuration missing strict token: {token}")
if '"outputDirectory": "."' in vercel_text:
    fail("P0-VERCEL-PREVIEW-UNSAFE", "Vercel can publish repository root")

for token in ("build_public_info_v3.py", "harden_public_info_v3.py", "stage_deploy.py --public-v3"):
    if token not in build_text:
        fail("P0-DEFAULT-BUILD-UNSAFE", f"default build missing strict token: {token}")
if any(token in build_text for token in ("build_pages.py", "build_trust.py", "build_catalog.py")):
    fail("P0-DEFAULT-BUILD-UNSAFE", "default build still invokes historical commerce generators")

if not SITE.is_dir():
    fail("P0-RELEASE-ARTIFACT-MISSING", "_site is missing; build/stage the strict L1 artifact before this gate")
else:
    files = [p for p in SITE.rglob("*") if p.is_file()]
    json_files = [p for p in files if p.suffix.lower() == ".json"]
    if json_files:
        fail("P0-PUBLIC-JSON-LEAK", f"staged artifact contains JSON: {[p.relative_to(SITE).as_posix() for p in json_files[:10]]}")

    forbidden_paths = ("checkout.html", "track.html", "catalog.json", "aips-live.json", "assets/catalog.js")
    for rel in forbidden_paths:
        if (SITE / rel).exists():
            fail("P0-LEGACY-PATH-LEAK", f"staged artifact contains forbidden legacy path: {rel}")

    commerce_hits: list[str] = []
    price_hits: list[str] = []
    payment_hits: list[str] = []
    sharing_hits: list[str] = []
    for path in files:
        if path.suffix.lower() not in {".html", ".js", ".txt", ".xml"}:
            continue
        content = text(path)
        lower = content.lower()
        rel = path.relative_to(SITE).as_posix()
        if "cartadd(" in lower or '"@type": "offer"' in lower or '"@type":"offer"' in lower or "aggregateoffer" in lower:
            commerce_hits.append(rel)
        if re.search(r"৳\s*[0-9]", content):
            price_hits.append(rel)
        if re.search(r"\b(?:bkash|nagad|rocket)\b|\+?8801\d{9}|wa\.me/|api\.whatsapp\.com", content, re.I):
            payment_hits.append(rel)
        if re.search(r"shared\s+(?:seat|account|plan)|provider\s+tos\s+prohibit|terms of service.*shared", content, re.I):
            sharing_hits.append(rel)

    if state in {"L0_BOOTSTRAP_PRIVATE", "L1_PUBLIC_INFO_ONLY"} and commerce_hits:
        fail("P0-LAUNCH-COMMERCE-BLOCK", f"strict artifact contains commerce while state={state}: {commerce_hits[:10]}")
    if not commerce_authorized and commerce_hits:
        fail("P0-COMMERCE-AUTHORITY-MISSING", f"strict artifact exposes commerce without authority: {commerce_hits[:10]}")
    if not public_price_authorized and price_hits:
        fail("P0-PUBLIC-PRICE-AUTHORITY-MISSING", f"strict artifact exposes BDT prices without authority: {price_hits[:10]}")
    if not payment_authorized and payment_hits:
        fail("P0-PAYMENT-AUTHORITY-MISSING", f"strict artifact exposes payment/contact destinations without authority: {payment_hits[:10]}")
    if sharing_hits:
        fail("P0-PROHIBITED-SHARING-PUBLIC", f"strict artifact still describes prohibited shared commerce: {sharing_hits[:10]}")

    manifest = text(SITE / "BUILD-MANIFEST.txt")
    for token in (
        "release_mode=L1_PUBLIC_INFO_ONLY",
        "public_prices=0",
        "commerce_controls=0",
        "payment_destinations=0",
        "whatsapp_destinations=0",
    ):
        if token not in manifest:
            fail("P0-BUILD-MANIFEST-MISMATCH", f"strict build manifest missing: {token}")

# Historical evidence is inventoried, but does not block if all publication paths
# above are proven strict. These warnings keep migration debt visible.
raw = json.loads(text(CATALOG) or "{}")
legacy_aips = [s for s in raw.get("meta", {}).get("price_precedence", []) if re.search(r"(^|[-_])aips($|[-_])", str(s), re.I)]
if legacy_aips:
    warn("LEGACY-AIPS-PRICE-EVIDENCE", f"historical catalog retains {len(legacy_aips)} AIPS precedence entry for provenance")

legacy_shared = 0
legacy_proof = 0
for product in raw.get("products", []):
    identity = f"{product.get('id','')} {product.get('name','')}".lower()
    is_openai = "chatgpt" in identity or "openai" in identity
    for plan in product.get("plans", []):
        looks_shared = (
            str(plan.get("type") or "").lower() == "shared"
            or str(plan.get("tos") or "").lower().startswith("shared")
            or "shared" in str(plan.get("label") or "").lower()
        )
        if is_openai and looks_shared:
            legacy_shared += 1
    if product.get("orders") not in (None, 0) or product.get("bestseller_rank") not in (None, 0):
        legacy_proof += 1
if legacy_shared:
    warn("LEGACY-OPENAI-SHARED-EVIDENCE", f"historical catalog retains {legacy_shared} prohibited shared plan record(s), quarantined from active v3 model")
if legacy_proof:
    warn("LEGACY-UNVERIFIED-PROOF-EVIDENCE", f"historical catalog retains proof fields on {legacy_proof} product(s), quarantined from active v3 model")

legacy_terms = text(TERMS)
if re.search(r"shared seats violate most providers.? terms of service", legacy_terms, re.I):
    warn("LEGACY-TERMS-EVIDENCE", "historical terms.html contains obsolete sharing language but is not a release source")

legacy_pages = 0
for path in list((ROOT / "p").glob("*.html")) + list((ROOT / "bn" / "p").glob("*.html")):
    content = text(path)
    if "cartAdd(" in content or re.search(r"৳\s*[0-9]", content):
        legacy_pages += 1
if legacy_pages:
    warn("LEGACY-GENERATED-COMMERCE-EVIDENCE", f"{legacy_pages} historical product HTML file(s) remain in repo but are excluded from all strict publication paths")

for code, message in warnings:
    print(f"WARN {code}: {message}")

if errors:
    print(f"RELEASE BLOCKED: {len(errors)} integrity failure(s)")
    for code, message in errors:
        print(f"FAIL {code}: {message}")
    sys.exit(1)

print("release integrity gate passed for staged strict artifact")
print(f"legacy quarantine warnings: {len(warnings)}")
