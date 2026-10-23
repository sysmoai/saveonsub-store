#!/usr/bin/env python3
"""Fail-closed commercial policy audit: catalog.json vs the pricing policy.

  * EXEC-010 locked decisions hold regardless of any later agent-recorded note:
    Google AI Pro is Price on Request (D1) and ChatGPT Plus is HOLD (D2) —
    neither may carry a plan, a price or a cart path.
  * While the policy's commercial_hold is active, every product is
    request_price with no plans and every policy rule is inquiry-only.
  * Outside HOLD, request_price is allowed only for products the policy scopes
    as inquiry (or the fail-closed AI/bundle categories); every fixed price must
    come from an explicit policy rule.
  * No cost / margin / supplier-cost field exists in the catalog or policy.

Usage: python3 audit_policy.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
CATALOG_PATH = ROOT / "catalog.json"

LOCKED_NO_SALE = {"google-ai-pro": "EXEC-010 D1 Price on Request", "chatgpt-plus": "EXEC-010 D2 HOLD"}
COST_KEY = re.compile(r"cost|margin|contribution|profit|supplier", re.I)


def cost_keys(value, path="") -> list[str]:
    out = []
    if isinstance(value, dict):
        for k, v in value.items():
            here = f"{path}.{k}" if path else k
            if COST_KEY.search(k):
                out.append(here)
            out += cost_keys(v, here)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out += cost_keys(v, f"{path}[{i}]")
    return out


def audit(catalog: dict, policy: dict) -> list[str]:
    issues: list[str] = []
    rules = policy.get("approved_products", {})
    hold = (policy.get("commercial_hold") or {}).get("status") == "HOLD"
    ai_categories = set(policy.get("ai_categories", []))
    products = {p.get("id"): p for p in catalog.get("products", [])}

    for pid, why in LOCKED_NO_SALE.items():
        product = products.get(pid)
        if product is None:
            issues.append(f"{pid}: missing from catalog ({why} must stay visible as no-sale)")
            continue
        if not product.get("request_price") or product.get("plans"):
            issues.append(f"{pid}: has a price/plan but is locked by {why}")
        rule = rules.get(pid, {})
        if rule.get("plans") or rule.get("mode") != "inquiry":
            issues.append(f"{pid}: policy rule publishes a price but is locked by {why}")

    for pid, product in products.items():
        plans = product.get("plans") or []
        rule = rules.get(pid)
        if hold:
            if not product.get("request_price") or plans:
                issues.append(f"{pid}: not Price on Request during EXEC-010 HOLD")
            continue
        if product.get("request_price"):
            category = str(product.get("category", ""))
            scoped = (rule and rule.get("mode") == "inquiry") or category in ai_categories \
                or category == "bundles" or str(pid).startswith(("bundle-", "aips-"))
            if not scoped:
                issues.append(f"{pid}: request_price outside the scoped inquiry allowlist")
            if plans:
                issues.append(f"{pid}: request_price product still carries plans")
        elif plans and not (rule and rule.get("plans")):
            issues.append(f"{pid}: fixed price without an explicit policy rule")

    if hold:
        for pid, rule in rules.items():
            if rule.get("mode") != "inquiry" or rule.get("plans"):
                issues.append(f"policy {pid}: fixed price rule during EXEC-010 HOLD")

    issues += [f"policy: cost/margin field {k}" for k in cost_keys(policy)]
    issues += [f"catalog: cost/margin field {k}" for k in cost_keys(catalog)]
    return issues


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    issues = audit(catalog, policy)
    if issues:
        print(f"[policy-audit] FAIL — {len(issues)} issue(s):")
        for x in issues[:60]:
            print("  " + x)
        return 1
    print("[policy-audit] PASS — EXEC-010 locks, request_price scope and cost/margin exclusion verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
