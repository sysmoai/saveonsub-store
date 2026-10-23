import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { makeWorld, restoreFetch, OPERATORS } from "./harness.mjs";

console.warn = () => {};
console.error = () => {};

let w;
const PHONE = "+8801711223344";
const EMAIL = "real.looking@example.test";
const NAME = "Rahim Uddin";
const NOTE = "customer said account password is hunter2";

beforeEach(async () => { w = await makeWorld(); });
afterEach(() => restoreFetch());

const seedAll = () => ({
  review: w.seedOrder({ status: "payment_review", name: NAME, phone: PHONE, email: EMAIL }),
  delivered: w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id, name: NAME, phone: PHONE, email: EMAIL }),
  mine: w.seedOrder({ status: "fulfilling", assignee: OPERATORS.support.id, name: NAME, phone: PHONE, email: EMAIL }),
});
const rowFor = (body, pub) => body.orders.find(o => o.public_order_id === pub);

test("C: owner and manager see full contact details", async () => {
  const o = seedAll();
  for (const who of ["owner", "manager"]) {
    const r = await w.api.list(who);
    const row = rowFor(r.body, o.review.pub);
    assert.equal(row.customer_name, NAME);
    assert.equal(row.customer_phone, PHONE);
    assert.equal(row.customer_email, EMAIL);
  }
});

test("C: viewer gets the queue shape only - no name, phone, email or assignee anywhere in the response", async () => {
  seedAll();
  const r = await w.api.list("viewer");
  assert.equal(r.status, 200);
  const raw = JSON.stringify(r.body);
  for (const secret of [NAME, "Rahim", PHONE, EMAIL, OPERATORS.fulfillA.id]) assert.ok(!raw.includes(secret), `leaked ${secret}`);
  for (const row of r.body.orders) {
    assert.equal(row.customer_name, null);
    assert.equal(row.customer_phone, null);
    assert.equal(row.customer_email, null);
  }
});

test("C: fulfillment gets name and email for delivery but never the phone number", async () => {
  const o = seedAll();
  const row = rowFor((await w.api.list("fulfillA")).body, o.delivered.pub);
  assert.equal(row.customer_name, NAME);
  assert.equal(row.customer_email, EMAIL);
  assert.equal(row.customer_phone, null);
  assert.ok(!JSON.stringify(await w.api.list("fulfillA")).includes(PHONE));
});

test("C: support sees contact details only for post-delivery or self-assigned orders", async () => {
  const o = seedAll();
  const body = (await w.api.list("support")).body;
  const unrelated = rowFor(body, o.review.pub);
  assert.equal(unrelated.customer_name, "R.");
  assert.equal(unrelated.customer_phone, null);
  assert.equal(unrelated.customer_email, null);
  for (const key of ["delivered", "mine"]) {
    const row = rowFor(body, o[key].pub);
    assert.equal(row.customer_phone, PHONE, key);
    assert.equal(row.customer_email, EMAIL, key);
  }
});

test("C: payment references and other internal columns are never returned by the list", async () => {
  w.seedOrder({ status: "payment_review", ref: "CUSTOMERCLAIM1" });
  for (const who of ["owner", "manager", "fulfillA", "support", "viewer"]) {
    const raw = JSON.stringify((await w.api.list(who)).body);
    assert.ok(!raw.includes("CUSTOMERCLAIM1"), who);
    assert.ok(!raw.includes("tracking_token_hash") && !raw.includes("idempotency_key"), who);
  }
});

test("C: event history is redacted per role on the server", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_review" });
  await w.api.verify("owner", pub, { provider: "bkash", transaction_id: "9ABC12XYZ0", amount_bdt: 1500, evidence_note: "stmt" });
  await w.api.claim("fulfillA", pub);
  await w.api.status("manager", pub, { status: "refunded", note: NOTE });

  const owner = (await w.api.events("owner", pub)).body.events;
  const refund = owner.find(e => e.payload && e.payload.note);
  assert.equal(refund.payload.note, NOTE, "owner sees the full payload");
  assert.equal(refund.actor_id, OPERATORS.manager.id);

  for (const who of ["fulfillA", "support"]) {
    const r = await w.api.events(who, pub);
    const raw = JSON.stringify(r.body);
    assert.ok(!raw.includes("hunter2") && !raw.includes("note"), `${who} saw free-text note`);
    assert.ok(!raw.includes(OPERATORS.manager.id) && !raw.includes("actor_id"), `${who} saw actor ids`);
    assert.ok(raw.includes("refunded"), "non-sensitive transition data is still visible");
  }

  const viewer = JSON.stringify((await w.api.events("viewer", pub)).body);
  for (const leaked of ["hunter2", "payload", "actor_id", OPERATORS.owner.id, "last4", "XYZ0", "from", "refunded"]) {
    assert.ok(!viewer.includes(leaked), `viewer saw ${leaked}`);
  }
  assert.ok(viewer.includes("status_changed") && viewer.includes("created_at"));
  void id;
});

test("C: payment verification events never expose the provider reference", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  await w.api.verify("owner", pub, { provider: "nagad", transaction_id: "SECRETTXN99", amount_bdt: 1500 });
  for (const who of ["owner", "manager", "fulfillA", "support", "viewer"]) {
    assert.ok(!JSON.stringify((await w.api.events(who, pub)).body).includes("SECRETTXN99"), who);
  }
});

test("C: invalid list filters are rejected, and limit is clamped", async () => {
  for (let i = 0; i < 3; i++) w.seedOrder();
  assert.equal((await w.api.list("owner", "?status=drop table")).status, 400);
  assert.equal((await w.api.list("owner", "?status=payment_review%27%20OR%201=1")).status, 400);
  assert.equal((await w.api.list("owner", "?limit=NaN")).body.orders.length, 3);
  assert.equal((await w.api.list("owner", "?limit=1")).body.orders.length, 1);
  assert.equal((await w.api.list("owner", "?limit=-5")).body.orders.length, 1);
});

test("C: events for an unknown order are 404 for every role", async () => {
  for (const who of ["owner", "fulfillA", "support", "viewer"]) {
    assert.equal((await w.api.events(who, "SOS-NOPE")).status, 404);
  }
});
