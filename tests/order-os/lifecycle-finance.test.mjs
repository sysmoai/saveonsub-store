// G1/G3/G4/G6 (2026-11-06): storefront CORS, per-order costs, month margin,
// service periods/renewals and refund evidence. Synthetic data only.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { makeWorld, restoreFetch, OPERATORS, handler } from "./harness.mjs";

console.warn = () => {};
console.error = () => {};

let w;
beforeEach(async () => { w = await makeWorld(); });
afterEach(() => restoreFetch());

const costs = (who, pub, body) => body === undefined
  ? w.call("api/ops/orders/[orderId]/costs.ts", "onRequestGet", who, { method: "GET", params: { orderId: pub } })
  : w.call("api/ops/orders/[orderId]/costs.ts", "onRequestPost", who, { body, params: { orderId: pub } });
const period = (who, pub, body) => w.call("api/ops/orders/[orderId]/service-period.ts", "onRequestPost", who, { body, params: { orderId: pub } });
const renewals = (who, query = "?days=30") => w.call("api/ops/renewals/index.ts", "onRequestGet", who, { method: "GET", query });
const margin = (who, query) => w.call("api/ops/finance/margin.ts", "onRequestGet", who, { method: "GET", query });
const REFUND = { amount_bdt: 1500, channel: "bkash", evidence_ref: "stmt:refund-0001" };

// ---------- G6 refund evidence ----------
test("G6: refund without amount, channel or private evidence is refused and writes nothing", async () => {
  const { pub, id } = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const before = w.snapshot();
  for (const refund of [undefined, { ...REFUND, amount_bdt: 0 }, { ...REFUND, channel: "cash" },
    { ...REFUND, evidence_ref: "https://imgur.com/x.png" }, { ...REFUND, amount_bdt: 1500.001 }]) {
    const r = await w.api.status("manager", pub, { status: "refunded", refund });
    assert.equal(r.status, 400, JSON.stringify(refund));
  }
  assert.equal((await w.api.status("manager", pub, { status: "refunded", refund: { ...REFUND, amount_bdt: 1500.01 } })).body.error, "REFUND_EXCEEDS_TOTAL");
  assert.equal(w.snapshot(), before);
  assert.equal(w.db.one("SELECT COUNT(*) n FROM order_refunds").n, 0);
  void id;
});

test("G6: a valid refund records money-out evidence atomically with the status change", async () => {
  const { pub, id } = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const r = await w.api.status("manager", pub, { status: "refunded", refund: { ...REFUND, amount_bdt: 700 } });
  assert.equal(r.status, 200);
  const row = w.db.one("SELECT * FROM order_refunds WHERE order_id=?", id);
  assert.equal(row.amount_minor, 70000);
  assert.equal(row.evidence_ref, "stmt:refund-0001");
  assert.equal(row.recorded_by, OPERATORS.manager.id);
  assert.throws(() => w.db.run("UPDATE order_refunds SET amount_minor=1"), /REFUND_LEDGER_IMMUTABLE/);
  assert.throws(() => w.db.run("DELETE FROM order_refunds"), /REFUND_LEDGER_IMMUTABLE/);
});

test("G6: a lost refund race writes no refund row", async () => {
  const { pub } = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  w.db.beforeBatch = (db) => db.prepare("UPDATE orders SET status='completed' WHERE public_order_id=?").run(pub);
  const r = await w.api.status("manager", pub, { status: "refunded", refund: REFUND, expected_status: "delivered" });
  assert.equal(r.status, 409);
  assert.equal(w.db.one("SELECT COUNT(*) n FROM order_refunds").n, 0);
});

// ---------- G3 costs + margin ----------
test("G3: only the owner records costs; manager reads; others are refused", async () => {
  const { pub } = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const body = { supplier_label: "Supplier A", amount_bdt: 900, evidence_ref: "stmt:sup-1" };
  for (const who of ["manager", "fulfillA", "support", "viewer"]) assert.equal((await costs(who, pub, body)).status, 403, who);
  for (const who of ["fulfillA", "support", "viewer"]) assert.equal((await costs(who, pub)).status, 403, who);
  const r = await costs("owner", pub, body);
  assert.equal(r.status, 201);
  assert.equal(r.body.cost_minor, 90000);
  assert.equal(r.body.gross_margin_minor, 150000 - 90000);
  assert.equal((await costs("manager", pub)).body.cost_minor, 90000);
});

