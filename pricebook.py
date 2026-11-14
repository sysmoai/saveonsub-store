#!/usr/bin/env python3
"""Effective pricebook: the CEO pricebook minus plans on commercial HOLD.

The pricebook (ops/PRICING-V2-2026-09-17.json) is the approved price list and is
never edited here. Plans named in ops/HELD-PLANS-2026-11-14.json are removed in
memory for every build step and audit that decides what may be sold, shown,
priced in JSON-LD or put in a cart. They are kept in rule["held_plans"] so the
product page can say plainly that the plan is not taking new orders.

A held file next to the pricebook is optional: temp copies used by tests have none.
"""
from __future__ import annotations

import json
from pathlib import Path

HELD_FILE = "HELD-PLANS-2026-11-14.json"


def load_policy(path: Path) -> dict:
    path = Path(path)
    policy = json.loads(path.read_text(encoding="utf-8"))
    held_path = path.parent / HELD_FILE
    if not held_path.is_file():
        return policy
    held = json.loads(held_path.read_text(encoding="utf-8")).get("held_plans") or {}
    book = policy.get("approved_products") or {}
    for pid, plan_ids in held.items():
        rule = book.get(pid)
        if not rule:
            raise SystemExit(f"[pricebook] held plan names unknown product: {pid}")
        known = {p["plan_id"]: p for p in rule.get("plans") or []}
        missing = [i for i in plan_ids if i not in known]
        if missing:
            raise SystemExit(f"[pricebook] held plan id not in pricebook for {pid}: {missing}")
        rule["held_plans"] = [
            {"plan_id": i, "label": known[i]["label"], "access_type": known[i].get("access_type", "personal")}
            for i in plan_ids
        ]
        rule["plans"] = [p for p in rule["plans"] if p["plan_id"] not in plan_ids]
        if not rule["plans"]:
            rule["mode"] = "inquiry"
            rule["note"] = ("Price on Request — no plan is currently taking new orders. Confirm the exact provider "
                            "tier, access method and availability with SaveOnSub support; no fixed price is published.")
    return policy
