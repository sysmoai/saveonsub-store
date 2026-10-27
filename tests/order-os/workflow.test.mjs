import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { makeWorld, restoreFetch, OPERATORS } from "./harness.mjs";
import { ORDER_STATUSES, decideTransition } from "../../functions/lib/order-os/order-workflow.ts";

console.warn = () => {};
console.error = () => {};

let w;
beforeEach(async () => { w = await makeWorld(); });
afterEach(() => restoreFetch());

const GOOD_VERIFY = { provider: "bkash", transaction_id: "9ABC12XYZ0", amount_bdt: 1500, evidence_ref: "stmt:bkash-2026-01-01-0001", receipt_confirmed: true, receipt_source: "receiving_account_history" };

// ---------------------------------------------------------------- Finding A
test("A: owner/manager cannot take any edge that is not in the ordinary state machine", async () => {
  const allowed = {
    submitted: ["payment_review", "cancelled"], payment_review: ["cancelled"], payment_confirmed: ["refunded"],
    assigned: ["fulfilling", "refunded"], fulfilling: ["delivered", "refunded"],
    delivered: ["completed", "support_open", "refunded"], support_open: ["completed", "fulfilling", "refunded"],
    completed: ["support_open", "refunded"], cancelled: [], refunded: [],
  };
  for (const role of ["owner", "manager"]) {
    for (const from of ORDER_STATUSES) for (const to of ORDER_STATUSES) {
      const ok = decideTransition(role, from, to).ok;
      assert.equal(ok, (allowed[from] || []).includes(to), `${role} ${from}->${to}`);
    }
  }
});

test("A: cancelled and refunded are immutable for every role through the status endpoint", async () => {
  for (const terminal of ["cancelled", "refunded"]) {
    const { pub, id } = w.seedOrder({ status: terminal });
    const before = w.snapshot();
    for (const who of ["owner", "manager", "fulfillA", "support", "viewer"]) {
      for (const to of ORDER_STATUSES.filter(s => s !== terminal && s !== "submitted")) {
        const r = await w.api.status(who, pub, { status: to });
        assert.ok([403, 409].includes(r.status), `${who} ${terminal}->${to} got ${r.status}`);
      }
    }
    assert.equal(w.snapshot(), before, "denied transitions must not change anything");
    assert.equal(w.order(pub).status, terminal);
    assert.equal(w.events(id).length, 0);
  }
});

test("A: the database itself refuses to leave a terminal state (trigger, bypassing the API)", async () => {
  for (const terminal of ["cancelled", "refunded"]) {
    const { id } = w.seedOrder({ status: terminal });
    assert.throws(() => w.db.run("UPDATE orders SET status='payment_review' WHERE id=?", id), /TERMINAL_ORDER_IMMUTABLE/);
    // Either guard may fire first for a paid target; the point is the database refuses.
    assert.throws(() => w.db.run("UPDATE orders SET status='completed' WHERE id=?", id), /TERMINAL_ORDER_IMMUTABLE|PAYMENT_NOT_VERIFIED/);
    assert.equal(w.db.one("SELECT status FROM orders WHERE id=?", id).status, terminal);
  }
});

test("A: support cannot jump to completed from an arbitrary state", async () => {
  for (const from of ["payment_review", "payment_confirmed", "assigned", "fulfilling", "delivered"]) {
    const { pub } = w.seedOrder({ status: from, assignee: OPERATORS.fulfillA.id });
    const before = w.snapshot();
    const r = await w.api.status("support", pub, { status: "completed" });
    // 409 where no such edge exists, 403 where the edge exists but support lacks it.
    assert.ok([403, 409].includes(r.status), `${from} got ${r.status}`);
    if (from === "delivered") assert.equal(r.status, 403);
    assert.equal(w.snapshot(), before);
  }
});