test("G3: unpaid orders, bad amounts, bad evidence and foreign origins are refused", async () => {
  const unpaid = w.seedOrder({ status: "payment_review" });
  assert.equal((await costs("owner", unpaid.pub, { supplier_label: "Supplier A", amount_bdt: 100 })).body.error, "ORDER_NOT_PAID");
  const { pub } = w.seedOrder({ status: "delivered" });
  assert.equal((await costs("owner", pub, { supplier_label: "Supplier A", amount_bdt: -5 })).status, 400);
  assert.equal((await costs("owner", pub, { supplier_label: "S", amount_bdt: 5 })).status, 400);
  assert.equal((await costs("owner", pub, { supplier_label: "Supplier A", amount_bdt: 5, evidence_ref: "http://x" })).status, 400);
  assert.equal((await costs("owner", pub, { entry_type: "correction", supplier_label: "Supplier A", amount_bdt: -5 })).body.error, "CORRECTION_NOTE_REQUIRED");
  const foreign = await w.call("api/ops/orders/[orderId]/costs.ts", "onRequestPost", "owner",
    { body: { supplier_label: "Supplier A", amount_bdt: 5 }, params: { orderId: pub }, headers: { origin: "https://evil.example" } });
  assert.equal(foreign.status, 403);
  assert.equal(w.db.one("SELECT COUNT(*) n FROM order_costs").n, 0);
});

test("G3: corrections are signed rows; the ledger cannot be edited or deleted", async () => {
  const { pub } = w.seedOrder({ status: "completed" });
  await costs("owner", pub, { supplier_label: "Supplier A", amount_bdt: 900 });
  const r = await costs("owner", pub, { entry_type: "correction", supplier_label: "Supplier A", amount_bdt: -100, note: "typo" });
  assert.equal(r.status, 201);
  assert.equal(r.body.cost_minor, 80000);
  assert.throws(() => w.db.run("UPDATE order_costs SET amount_minor=1"), /COST_LEDGER_IMMUTABLE/);
  assert.throws(() => w.db.run("DELETE FROM order_costs"), /COST_LEDGER_IMMUTABLE/);
});

test("G3: month margin uses Dhaka boundaries and flags paid orders with no cost", async () => {
  const a = w.seedOrder({ status: "delivered" });
  const b = w.seedOrder({ status: "delivered", total: 50000 });
  // 2025-12-31T18:30Z is 2026-01-01 00:30 in Dhaka -> January.
  w.db.run("UPDATE payment_verifications SET verified_at='2025-12-31T18:30:00.000Z' WHERE order_id=?", a.id);
  w.db.run("UPDATE payment_verifications SET verified_at='2026-01-10T00:00:00.000Z' WHERE order_id=?", b.id);
  await costs("owner", a.pub, { supplier_label: "Supplier A", amount_bdt: 1000 });
  const m = await margin("owner", "?month=2026-01");
  assert.equal(m.status, 200);
  assert.equal(m.body.paid_orders, 2);
  assert.equal(m.body.verified_receipts_minor, 200000);
  assert.equal(m.body.order_costs_minor, 100000);
  assert.equal(m.body.gross_margin_minor, 100000);
  assert.equal(m.body.paid_orders_without_cost, 1);
  assert.equal(m.body.complete, false);
  assert.equal((await margin("owner", "?month=2025-12")).body.paid_orders, 0);
  assert.equal((await margin("owner", "?month=2026-13")).status, 400);
  for (const who of ["fulfillA", "support", "viewer"]) assert.equal((await margin(who, "?month=2026-01")).status, 403);
});

// ---------- G4 service periods + renewals ----------
const iso = (d) => d.toISOString().slice(0, 10);
const dhakaToday = () => iso(new Date(Date.now() + 6 * 3600 * 1000));
const plus = (n) => { const d = new Date(`${dhakaToday()}T00:00:00Z`); d.setUTCDate(d.getUTCDate() + n); return iso(d); };

