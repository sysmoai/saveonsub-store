import { test, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { makeWorld, restoreFetch, OPERATORS } from "./harness.mjs";
afterEach(restoreFetch);
const file = "api/ops/business.ts";
async function world() {
  const w = await makeWorld();
  w.db.db.exec(
    readFileSync(
      new URL("../../ops/order-os/business-schema.sql", import.meta.url),
      "utf8",
    ),
  );
  return w;
}
const get = (w, who = "owner", query = "") =>
  w.call(file, "onRequestGet", who, { method: "GET", query });
const post = (w, who, body, options = {}) =>
  w.call(file, "onRequestPost", who, { body, ...options });
test("fails closed for missing JWT, invalid month, missing schema and foreign origin", async () => {
  const w = await world();
  assert.equal((await get(w, null)).status, 401);
  assert.equal((await get(w, "owner", "?month=2026-13")).status, 400);
  assert.equal(
    (
      await post(
        w,
        "owner",
        { action: "create" },
        { headers: { origin: "https://foreign.test" } },
      )
    ).status,
    403,
  );
  w.db.db.exec("DROP TABLE business_audit");
  assert.equal((await get(w)).status, 503);
});
test("lead persists, owner sees CRM, unrelated support/viewer cannot read contacts or finance", async () => {
  const w = await world();
  const r = await post(w, "support", {
    action: "create",
    kind: "lead",
    title: "Synthetic lead",
    details: "Private contact example.test",
  });
  assert.equal(r.status, 201);
  assert.equal((await get(w, "owner")).body.records.length, 1);
  assert.equal(
    (await get(w, "support")).body.records[0].details,
    "Private contact example.test",
  );
  const v = (await get(w, "viewer")).body;
  assert.equal(v.records.length, 0);
  assert.equal(v.finance, undefined);
  assert.equal(v.audit, undefined);
  assert.equal(
    (
      await post(w, "viewer", {
        action: "create",
        kind: "task",
        title: "No access",
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await post(w, "fulfillA", {
        action: "transition",
        id: r.body.id,
        status: "done",
        expected_status: "open",
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await post(w, "support", {
        action: "transition",
        id: r.body.id,
        status: "working",
        expected_status: "open",
      })
    ).status,
    200,
  );
  assert.equal(
    (
      await post(w, "support", {
        action: "transition",
        id: r.body.id,
        status: "done",
        expected_status: "open",
      })
    ).status,
    409,
  );
});
test("independent owner approval, expense ledger, immutable decisions, append-only audit", async () => {
  const w = await world();
  const r = await post(w, "manager", {
    action: "create",
    kind: "expense",
    title: "Synthetic invoice",
    amount_bdt: 125.5,
  });
  const change = {
    action: "transition",
    id: r.body.id,
    status: "approved",
    expected_status: "pending",
  };
  assert.equal((await post(w, "manager", change)).status, 403);
  assert.equal((await post(w, "owner", change)).status, 200);
  assert.equal((await get(w)).body.finance.approved_expenses_minor, 12550);
  assert.equal(
    (
      await post(w, "owner", {
        ...change,
        expected_status: "approved",
        status: "rejected",
      })
    ).status,
    409,
  );
  assert.throws(
    () => w.db.run("DELETE FROM business_audit"),
    /AUDIT_IMMUTABLE/,
  );
  assert.throws(
    () => w.db.run("UPDATE business_audit SET action='tampered'"),
    /AUDIT_IMMUTABLE/,
  );
  const own = await post(w, "owner", {
    action: "create",
    kind: "expense",
    title: "Owner request",
    amount_bdt: 1,
  });
  assert.equal(
    (await post(w, "owner", { ...change, id: own.body.id })).status,
    403,
  );
});
test("race writes no phantom approval or duplicate audit; untrusted privileged fields rejected", async () => {
  const w = await world();
  const r = await post(w, "manager", {
    action: "create",
    kind: "price_review",
    title: "test plan",
    amount_bdt: 1500,
  });
  w.db.beforeBatch = (db) =>
    db
      .prepare(
        "UPDATE business_records SET status='rejected',decided_by=? WHERE id=?",
      )
      .run(OPERATORS.owner.id, r.body.id);
  assert.equal(
    (
      await post(w, "owner", {
        action: "transition",
        id: r.body.id,
        expected_status: "pending",
        status: "approved",
      })
    ).status,
    409,
  );
  assert.equal(w.db.one("SELECT COUNT(*) AS n FROM business_audit").n, 1);
  assert.equal(
    (
      await post(w, "owner", {
        action: "create",
        kind: "task",
        title: "test",
        business_unit: "sister",
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await post(w, "owner", {
        action: "create",
        kind: "expense",
        title: "test",
        amount_bdt: 1.001,
      })
    ).status,
    400,
  );
  assert.equal(
    (
      await post(w, "owner", {
        action: "create",
        kind: "task",
        title: "oversized",
        details: "a".repeat(5000),
      })
    ).status,
    400,
  );
});
test("revenue uses all verified receipts, Dhaka boundaries, no unpaid claims or profit fabrication", async () => {
  const w = await world();
  w.seedOrder({ total: 999999 });
  const a = w.seedOrder({ status: "payment_confirmed", total: 125000 });
  const b = w.seedOrder({ status: "refunded", total: 50000 });
  w.db.run(
    "UPDATE payment_verifications SET verified_at='2026-09-30T18:00:00.000Z' WHERE order_id=?",
    a.id,
  );
  w.db.run(
    "UPDATE payment_verifications SET verified_at='2026-10-01T00:00:00.000Z' WHERE order_id=?",
    b.id,
  );
  const r = (await get(w, "owner", "?month=2026-10")).body;
  assert.equal(r.finance.sales_minor, 125000);
  assert.equal(r.finance.refunded_order_minor, 50000);
  assert.equal(r.finance.verified_receipts, 2);
  assert.equal(r.finance.profit_minor, null);
  assert.equal(r.target_bdt, 300000);
  assert.equal(
    (await get(w, "owner", "?month=2026-09")).body.finance.sales_minor,
    0,
  );
});