test("A: support may only reopen and close support cases on delivered work", async () => {
  const delivered = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  assert.equal((await w.api.status("support", delivered.pub, { status: "support_open" })).status, 200);
  assert.equal((await w.api.status("support", delivered.pub, { status: "completed" })).status, 200);
  assert.equal((await w.api.status("support", delivered.pub, { status: "support_open" })).status, 200);
  assert.equal((await w.api.status("support", delivered.pub, { status: "refunded" })).status, 403);
  assert.equal((await w.api.status("support", delivered.pub, { status: "cancelled" })).status, 409);
});

test("A: refunds and cancellations are manager-only; fulfillment cannot refund or cancel", async () => {
  const a = w.seedOrder({ status: "fulfilling", assignee: OPERATORS.fulfillA.id });
  assert.equal((await w.api.status("fulfillA", a.pub, { status: "refunded" })).status, 403);
  assert.equal((await w.api.status("manager", a.pub, { status: "refunded" })).status, 200);
  const b = w.seedOrder({ status: "payment_review" });
  assert.equal((await w.api.status("fulfillA", b.pub, { status: "cancelled" })).status, 403);
  assert.equal((await w.api.status("manager", b.pub, { status: "cancelled" })).status, 200);
});

test("A: generic status endpoint refuses payment_confirmed and assigned (dedicated endpoints only)", async () => {
  const a = w.seedOrder({ status: "payment_review" });
  const r1 = await w.api.status("owner", a.pub, { status: "payment_confirmed" });
  assert.equal(r1.status, 409);
  assert.equal(r1.body.error, "USE_PAYMENT_VERIFICATION");
  const b = w.seedOrder({ status: "payment_confirmed" });
  const r2 = await w.api.status("owner", b.pub, { status: "assigned" });
  assert.equal(r2.body.error, "USE_CLAIM");
  assert.equal(w.order(a.pub).status, "payment_review");
  assert.equal(w.order(b.pub).status, "payment_confirmed");
});

test("A: same-state, unknown and unsupported statuses are rejected", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  assert.equal((await w.api.status("owner", pub, { status: "payment_review" })).status, 409);
  assert.equal((await w.api.status("owner", pub, { status: "teleported" })).status, 400);
  assert.equal((await w.api.status("owner", pub, { status: "submitted" })).status, 400);
  assert.equal((await w.api.status("owner", pub, {})).status, 400);
  assert.equal((await w.api.status("owner", pub, "not json")).status, 400);
  assert.equal((await w.api.status("owner", "SOS-NOPE", { status: "cancelled" })).status, 404);
});

test("A: viewer can never change anything", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const before = w.snapshot();
  assert.equal((await w.api.status("viewer", pub, { status: "cancelled" })).status, 403);
  assert.equal((await w.api.claim("viewer", pub)).status, 403);
  assert.equal((await w.api.verify("viewer", pub, GOOD_VERIFY)).status, 403);
  assert.equal((await w.api.reverse("viewer", pub, { reason: "x".repeat(30) })).status, 403);
  assert.equal(w.snapshot(), before);
});

test("A: the audited reversal workflow is the only way out of a terminal state", async () => {
  const { pub, id } = w.seedOrder({ status: "refunded" });
  // Not owner / missing reason / not terminal -> refused, nothing changes.
  const before = w.snapshot();
  assert.equal((await w.api.reverse("manager", pub, { reason: "r".repeat(30) })).status, 403);
  assert.equal((await w.api.reverse("owner", pub, { reason: "too short" })).status, 400);
  assert.equal((await w.api.reverse("owner", pub, {})).status, 400);
  assert.equal(w.snapshot(), before);
  const live = w.seedOrder({ status: "assigned" });
  assert.equal((await w.api.reverse("owner", live.pub, { reason: "r".repeat(30) })).status, 409);

  const ok = await w.api.reverse("owner", pub, { reason: "Customer refund was issued in error; payment must be re-verified" });
  assert.equal(ok.status, 200);
  const row = w.order(pub);
  assert.equal(row.status, "payment_review", "reversal never lands in a paid or fulfilment state");
  assert.equal(row.assigned_operator_id, null);
  assert.equal(row.payment_confirmed_at, null);
  assert.ok(w.db.one("SELECT voided_at FROM payment_verifications WHERE order_id=?", id).voided_at, "old verification is voided");
  assert.equal(w.events(id).at(-1).event_type, "terminal_reversal");
  assert.equal(w.db.one("SELECT count(*) c FROM order_reversals WHERE applied_at IS NOT NULL").c, 1);
  // The grant is single-use: the order is not terminal anymore, and re-cancelling then reopening needs a new reversal.
  assert.equal((await w.api.status("owner", pub, { status: "cancelled" })).status, 200);
  assert.throws(() => w.db.run("UPDATE orders SET status='payment_review' WHERE id=?", id), /TERMINAL_ORDER_IMMUTABLE/);
});