test("G4: only delivered orders get a period; fulfillment only on its own orders", async () => {
  const mine = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const theirs = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillB.id });
  const unpaid = w.seedOrder({ status: "payment_review" });
  const p = { service_starts_on: plus(-25), service_ends_on: plus(5) };
  assert.equal((await period("fulfillA", mine.pub, p)).status, 200);
  assert.equal((await period("fulfillA", theirs.pub, p)).status, 403);
  assert.equal((await period("support", mine.pub, p)).status, 403);
  assert.equal((await period("owner", unpaid.pub, p)).body.error, "ORDER_NOT_DELIVERED");
  assert.equal((await period("owner", mine.pub, { service_starts_on: "2026-02-30", service_ends_on: "2026-03-30" })).status, 400);
  assert.equal((await period("owner", mine.pub, { service_starts_on: plus(0), service_ends_on: plus(0) })).status, 400);
  assert.equal((await period("owner", mine.pub, { service_starts_on: plus(0), service_ends_on: plus(500) })).body.error, "SERVICE_PERIOD_TOO_LONG");
  assert.ok(w.events(mine.id).some(e => e.event_type === "service_period_set"));
});

test("G4: renewal queue lists due subscriptions, scoped and shaped by role", async () => {
  const soon = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id, phone: "+8801999000111" });
  const later = w.seedOrder({ status: "completed", assignee: OPERATORS.fulfillB.id });
  const refunded = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  await period("owner", soon.pub, {
    service_starts_on: plus(-27), service_ends_on: plus(3),
    expiry_source: "provider_dashboard", expiry_evidence_ref: "r2:sos/private/synthetic-provider-expiry-001"
  });
  await period("owner", later.pub, { service_starts_on: plus(0), service_ends_on: plus(90) });
  await period("owner", refunded.pub, { service_starts_on: plus(-27), service_ends_on: plus(2) });
  w.db.run("UPDATE orders SET status='refunded' WHERE id=?", refunded.id);

  const owner = await renewals("owner", "?days=7");
  assert.deepEqual(owner.body.renewals.map(r => r.public_order_id), [soon.pub]);
  assert.equal(owner.body.renewals[0].days_left, 3);
  const a = (await renewals("fulfillA")).body.renewals;
  assert.deepEqual(a.map(r => r.public_order_id), [soon.pub]);
  assert.equal(a[0].customer_phone, undefined, "contact PII must not be included without consent verification");
  assert.equal(a[0].outreach_allowed, false, "verified expiry does not itself grant contact consent");
  assert.equal(a[0].expiry_evidence_state, "provider_confirmed");
  assert.equal(owner.body.outreach_enabled, false);
  assert.equal((await renewals("fulfillB", "?days=7")).body.renewals.length, 0);
  for (const who of ["support", "viewer"]) assert.equal((await renewals(who)).status, 403);
});

test("G4 safety: WhatsApp note or legacy expiry is review-only with no contact details", async () => {
  const note = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id, phone: "+8801999000777" });
  const legacy = w.seedOrder({ status: "completed", assignee: OPERATORS.fulfillB.id });
  const result = await period("owner", note.pub, {
    service_starts_on: plus(-27), service_ends_on: plus(3), expiry_source: "whatsapp_note"
  });
  assert.equal(result.status, 200);
  assert.equal(result.body.expiry_evidence_state, "needs_review");
  assert.equal(result.body.renewal_outreach_allowed, false);

  // A legacy period can exist without an attested service_period_set event.
  w.db.run(`INSERT INTO order_service_periods(order_id,service_starts_on,service_ends_on,set_by,updated_at)
    VALUES (?,?,?,?,?)`, legacy.id, plus(-27), plus(4), OPERATORS.owner.id, new Date().toISOString());

  const owner = await renewals("owner", "?days=7");
  assert.equal(owner.status, 200);
  assert.deepEqual(owner.body.renewals, [], "unverified dates must not enter the provider-confirmed queue");
  assert.deepEqual(owner.body.needs_review.map(r => r.public_order_id).sort(), [note.pub, legacy.pub].sort());
  for (const row of owner.body.needs_review) {
    assert.equal(row.outreach_allowed, false);
    assert.equal(row.renewal_contact_consent, "not_verified");
    assert.equal(row.customer_phone, undefined);
    assert.equal(row.customer_email, undefined);
    assert.equal(row.customer_name, undefined);
    assert.equal(row.expiry_evidence_state, "needs_review");
  }
  const mine = await renewals("fulfillA", "?days=7");
  assert.deepEqual(mine.body.needs_review.map(r => r.public_order_id), [note.pub]);
  assert.equal((await renewals("support")).status, 403);
});

