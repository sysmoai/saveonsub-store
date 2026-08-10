#!/usr/bin/env python3
"""Static safety validator for SAVEONSUB shadow commerce Worker.

This check verifies that the additive backend remains non-production, contains no
customer/payment authority data, and that the generated runtime seed cannot
silently enable commerce or copy legacy catalog prices into D1.
"""
from __future__ import annotations

import pathlib
import re

from catalog_model import load_catalog

ROOT = pathlib.Path(__file__).resolve().parent
WORKER = ROOT / "commerce-worker"
CONFIG = WORKER / "wrangler.toml"
SOURCE = WORKER / "src" / "index.js"
MIGRATIONS = [
    WORKER / "migrations" / "0001_shadow_runtime.sql",
    WORKER / "migrations" / "0002_observability_media_drafts.sql",
]
SEED = WORKER / "generated" / "plan_runtime_seed.sql"

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def strip_sql_comments(text: str) -> str:
    return re.sub(r"--[^\n]*", "", text)


def main() -> int:
    for path in (CONFIG, SOURCE, SEED, *MIGRATIONS):
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        for message in errors:
            print(f"FAIL {message}")
        return 1

    config = CONFIG.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    migration = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS)
    seed = SEED.read_text(encoding="utf-8")

    required_config = (
        'name = "saveonsub-commerce-shadow"',
        'workers_dev = true',
        'COMMERCE_MODE = "shadow"',
        'ENVIRONMENT = "shadow"',
    )
    for token in required_config:
        if token not in config:
            fail(f"wrangler config missing fail-closed token: {token}")
    active_config = "\n".join(line for line in config.splitlines() if not line.lstrip().startswith("#"))
    if re.search(r"(?m)^\s*(route|routes|custom_domain)\s*=", active_config):
        fail("shadow Worker config contains a production/custom route")
    if re.search(r"(?m)^\s*\[\[d1_databases\]\]", active_config):
        fail("D1 binding exists before reviewed provisioning step")

    required_source = (
        "ORDER_CREATION_DISABLED",
        "ORDER_TRACKING_DISABLED",
        "ADMIN_DISABLED",
        "SHADOW_DATABASE_NOT_BOUND",
        "PLAN_NOT_SELLABLE",
        "PRICE_NOT_AUTHORIZED",
        "order_creation_enabled: false",
        "x-request-id",
        "request_complete",
        "quote_audit",
    )
    for token in required_source:
        if token not in source:
            fail(f"Worker source missing fail-closed/observability behavior: {token}")
    if re.search(r"(?:bkash|nagad|rocket|payment[_ -]?(?:number|account|destination))", source, re.I):
        fail("Worker source contains payment-destination language")
    if re.search(r"(?:8801\d{9}|\+8801\d{9})", source):
        fail("Worker source contains a Bangladesh mobile number")

    if re.search(r"item\?\.(?:price|price_bdt|amount|total)", source):
        fail("Worker reads a browser-supplied price/amount field")
    if "runtime.price_bdt" not in source:
        fail("Worker does not derive quote price from runtime DB")

    sql = strip_sql_comments(migration).lower()
    forbidden_tables = (
        "create table customers",
        "create table customer_identities",
        "create table orders",
        "create table order_items",
        "create table payment_attempts",
        "create table payment_destinations",
        "create table fulfillment_events",
    )
    for token in forbidden_tables:
        if token in sql:
            fail(f"shadow migration unexpectedly creates protected table: {token}")
    for pii_column in ("email", "phone", "address", "customer_name", "payment_number", "account_number"):
        if re.search(rf"\b{re.escape(pii_column)}\b", sql):
            fail(f"shadow migration contains protected/PII column: {pii_column}")

    for required_table in ("quote_audit", "operational_events", "media_drafts", "admin_audit_events"):
        if not re.search(rf"create table if not exists\s+{required_table}\b", sql):
            fail(f"shadow observability/media schema missing table: {required_table}")

    catalog = load_catalog()
    expected_plans = sum(len(p.get("plans", [])) for p in catalog.get("products", []))
    seed_rows = len(re.findall(r"(?m)^INSERT INTO plan_runtime\(", seed))
    if seed_rows != expected_plans:
        fail(f"seed row count mismatch: expected {expected_plans}, found {seed_rows}")

    if seed.count("'unknown', NULL, 'BDT'") != expected_plans:
        fail("not every plan seed is commercial_state=unknown with NULL price")
    if re.search(r"'allowed'\s*,", seed):
        fail("seed contains an allowed commercial state")
    for line in seed.splitlines():
        if "'unknown'," in line and re.search(r"'unknown'\s*,\s*[0-9]", line):
            fail("seed contains a numeric price value")
            break

    source_sha = catalog.get("meta", {}).get("v3_model", {}).get("source_sha256")
    if source_sha and source_sha not in seed:
        fail("seed does not carry normalized catalog source provenance")

    if errors:
        print(f"SHADOW COMMERCE INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    print("shadow commerce static validation passed")
    print(f"plans represented: {expected_plans}")
    print("commercial seed: 100% unknown")
    print("price seed: 100% NULL")
    print("order/payment/customer persistence: disabled")
    print("observability/media drafts: schema-only, non-public")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