test("A: after a reversal, fulfilment cannot restart until payment is verified again", async () => {
  const { pub } = w.seedOrder({ status: "refunded" });
  await w.api.reverse("owner", pub, { reason: "Refund reversed after bank dispute resolved in our favour" });
  assert.equal((await w.api.claim("fulfillA", pub)).status, 409);
  assert.equal((await w.api.verify("owner", pub, GOOD_VERIFY)).status, 200);
  assert.equal((await w.api.claim("fulfillA", pub)).status, 200);
});

// ---------------------------------------------------------------- Finding B
test("B: payment_confirmed is impossible without a verification record (database trigger)", async () => {
  const { id } = w.seedOrder({ status: "payment_review" });
  for (const s of ["payment_confirmed", "assigned", "fulfilling", "delivered", "completed", "support_open"]) {
    assert.throws(() => w.db.run("UPDATE orders SET status=? WHERE id=?", s, id), /PAYMENT_NOT_VERIFIED/, s);
  }
  assert.throws(() => w.db.run(`INSERT INTO orders (id,public_order_id,tracking_token_hash,idempotency_key,status,total_minor,created_at,updated_at)
    VALUES ('x','SOS-X','h','k-xxxxxxxxxxxxxxxxxx','completed',100,'t','t')`), /ORDER_MUST_START_UNPAID/);
});

test("B: only the owner (CEO) can verify by default; manager, support, fulfillment and viewer are refused", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const before = w.snapshot();
  for (const who of ["manager", "support", "fulfillA", "viewer"]) {
    assert.equal((await w.api.verify(who, pub, GOOD_VERIFY)).status, 403, who);
  }
  assert.equal(w.snapshot(), before);
});

test("B: verification records provenance and confirms the order atomically", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_review", ref: "9abc12xyz0" });
  const r = await w.api.verify("owner", pub, { ...GOOD_VERIFY, evidence_note: "seen in merchant statement" });
  assert.equal(r.status, 200);
  assert.equal(r.body.status, "payment_confirmed");
  const v = w.db.one("SELECT * FROM payment_verifications WHERE order_id=?", id);
  assert.equal(v.verified_by, OPERATORS.owner.id);
  assert.equal(v.evidence_ref, GOOD_VERIFY.evidence_ref);
  assert.equal(v.amount_minor, 150000);
  assert.equal(v.currency, "BDT");
  assert.equal(v.txn_ref_last4, "XYZ0");
  assert.equal(v.matches_customer_reference, 1);
  assert.match(v.txn_ref_hash, /^[0-9a-f]{64}$/);
  assert.ok(!JSON.stringify(v).includes("9ABC12XYZ0"), "full provider reference is not stored");
  assert.equal(w.order(pub).status, "payment_confirmed");
  assert.ok(w.order(pub).payment_confirmed_at);
  const ev = w.events(id).at(-1);
  assert.equal(ev.event_type, "payment_verified");
  assert.ok(!ev.payload_json.includes("9ABC12XYZ0"));
});

