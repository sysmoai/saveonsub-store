// SaveOnSub personal Send Money rails: receipt attestation is human, NOT an API callback.
// Synthetic orders only; no customer or settlement data is included.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { makeWorld, restoreFetch } from "./harness.mjs";

let w;
beforeEach(async () => { w = await makeWorld(); });
afterEach(() => restoreFetch());

const good = (provider, txn = "9ABC12XYZ0") => ({
  provider,
  transaction_id: txn,
  amount_bdt: 1500,
  currency: "BDT",
  evidence_ref: "stmt:synthetic-recipient-account-2026-10-28",
  receipt_confirmed: true,
  receipt_source: provider === "bank_transfer" ? "bank_statement" : "receiving_account_history",
});

const paidAlerts = () => w.db.rows(
  "SELECT * FROM notification_outbox WHERE template_key='paid_order_priority' ORDER BY id"
);

for (const provider of ["bkash", "nagad", "rocket", "bank_transfer"]) {
  test(`verified ${provider} personal receipt creates precisely one P0 paid alert`, async () => {
    const { pub, id } = w.seedOrder();
    w.db.run("UPDATE orders SET payment_method=? WHERE id=?", provider, id);
    assert.equal(paidAlerts().length, 0, "unpaid orders must not interrupt staff");
    const result = await w.api.verify("owner", pub, good(provider));
    assert.equal(result.status, 200);
    assert.equal(result.body.status, "payment_confirmed");
    assert.equal(result.body.staff_notification, "queued_not_sent");
    assert.equal(w.order(pub).priority, 0);
    const alerts = paidAlerts();
    assert.equal(alerts.length, 1);
    assert.equal(alerts[0].status, "pending", "queued does not mean delivered");
    assert.equal(alerts[0].priority, 0);
    assert.equal(alerts[0].destination_key, "sos-ripon");
    assert.equal(alerts[0].order_id, id);
    const payload = JSON.parse(alerts[0].payload_json);
    assert.deepEqual(payload, {
      order_id: pub, amount_minor: 150000, currency: "BDT", provider
    });
    assert.ok(!alerts[0].payload_json.includes("9ABC12XYZ0"), "no full transaction ID in alert");
    assert.ok(!alerts[0].payload_json.includes("Customer"), "no PII in alert");
    assert.equal(w.db.rows("SELECT receipt_source FROM payment_verifications WHERE order_id=?", id)[0].receipt_source,
      good(provider).receipt_source);
  });
}

test("customer reference or unverified order alone cannot enqueue a paid alert", async () => {
  const { pub, id } = w.seedOrder({ ref: "9ABC12XYZ0" });
  assert.equal(w.order(pub).status, "payment_review");
  assert.equal(paidAlerts().length, 0);
  assert.equal(w.events(id).length, 0);
});

test("attestation and actual receiving-account source are required", async () => {
  const { pub } = w.seedOrder();
  const variations = [
    { ...good("bkash"), receipt_confirmed: false },
    { ...good("bkash"), receipt_confirmed: undefined },
    { ...good("bkash"), receipt_source: "customer_screenshot" },
    { ...good("bkash"), receipt_source: "bank_statement" },
    { ...good("bank_transfer"), receipt_source: "receiving_account_history" },
  ];
  for (const payload of variations) {
    const r = await w.api.verify("owner", pub, payload);
    assert.equal(r.status, 400);
    assert.ok(["RECEIPT_ATTESTATION_REQUIRED", "INVALID_RECEIPT_SOURCE"].includes(r.body.error));
    assert.equal(paidAlerts().length, 0);
    assert.equal(w.order(pub).status, "payment_review");
  }
});

test("the same incoming reference cannot pay two orders or trigger two alerts", async () => {
  const a = w.seedOrder();
  const b = w.seedOrder();
  w.db.run("UPDATE orders SET payment_method='nagad' WHERE id IN (?,?)", a.id, b.id);
  assert.equal((await w.api.verify("owner", a.pub, good("nagad"))).status, 200);
  const replay = await w.api.verify("owner", b.pub, good("nagad"));
  assert.equal(replay.status, 409);
  assert.equal(w.order(b.pub).status, "payment_review");
  assert.equal(paidAlerts().length, 1);
  assert.equal((await w.api.verify("owner", a.pub, good("nagad"))).status, 409);
  assert.equal(paidAlerts().length, 1);
});

test("underpayment and unsupported role do not create paid alerts", async () => {
  const { pub } = w.seedOrder();
  assert.equal((await w.api.verify("owner", pub, { ...good("bkash"), amount_bdt: 1499 })).status, 409);
  assert.equal((await w.api.verify("support", pub, good("bkash"))).status, 403);
  assert.equal(paidAlerts().length, 0);
});

test("storage uniqueness blocks duplicate priority notification for the same verified order", async () => {
  const { pub, id } = w.seedOrder();
  w.db.run("UPDATE orders SET payment_method='rocket' WHERE id=?", id);
  assert.equal((await w.api.verify("owner", pub, good("rocket"))).status, 200);
  const row = paidAlerts()[0];
  assert.throws(() => w.db.run(
    "INSERT INTO notification_outbox (order_id,channel,destination_key,template_key,payload_json,priority,status,next_attempt_at,created_at,updated_at) VALUES (?,?,?,?,?,0,'pending',?,?,?)",
    id, "webhook", row.destination_key, row.template_key, "{}", row.next_attempt_at, row.created_at, row.updated_at
  ), /UNIQUE/);
  assert.equal(paidAlerts().length, 1);
});

test("a real receipt from another rail cannot silently pay the selected order", async () => {
  const { pub } = w.seedOrder(); // Selected rail = bkash.
  const r = await w.api.verify("owner", pub, good("nagad"));
  assert.equal(r.status, 409);
  assert.equal(r.body.error, "PAYMENT_METHOD_MISMATCH");
  assert.equal(w.order(pub).status, "payment_review");
  assert.equal(paidAlerts().length, 0);
});
