#!/usr/bin/env python3
"""Fail-closed structural audit for SaveOnSub Order OS."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
errors=[]

policy=json.loads((ROOT/"ops/PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
seen=set()
sellable=0
for product_id, product in policy["approved_products"].items():
    plans=product.get("plans") or []
    if product.get("mode")=="inquiry":
        continue
    for plan in plans:
        sellable+=1
        pid=plan.get("plan_id")
        if not pid:
            errors.append(f"{product_id}: missing plan_id")
            continue
        key=(product_id,pid)
        if key in seen:
            errors.append(f"duplicate governed plan key: {product_id}:{pid}")
        seen.add(key)
        if not isinstance(plan.get("bdt"),int) or plan["bdt"]<=0:
            errors.append(f"{product_id}:{pid}: invalid BDT price")
        if plan.get("access_type") not in {"personal","team"}:
            errors.append(f"{product_id}:{pid}: unsupported access_type")

required=[
    "functions/api/orders/index.ts",
    "functions/api/orders/track.ts",
    "functions/api/ops/orders/index.ts",
    "functions/lib/order-os/access-auth.ts",
    "functions/lib/order-os/ops-auth.ts",
    "ops/order-os/schema.sql",
    "workers/order-notifications/src/index.ts",
    "assets/order-config.js",
    "assets/order-v2.js",
    "ops/index.html",
    "functions/lib/order-os/order-workflow.ts",
    "functions/lib/order-os/redaction.ts",
    "functions/lib/order-os/http.ts",
    "functions/api/ops/orders/[orderId]/payment-verification.ts",
    "functions/api/ops/orders/[orderId]/reversal.ts",
    "tests/order-os/auth.test.mjs",
    "tests/order-os/workflow.test.mjs",
    "tests/order-os/redaction.test.mjs",
]
for rel in required:
    if not (ROOT/rel).exists():
        errors.append(f"missing required Order OS file: {rel}")

config=(ROOT/"assets/order-config.js").read_text(encoding="utf-8")
if "serverCheckoutEnabled: false" not in config:
    errors.append("public server checkout must remain default-off until production bindings are approved")
if "turnstileSiteKey: """ not in config:
    errors.append("branch config must not contain a production Turnstile site key")

api=(ROOT/"functions/api/orders/index.ts").read_text(encoding="utf-8")
for needle in ["TURNSTILE_SECRET_KEY","idempotency_key","resolveGovernedPlan","notification_outbox","trackingToken"]:
    if needle not in api:
        errors.append(f"order API missing guard/feature: {needle}")

auth=(ROOT/"functions/lib/order-os/access-auth.ts").read_text(encoding="utf-8")
for needle in ["cf-access-jwt-assertion","RS256","POLICY_AUD","cdn-cgi/access/certs","crypto.subtle.verify"]:
    if needle not in auth:
        errors.append(f"staff origin auth missing: {needle}")

# Security controls that must not be silently removed (behaviour is proven by tests/order-os).
schema=(ROOT/"ops/order-os/schema.sql").read_text(encoding="utf-8")
for needle in ["payment_verifications","order_reversals","trg_orders_terminal_immutable",
               "trg_orders_paid_states_need_verification","trg_orders_insert_unpaid_only",
               "trg_order_events_no_update","ux_payment_ref_active"]:
    if needle not in schema:
        errors.append(f"schema missing security control: {needle}")

ops_dir=ROOT/"functions/api/ops/orders"
for path in ops_dir.rglob("*.ts"):
    src=path.read_text(encoding="utf-8")
    rel=path.relative_to(ROOT).as_posix()
    if "String(e)" in src:
        errors.append(f"{rel}: echoes raw exception text to the client")
    if "requireOperator" not in src:
        errors.append(f"{rel}: staff endpoint without requireOperator")
status_src=(ops_dir/"[orderId]/status.ts").read_text(encoding="utf-8")
if "decideTransition" not in status_src:
    errors.append("status endpoint must use decideTransition (server-enforced state machine)")
if "status=?" not in status_src:
    errors.append("status endpoint must update with a compare-and-set guard on the current status")
if "payment_confirmed_at" in status_src:
    errors.append("status endpoint must not set payment_confirmed_at (payment verification endpoint only)")

checkout=(ROOT/"checkout.html").read_text(encoding="utf-8")
for needle in ['assets/order-config.js','assets/order-v2.js']:
    if needle not in checkout:
        errors.append(f"checkout missing {needle}")

commercial=(ROOT/"commercial_truth_v2.py").read_text(encoding="utf-8")
if 'plan.get("plan_id")' not in commercial:
    errors.append("final commercial projection does not propagate governed plan_id")

if errors:
    print("ORDER OS AUDIT FAILED")
    for e in errors:
        print(" -",e)
    raise SystemExit(1)

print(f"Order OS audit OK — {sellable} governed sellable plans with unique stable IDs.")