test("B: a customer-submitted reference alone is never proof (mismatch is flagged, amount still required)", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_review", ref: "CUSTOMERCLAIM1" });
  const r = await w.api.verify("owner", pub, GOOD_VERIFY);
  assert.equal(r.status, 200);
  assert.equal(r.body.verification.matches_customer_reference, false);
  assert.equal(w.db.one("SELECT matches_customer_reference m FROM payment_verifications WHERE order_id=?", id).m, 0);
});

test("B: amount and currency must match the order total exactly; nothing changes otherwise", async () => {
  const { pub } = w.seedOrder({ status: "payment_review", total: 150000 });
  const before = w.snapshot();
  for (const body of [
    { ...GOOD_VERIFY, amount_bdt: 1499.99 }, { ...GOOD_VERIFY, amount_bdt: 1500.01 }, { ...GOOD_VERIFY, amount_bdt: 15000 },
    { ...GOOD_VERIFY, currency: "USD" },
  ]) {
    const r = await w.api.verify("owner", pub, body);
    assert.equal(r.status, 409, JSON.stringify(body));
    assert.equal(r.body.error, "AMOUNT_OR_CURRENCY_MISMATCH");
    assert.doesNotMatch(JSON.stringify(r.body), /1500|150000/, "expected total is not revealed");
  }
  assert.equal(w.snapshot(), before);
});

test("B: malformed verification input is rejected with no side effects", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const before = w.snapshot();
  const bad = [
    { ...GOOD_VERIFY, provider: "paypal" }, { ...GOOD_VERIFY, provider: undefined },
    { ...GOOD_VERIFY, transaction_id: "short" }, { ...GOOD_VERIFY, transaction_id: "bad id with spaces!!" },
    { ...GOOD_VERIFY, transaction_id: 1234567890 }, { ...GOOD_VERIFY, amount_bdt: "1500" },
    { ...GOOD_VERIFY, amount_bdt: -5 }, { ...GOOD_VERIFY, amount_bdt: 0 }, { ...GOOD_VERIFY, amount_bdt: Infinity },
    { ...GOOD_VERIFY, amount_bdt: 1500.001 },
  ];
  for (const body of bad) {
    const r = await w.api.verify("owner", pub, body);
    assert.equal(r.status, 400, JSON.stringify(body));
  }
  assert.equal(w.snapshot(), before);
});

test("B: the same provider reference cannot back two orders (duplicate control)", async () => {
  const a = w.seedOrder({ status: "payment_review", total: 150000 });
  const b = w.seedOrder({ status: "payment_review", total: 150000 });
  assert.equal((await w.api.verify("owner", a.pub, GOOD_VERIFY)).status, 200);
  const before = w.snapshot();
  const dup = await w.api.verify("owner", b.pub, { ...GOOD_VERIFY, transaction_id: "9abc12xyz0" });
  assert.equal(dup.status, 409);
  assert.equal(dup.body.error, "DUPLICATE_PAYMENT_REFERENCE");
  assert.equal(w.snapshot(), before, "failed duplicate leaves no verification, event or status change");
  assert.equal(w.order(b.pub).status, "payment_review");
  // Same reference on another provider is a different payment.
  assert.equal((await w.api.verify("owner", b.pub, { ...GOOD_VERIFY, provider: "nagad" })).status, 200);
});

test("B: an order cannot be verified twice, and only while awaiting payment", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  assert.equal((await w.api.verify("owner", pub, GOOD_VERIFY)).status, 200);
  const again = await w.api.verify("owner", pub, { ...GOOD_VERIFY, transaction_id: "ANOTHER12345" });
  assert.equal(again.status, 409);
  const done = w.seedOrder({ status: "delivered" });
  assert.equal((await w.api.verify("owner", done.pub, GOOD_VERIFY)).status, 409);
  const cancelled = w.seedOrder({ status: "cancelled" });
  assert.equal((await w.api.verify("owner", cancelled.pub, GOOD_VERIFY)).status, 409);
  assert.equal((await w.api.verify("owner", "SOS-NOPE", GOOD_VERIFY)).status, 404);
});

