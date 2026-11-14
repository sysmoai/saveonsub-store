#!/usr/bin/env python3
"""Deterministic pricebook -> public artifact reconciliation (post-build step).

Walks the CEO pricebook (ops/PRICING-V2-*.json) and proves that every layer of
the staged artifact agrees with it, product by product and plan by plan:

  pricebook -> catalog.json ids -> _site/assets/catalog.js plans
            -> EN/BN product page prices -> WhatsApp prefills
            -> canonical / hreflang / sitemap coverage

Any mismatch fails the build. It also writes a public-safe coverage ledger,
ops/seo/control/product-coverage.json, so later sessions can read one file
instead of re-auditing the catalog. The ledger records statuses only; no
supplier, cost or customer data ever goes into this public repository.

Price approval is not provider-rights evidence: every plan carries a separate
provider_terms_status, and shared-access plans stay flagged for review here
rather than being silently dropped or relabelled.

`--check` verifies without rewriting the ledger.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

from apply_pricing_v2 import DURATION_UNITS
from site_config import SUPPORT_PHONE_DIGITS
from pricebook import load_policy

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
CATALOG = ROOT / "catalog.json"
LEDGER = ROOT / "ops" / "seo" / "control" / "product-coverage.json"
BASE = "https://saveonsub.com"

PRICE = re.compile(r"৳\s?([\d,]+)")
WA_LINK = re.compile(r"https://wa\.me/(\d+)(?:\?text=([^\"'\s<>]+))?")
CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"')
HREFLANG = re.compile(r'hreflang="([^"]+)" href="([^"]+)"')
# Pricebook-only ids that name an existing catalog product (same provider and
# official URL). They never had a page (live /p/<alias> returns 404), so they
# stay inquiry-only and resolve to the canonical product instead of a new page.
ALIASES = {"kling-ai": "kling", "pika-labs": "pika", "gamma-pro": "gamma",
           "mistral": "mistral-pro", "replit": "replit-core"}
JS_CATALOG = re.compile(r"const CATALOG = (\{.*?\});\s*$", re.S | re.M)


def bdt_values(text: str) -> set[int]:
    return {int(m.replace(",", "")) for m in PRICE.findall(text)}


def wa_prefills(text: str) -> list[tuple[str, str]]:
    out = []
    for number, query in WA_LINK.findall(html.unescape(text)):
        out.append((number, urllib.parse.unquote(query) if query else ""))
    return out


def load_js_catalog(path: Path) -> dict[str, dict]:
    match = JS_CATALOG.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path}: CATALOG literal not found")
    return {p["id"]: p for p in json.loads(match.group(1))["products"]}


def plan_status(plan: dict) -> str:
    # CEO approval covers the price, not provider permission to resell access.
    if plan.get("access_type") == "shared":
        return "CONFLICTED_PROVIDER_TERMS_REVIEW"
    if plan.get("access_type") == "official":
        return "UNKNOWN_VERIFY_PROVIDER_CHECKOUT"
    return "UNKNOWN_VERIFY_ACTIVATION_METHOD"


def normalised(plan: dict) -> tuple:
    duration, unit = DURATION_UNITS.get(str(plan.get("duration", "1 month")).strip().lower(), (None, None))
    return (plan["label"], int(plan["bdt"]), plan.get("access_type", "personal"), duration, unit)


def check_page(pid: str, locale: str, page: Path, approved: set[int],
               non_monthly: set[int], sitemap: str, errors: list[str]) -> dict:
    prefix = "/bn/p/" if locale == "bn" else "/p/"
    url = f"{BASE}{prefix}{pid}"
    if not page.exists():
        errors.append(f"{pid}[{locale}]: page missing ({page.relative_to(SITE)})")
        return {"url": url, "status": "MISSING"}
    text = page.read_text(encoding="utf-8")
    shown = bdt_values(text)
    if shown - approved:
        errors.append(f"{pid}[{locale}]: unapproved price(s) on page {sorted(shown - approved)}")
    if approved - shown:
        errors.append(f"{pid}[{locale}]: approved price(s) not shown {sorted(approved - shown)}")
    for bdt in sorted(non_monthly):
        if re.search(rf"৳{bdt:,}\s*/\s*(?:month|মাস)", text):
            errors.append(f"{pid}[{locale}]: ৳{bdt:,} is a 6-month/yearly price but is labelled per month")
    for number, query in wa_prefills(text):
        if number != SUPPORT_PHONE_DIGITS:
            errors.append(f"{pid}[{locale}]: WhatsApp link to non-canonical number {number}")
        quoted = bdt_values(query)
        if quoted - approved:
            errors.append(f"{pid}[{locale}]: WhatsApp prefill quotes unapproved {sorted(quoted - approved)}")
    canon = CANONICAL.findall(text)
    if canon != [url]:
        errors.append(f"{pid}[{locale}]: canonical {canon} != [{url}]")
    langs = dict(HREFLANG.findall(text))
    if langs.get("en-bd") != f"{BASE}/p/{pid}" or langs.get("bn-bd") != f"{BASE}/bn/p/{pid}":
        errors.append(f"{pid}[{locale}]: EN/BN hreflang pair incomplete")
    in_sitemap = f"<loc>{url}</loc>" in sitemap
    if not in_sitemap:
        errors.append(f"{pid}[{locale}]: missing from sitemap.xml")
    return {"url": url, "status": "OK", "prices_shown": sorted(shown), "in_sitemap": in_sitemap}


def reconcile(policy: dict, catalog: dict, site: Path) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    book = policy.get("approved_products") or {}
    products = {p["id"]: p for p in catalog.get("products", [])}
    js = load_js_catalog(site / "assets" / "catalog.js")
    sitemap = (site / "sitemap.xml").read_text(encoding="utf-8")
    records = []

    for pid in sorted(set(products) - set(book)):
        errors.append(f"{pid}: catalog product has no pricebook decision")

    for pid in sorted(book):
        rule = book[pid]
        mode = rule.get("mode")
        plans = rule.get("plans") or []
        record = {
            "product_id": pid,
            "name": (products.get(pid) or {}).get("name"),
            "category": (products.get(pid) or {}).get("category"),
            "pricebook_mode": mode,
            "ceo_approval_source": "pricebook commercial_hold.authority" if mode == "fixed" else None,
            "plans": [],
            "pages": {},
        }
        if pid.startswith("aips-") and mode != "inquiry":
            errors.append(f"{pid}: other business unit's package must stay inquiry-only")
        if pid not in products:
            if mode == "fixed":
                errors.append(f"{pid}: fixed price approved but no catalog product/page")
            target = ALIASES.get(pid)
            if target is not None and target not in products:
                errors.append(f"{pid}: alias target {target} is not a catalog product")
            record["route_decision"] = f"ALIAS_OF:{target}" if target else "HELD_NO_PAGE"
            records.append(record)
            continue

        approved = {int(p["bdt"]) for p in plans} if mode == "fixed" else set()
        if mode == "fixed" and not plans:
            errors.append(f"{pid}: fixed mode without plans")
        if mode not in ("fixed", "inquiry"):
            errors.append(f"{pid}: unknown pricebook mode {mode!r}")

        labels = [p.get("label") for p in plans]
        if len(labels) != len(set(labels)):
            errors.append(f"{pid}: duplicate plan labels")
        for plan in plans:
            if normalised(plan)[3] is None:
                errors.append(f"{pid}: unknown duration {plan.get('duration')!r} ({plan.get('label')})")
            record["plans"].append({
                "label": plan.get("label"),
                "bdt": plan.get("bdt"),
                "duration": plan.get("duration"),
                "access_type": plan.get("access_type"),
                "provider_terms_status": plan_status(plan),
            })

        js_plans = [(p["label"], int(p["bdt"]), p.get("type"), p.get("duration"), p.get("billing_unit"))
                    for p in (js.get(pid) or {}).get("plans", [])]
        want = [normalised(p) for p in plans] if mode == "fixed" else []
        non_monthly = {w[1] for w in want if w[4] != "month"} - {w[1] for w in want if w[4] == "month"}
        if pid not in js:
            errors.append(f"{pid}: missing from public catalog.js")
        elif js_plans != want:
            errors.append(f"{pid}: catalog.js plans {js_plans} != pricebook {want}")

        en = site / "p" / f"{pid}.html"
        bn = site / "bn" / "p" / f"{pid}.html"
        record["pages"]["en"] = check_page(pid, "en", en, approved, non_monthly, sitemap, errors)
        record["pages"]["bn"] = check_page(pid, "bn", bn, approved, non_monthly, sitemap, errors)
        record["route_decision"] = "PRICED_PAGE" if mode == "fixed" else "INQUIRY_PAGE"
        records.append(record)

    fixed = [r for r in records if r["pricebook_mode"] == "fixed"]
    summary = {
        "pricebook_revision": policy.get("revision"),
        "pricebook_entries": len(book),
        "catalog_products": len(products),
        "fixed_products": len(fixed),
        "inquiry_entries": len(records) - len(fixed),
        "approved_plans": sum(len(r["plans"]) for r in fixed),
        "held_without_page": sorted(r["product_id"] for r in records if r["route_decision"] == "HELD_NO_PAGE"),
        "aliases": {r["product_id"]: r["route_decision"].split(":", 1)[1]
                    for r in records if r["route_decision"].startswith("ALIAS_OF:")},
        "plans_by_provider_terms_status": {},
        "errors": len(errors),
        "warnings": len(warnings),
    }
    for r in fixed:
        for p in r["plans"]:
            key = p["provider_terms_status"]
            summary["plans_by_provider_terms_status"][key] = summary["plans_by_provider_terms_status"].get(key, 0) + 1
    return errors, warnings, {"summary": summary, "warnings": warnings, "products": records}


def main(argv: list[str]) -> int:
    policy = load_policy(POLICY)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    errors, warnings, ledger = reconcile(policy, catalog, SITE)
    for w in warnings:
        print("[reconcile] WARN " + w)
    for e in errors[:40]:
        print("[reconcile] FAIL " + e)
    s = ledger["summary"]
    if errors:
        print(f"[reconcile] BLOCKED — {len(errors)} mismatch(es) between pricebook and staged artifact")
        return 1
    if "--check" not in argv:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[reconcile] PASS — {s['pricebook_entries']} pricebook entries, {s['fixed_products']} priced "
          f"products / {s['approved_plans']} plans, {s['inquiry_entries']} inquiry, "
          f"aliases: {len(s['aliases'])}, held without page: {', '.join(s['held_without_page']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