test("G4 safety: only owner with private provider evidence can attest verified expiry", async () => {
  const { pub, id } = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const base = { service_starts_on: plus(-26), service_ends_on: plus(4) };
  for (const payload of [
    { ...base, expiry_source: "provider_dashboard" },
    { ...base, expiry_source: "provider_dashboard", expiry_evidence_ref: "https://example.test/expiry.png" },
    { ...base, expiry_source: "provider_dashboard", expiry_evidence_ref: "r2:sos/private/../sensitive" },
    { ...base, expiry_source: "whatsapp_note", expiry_evidence_ref: "r2:sos/private/note" },
    { ...base, expiry_source: "invalid_source" }
  ]) {
    const r = await period("owner", pub, payload);
    assert.equal(r.status, 400);
  }
  assert.equal((await period("fulfillA", pub, {
    ...base, expiry_source: "provider_confirmation", expiry_evidence_ref: "r2:sos/private/provider-001"
  })).status, 403);
  assert.equal(w.db.one("SELECT COUNT(*) n FROM order_service_periods WHERE order_id=?", id).n, 0);

  const verified = await period("owner", pub, {
    ...base, expiry_source: "provider_confirmation", expiry_evidence_ref: "r2:sos/private/provider-001"
  });
  assert.equal(verified.status, 200);
  assert.equal(verified.body.expiry_evidence_state, "provider_confirmed");
  assert.deepEqual((await renewals("owner")).body.renewals.map(r => r.public_order_id), [pub]);

  // Re-saving the same dates as a manual note MUST revoke the old evidentiary status.
  const reviewed = await period("owner", pub, { ...base, expiry_source: "manual_note" });
  assert.equal(reviewed.status, 200);
  const q = await renewals("owner");
  assert.deepEqual(q.body.renewals, []);
  assert.deepEqual(q.body.needs_review.map(r => r.public_order_id), [pub]);
  assert.ok(w.events(id).some(e => e.event_type === "service_period_set"));
});

// ---------- G1 storefront CORS middleware ----------
async function mw(method, origin, url = "https://ops.saveonsub.com/api/orders") {
  const onRequest = await handler("api/orders/_middleware.ts", "onRequest");
  const headers = origin ? { origin } : {};
  let called = false;
  const res = await onRequest({ request: new Request(url, { method, headers }),
    next: async () => { called = true; return new Response("{}", { headers: { "content-type": "application/json" } }); } });
  return { res, called };
}

test("G1: storefront origins get CORS; other origins are refused before the handler", async () => {
  for (const o of ["https://saveonsub.com", "https://www.saveonsub.com"]) {
    const pre = await mw("OPTIONS", o);
    assert.equal(pre.res.status, 204);
    assert.equal(pre.res.headers.get("access-control-allow-origin"), o);
    assert.equal(pre.called, false);
    const post = await mw("POST", o);
    assert.equal(post.called, true);
    assert.equal(post.res.headers.get("access-control-allow-origin"), o);
  }
  for (const o of ["https://evil.example", "https://saveonsub.com.evil.example", "http://saveonsub.com", "null"]) {
    const post = await mw("POST", o);
    assert.equal(post.res.status, 403, o);
    assert.equal(post.called, false, o);
    assert.equal((await mw("OPTIONS", o)).res.status, 403, o);
  }
  const noOrigin = await mw("GET", null);
  assert.equal(noOrigin.called, true);
  assert.equal(noOrigin.res.headers.get("access-control-allow-origin"), null);
  const same = await mw("POST", "https://ops.saveonsub.com");
  assert.equal(same.called, true);
});