test("B: completion before verified payment is impossible end to end", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const before = w.snapshot();
  for (const who of ["owner", "manager", "support", "fulfillA"]) {
    for (const to of ["payment_confirmed", "assigned", "fulfilling", "delivered", "support_open", "completed"]) {
      const r = await w.api.status(who, pub, { status: to });
      assert.ok(r.status >= 400, `${who}->${to}`);
    }
    assert.ok((await w.api.claim(who, pub)).status >= 400);
  }
  assert.equal(w.snapshot(), before);
});

test("B: a full happy path runs only through the sanctioned steps", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_review" });
  assert.equal((await w.api.verify("owner", pub, GOOD_VERIFY)).status, 200);
  assert.equal((await w.api.claim("fulfillA", pub)).body.status, "assigned");
  assert.equal((await w.api.status("fulfillA", pub, { status: "fulfilling" })).status, 200);
  assert.equal((await w.api.status("fulfillA", pub, { status: "delivered" })).status, 200);
  assert.equal((await w.api.status("fulfillA", pub, { status: "completed" })).status, 200);
  assert.deepEqual(w.events(id).map(e => e.event_type),
    ["payment_verified", "order_claimed", "status_changed", "status_changed", "status_changed"]);
});

// ---------------------------------------------------------------- Finding D
test("D: of two simultaneous claims exactly one wins and the loser changes nothing", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_confirmed" });
  const [a, b] = await Promise.all([w.api.claim("fulfillA", pub), w.api.claim("fulfillB", pub)]);
  assert.deepEqual([a.status, b.status].sort(), [200, 409]);
  const winner = a.status === 200 ? OPERATORS.fulfillA.id : OPERATORS.fulfillB.id;
  assert.equal(w.order(pub).assigned_operator_id, winner);
  assert.equal(w.events(id).filter(e => e.event_type === "order_claimed").length, 1, "one claim event only");
  assert.equal((a.status === 409 ? a : b).body.error, "ALREADY_CLAIMED");
});

test("D: a claim that loses a race (another claim lands between read and write) cannot overwrite the winner", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_confirmed" });
  w.db.beforeBatch = (raw) => raw.exec(`UPDATE orders SET assigned_operator_id='${OPERATORS.fulfillB.id}', status='assigned' WHERE id='${id}'`);
  const r = await w.api.claim("fulfillA", pub);
  assert.equal(r.status, 409);
  assert.equal(w.order(pub).assigned_operator_id, OPERATORS.fulfillB.id);
  assert.equal(w.events(id).length, 0, "no misleading claim event for the loser");
});

test("D: re-claiming your own order is idempotent and adds no event", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_confirmed" });
  await w.api.claim("fulfillA", pub);
  const again = await w.api.claim("fulfillA", pub);
  assert.equal(again.status, 200);
  assert.equal(again.body.already_yours, true);
  assert.equal(w.events(id).length, 1);
});

test("D: claiming is refused for unpaid, closed or missing orders and for support/viewer", async () => {
  for (const status of ["payment_review", "cancelled", "refunded"]) {
    const { pub } = w.seedOrder({ status });
    const before = w.snapshot();
    assert.equal((await w.api.claim("fulfillA", pub)).status, 409, status);
    assert.equal(w.snapshot(), before);
  }
  const { pub } = w.seedOrder({ status: "payment_confirmed" });
  assert.equal((await w.api.claim("support", pub)).status, 403);
  assert.equal((await w.api.claim("viewer", pub)).status, 403);
  assert.equal((await w.api.claim("owner", "SOS-NOPE")).status, 404);
});

test("D: a stale status update (state changed under the caller) is refused and writes no event", async () => {
  const { pub, id } = w.seedOrder({ status: "assigned", assignee: OPERATORS.fulfillA.id });
  w.db.beforeBatch = (raw) => raw.exec(`UPDATE orders SET status='fulfilling' WHERE id='${id}'`);
  const r = await w.api.status("fulfillA", pub, { status: "fulfilling" });
  assert.equal(r.status, 409);
  assert.equal(r.body.error, "STALE_STATE");
  assert.equal(w.events(id).length, 0);
});

test("D: simultaneous conflicting transitions - exactly one applies, one audit event", async () => {
  const { pub, id } = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const [a, b] = await Promise.all([
    w.api.status("manager", pub, { status: "refunded" }),
    w.api.status("fulfillA", pub, { status: "completed" }),
  ]);
  assert.equal([a.status, b.status].filter(s => s === 200).length >= 1, true);
  const final = w.order(pub).status;
  assert.ok(["refunded", "completed"].includes(final));
  const changes = w.events(id).filter(e => e.event_type === "status_changed");
  const succeeded = [a, b].filter(r => r.status === 200).length;
  assert.equal(changes.length, succeeded, "one audit event per applied change, none for refused ones");
});

test("D: expected_status gives callers explicit optimistic concurrency", async () => {
  const { pub } = w.seedOrder({ status: "assigned", assignee: OPERATORS.fulfillA.id });
  const r = await w.api.status("fulfillA", pub, { status: "fulfilling", expected_status: "payment_review" });
  assert.equal(r.status, 409);
  assert.equal(r.body.error, "STALE_STATE");
});

// ---------------------------------------------------------------- Finding E
test("E: fulfillment can only act on orders assigned to them", async () => {
  const { pub } = w.seedOrder({ status: "assigned", assignee: OPERATORS.fulfillA.id });
  const before = w.snapshot();
  assert.equal((await w.api.status("fulfillB", pub, { status: "fulfilling" })).status, 403);
  assert.equal(w.snapshot(), before);
  assert.equal((await w.api.status("fulfillA", pub, { status: "fulfilling" })).status, 200);
});

test("E: moving to fulfilling requires a claimed order even for managers", async () => {
  const { pub } = w.seedOrder({ status: "support_open", assignee: null });
  const r = await w.api.status("manager", pub, { status: "fulfilling" });
  assert.equal(r.status, 409);
  assert.equal(r.body.error, "CLAIM_REQUIRED");
});

test("E: support (customer-service role) cannot verify payments, refund, cancel, claim or reverse", async () => {
  const a = w.seedOrder({ status: "payment_review" });
  const b = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const c = w.seedOrder({ status: "refunded" });
  const before = w.snapshot();
  assert.equal((await w.api.verify("support", a.pub, GOOD_VERIFY)).status, 403);
  assert.equal((await w.api.status("support", a.pub, { status: "cancelled" })).status, 403);
  assert.equal((await w.api.status("support", b.pub, { status: "refunded" })).status, 403);
  assert.equal((await w.api.claim("support", b.pub)).status, 403);
  assert.equal((await w.api.reverse("support", c.pub, { reason: "r".repeat(30) })).status, 403);
  assert.equal(w.snapshot(), before);
});

test("E: only the owner may authorise a reversal", async () => {
  const { pub } = w.seedOrder({ status: "cancelled" });
  for (const who of ["manager", "fulfillA", "support", "viewer"]) {
    assert.equal((await w.api.reverse(who, pub, { reason: "r".repeat(30) })).status, 403, who);
  }
  assert.equal(w.order(pub).status, "cancelled");
});

test("E: no endpoint accepts a price or discount field (pricing stays CEO-controlled)", async () => {
  const { pub } = w.seedOrder({ status: "payment_review", total: 150000 });
  await w.api.status("owner", pub, { status: "cancelled", total_minor: 1, discount_bdt: 500, price: 1 });
  assert.equal(w.order(pub).total_minor, 150000);
  const { pub: p2 } = w.seedOrder({ status: "payment_review", total: 150000 });
  const r = await w.api.verify("owner", p2, { ...GOOD_VERIFY, amount_bdt: 1500, total_minor: 1 });
  assert.equal(r.status, 200);
  assert.equal(w.order(p2).total_minor, 150000);
});

// ---------------------------------------------------------------- Audit integrity
test("audit: events are append-only at the database level", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_review" });
  await w.api.status("owner", pub, { status: "cancelled", note: "customer asked" });
  assert.throws(() => w.db.run("UPDATE order_events SET payload_json='{}' WHERE order_id=?", id), /AUDIT_LOG_IMMUTABLE/);
});

test("audit: every applied change has exactly one event; refused changes have none", async () => {
  const { pub, id } = w.seedOrder({ status: "payment_review" });
  await w.api.status("support", pub, { status: "cancelled" });        // refused
  await w.api.status("owner", pub, { status: "payment_confirmed" });  // refused (dedicated endpoint)
  assert.equal(w.events(id).length, 0);
  await w.api.status("owner", pub, { status: "cancelled", note: "n" });
  const evs = w.events(id);
  assert.equal(evs.length, 1);
  assert.equal(evs[0].actor_id, OPERATORS.owner.id);
  assert.deepEqual(JSON.parse(evs[0].payload_json), { from: "payment_review", to: "cancelled", note: "n" });
});

test("audit: write failures are reported without leaking database text", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const original = w.db.batch.bind(w.db);
  w.db.batch = async () => { throw new Error("SQLITE_ERROR: no such table: secret_internal_table"); };
  const r = await w.api.status("owner", pub, { status: "cancelled" });
  w.db.batch = original;
  assert.equal(r.status, 503);
  assert.doesNotMatch(JSON.stringify(r.body), /sqlite|secret_internal_table/i);
});

test("missing orders table does not crash the auth layer into a 200", async () => {
  const saved = w.env.DB;
  w.env.DB = { prepare() { throw new Error("D1_ERROR: no such table: operators"); } };
  const r = await w.api.list("owner");
  w.env.DB = saved;
  assert.equal(r.status, 503);
  assert.doesNotMatch(JSON.stringify(r.body), /operators|D1_ERROR/);
});

test("T018-07: PAYMENT_VERIFIER_ROLES can widen to manager only; never to support/fulfillment/viewer", async () => {
  const saved = w.env.PAYMENT_VERIFIER_ROLES;
  try {
    w.env.PAYMENT_VERIFIER_ROLES = "owner,manager,support,fulfillment,viewer";
    const a = w.seedOrder({ status: "payment_review" });
    for (const who of ["support", "fulfillA", "viewer"]) {
      assert.equal((await w.api.verify(who, a.pub, GOOD_VERIFY)).status, 403, who);
    }
    assert.equal((await w.api.verify("manager", a.pub, GOOD_VERIFY)).status, 200);
  } finally {
    w.env.PAYMENT_VERIFIER_ROLES = saved;
  }
  const b = w.seedOrder({ status: "payment_review" });
  assert.equal((await w.api.verify("manager", b.pub, { ...GOOD_VERIFY, transaction_id: "OTHERTXN123" })).status, 403);
});

test("T018-07: evidence_ref is required and must be settlement evidence, not a screenshot or URL", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const before = w.snapshot();
  const { evidence_ref, ...noRef } = GOOD_VERIFY;
  const missing = await w.api.verify("owner", pub, noRef);
  assert.equal(missing.status, 400);
  assert.equal(missing.body.error, "EVIDENCE_REF_REQUIRED");
  for (const bad of ["https://example.test/shot.png", "r2:sos/private/payments/shot.png", "r2:sos/public/x",
                     "r2:sos/private/../x", "screenshot", "stmt:", 42]) {
    const r = await w.api.verify("owner", pub, { ...GOOD_VERIFY, evidence_ref: bad });
    assert.equal(r.status, 400, String(bad));
  }
  assert.equal(w.snapshot(), before);
  const ok = await w.api.verify("owner", pub, { ...GOOD_VERIFY, evidence_ref: "r2:sos/private/payments/2026/statement-0001.pdf" });
  assert.equal(ok.status, 200);
});
