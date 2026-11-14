// Staff-assisted ticket intake, assignment, escalation, categories.
// FakeD1 (in-memory SQLite), synthetic operators/orders only. NOT a staging or
// production result: no Cloudflare D1, Turnstile, Access MFA or real login.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { makeWorld, restoreFetch, handler, OPERATORS } from "./harness.mjs";

console.warn = () => {};
console.error = () => {};

let w;
const sha = (s) => createHash("sha256").update(s).digest("hex");

beforeEach(async () => {
  w = await makeWorld();
  w.env.TURNSTILE_SECRET_KEY = "synthetic";
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ success: true, keys: [w.keys.jwk] }) });
});
afterEach(() => restoreFetch());

const intake = (who, body) => w.call("api/ops/tickets/index.ts", "onRequestPost", who, { body });
const opsGet = (who, id) => w.call("api/ops/tickets/[ticketId]/index.ts", "onRequestGet", who, { method: "GET", params: { ticketId: id } });
const opsPost = (who, id, body) => w.call("api/ops/tickets/[ticketId]/index.ts", "onRequestPost", who, { body, params: { ticketId: id } });
const opsList = (who) => w.call("api/ops/tickets/index.ts", "onRequestGet", who, { method: "GET" });
async function view(ticket, token) {
  const fn = await handler("api/support/tickets/status.ts", "onRequestGet");
  const r = await fn({ request: new Request(`https://staging.test/api/support/tickets/status?ticket=${ticket}`, { headers: { "x-ticket-token": token } }), env: w.env });
  return { status: r.status, body: await r.json() };
}
const V = { verified: true, verification_method: "whatsapp_number_match" };

test("assisted intake links a real order, records who verified how, returns a one-time code, stores only its hash", async () => {
  const o = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const r = await intake("support", { order_id: o.pub, message: "Login nahi hocche", subject: "Login", ...V });
  assert.equal(r.status, 201);
  assert.equal(r.body.verification, "staff_verified");
  const row = w.db.one("SELECT * FROM support_threads WHERE public_ticket_id=?", r.body.ticket_id);
  assert.equal(row.order_id, o.id);
  assert.equal(row.verified_by, OPERATORS.support.id);
  assert.equal(row.verification_method, "whatsapp_number_match");
  assert.equal(row.channel, "whatsapp_assisted");
  assert.equal(row.access_token_hash, sha(r.body.access_code));
  assert.ok(!JSON.stringify(w.db.rows("SELECT * FROM support_threads")).includes(r.body.access_code));
  // the relayed code actually opens the customer view
  const v = await view(r.body.ticket_id, r.body.access_code);
  assert.equal(v.status, 200);
  assert.equal(v.body.messages[0].from, "you");
});

test("assisted intake refuses unknown orders, missing verification, and writes nothing", async () => {
  const o = w.seedOrder({ status: "delivered" });
  assert.equal((await intake("support", { order_id: "SOS-NOPE-1", message: "x", ...V })).status, 404);
  assert.equal((await intake("support", { order_id: o.pub, message: "x" })).status, 400);
  assert.equal((await intake("support", { order_id: o.pub, message: "x", verification_method: "whatsapp_number_match" })).status, 400);
  assert.equal((await intake("support", { order_id: o.pub, message: "x", verified: true, verification_method: "vibes" })).status, 400);
  assert.equal(w.db.rows("SELECT * FROM support_threads").length, 0);
  assert.equal(w.db.rows("SELECT * FROM orders").length, 1, "no order is ever fabricated");
});

test("customer without any order record gets an unverified ticket with no order data", async () => {
  const r = await intake("support", { message: "Ami ChatGPT Plus kinte chai", category: "order_status" });
  assert.equal(r.status, 201);
  assert.equal(r.body.verification, "unverified");
  const row = w.db.one("SELECT * FROM support_threads WHERE public_ticket_id=?", r.body.ticket_id);
  assert.equal(row.order_id, null);
  assert.equal(row.verified_by, null);
  assert.equal(w.db.rows("SELECT * FROM orders").length, 0);
});

test("only owner/manager/support may run assisted intake; fulfillment, viewer, disabled and anonymous cannot", async () => {
  const o = w.seedOrder({ status: "delivered" });
  for (const who of ["owner", "manager", "support"]) {
    assert.equal((await intake(who, { order_id: o.pub, message: "hi", ...V })).status, 201, who);
  }
  assert.equal((await intake("fulfillA", { message: "hi" })).status, 403);
  assert.equal((await intake("viewer", { message: "hi" })).status, 403);
  assert.ok([401, 403].includes((await intake("gone", { message: "hi" })).status));
  assert.equal((await intake(null, { message: "hi" })).status, 401);
});

test("DB triggers: staff_verified needs actor+method+order; unverified cannot link an order", async () => {
  const o = w.seedOrder({ status: "delivered" });
  const ins = (cols, vals) => w.db.run(`INSERT INTO support_threads(id,${cols},created_at,updated_at) VALUES ('x'||hex(randomblob(4)),${vals},'t','t')`);
  assert.throws(() => ins("order_id,verification_status", `'${o.id}','staff_verified'`), /STAFF_VERIFIED_NEEDS_ACTOR_METHOD_ORDER/);
  assert.throws(() => ins("order_id,verification_status", `'${o.id}','unverified'`), /UNVERIFIED_TICKET_CANNOT_LINK_ORDER/);
  assert.throws(() => ins("category", "'sales_pitch'"));
});

test("categories: subscription support is the default; AI training is a separate category; bad values are refused", async () => {
  const a = await intake("support", { message: "help" });
  assert.equal(w.db.one("SELECT category FROM support_threads WHERE public_ticket_id=?", a.body.ticket_id).category, "subscription_support");
  const b = await intake("support", { message: "AI training info", category: "ai_training_inquiry" });
  assert.equal(w.db.one("SELECT category FROM support_threads WHERE public_ticket_id=?", b.body.ticket_id).category, "ai_training_inquiry");
  assert.equal((await intake("support", { message: "x", category: "hack" })).status, 400);
  const list = await opsList("support");
  assert.deepEqual(new Set(list.body.tickets.map(t => t.category)), new Set(["subscription_support", "ai_training_inquiry"]));
});

test("assignment: owner/manager only, active operator only, recorded in history", async () => {
  const t = (await intake("support", { message: "help" })).body;
  assert.equal((await opsPost("support", t.ticket_id, { assign_to: OPERATORS.manager.id })).status, 403);
  assert.equal((await opsPost("manager", t.ticket_id, { assign_to: "op-ghost" })).status, 404);
  assert.equal((await opsPost("manager", t.ticket_id, { assign_to: OPERATORS.gone.id })).status, 404);
  assert.equal((await opsPost("manager", t.ticket_id, { assign_to: OPERATORS.support.id })).status, 200);
  const d = await opsGet("support", t.ticket_id);
  assert.equal(d.body.ticket.assigned_to, OPERATORS.support.id);
  assert.ok(d.body.messages.some(m => m.type === "assigned"));
});

test("escalation: needs a reason, sets priority 0 and a timestamp, is logged, and stays visible in the list", async () => {
  const t = (await intake("support", { message: "paid but no access" })).body;
  assert.equal((await opsPost("support", t.ticket_id, { escalate: "" })).status, 400);
  const r = await opsPost("support", t.ticket_id, { escalate: "customer paid, call back, number 01712345678" });
  assert.equal(r.status, 200);
  const row = w.db.one("SELECT priority,escalated_at,escalation_reason FROM support_threads WHERE public_ticket_id=?", t.ticket_id);
  assert.equal(row.priority, 0);
  assert.ok(row.escalated_at);
  assert.ok(!row.escalation_reason.includes("01712345678"), "phone numbers are redacted from reasons");
  const list = await opsList("manager");
  assert.equal(list.body.tickets[0].escalated, true);
  assert.equal((await opsPost("viewer", t.ticket_id, { escalate: "x" })).status, 403);
  assert.equal((await opsPost("fulfillA", t.ticket_id, { escalate: "x" })).status, 403);
});

test("rotate_code: new code works, old code stops working, only a hash is stored", async () => {
  const t = (await intake("support", { message: "lost my code" })).body;
  const r = await opsPost("support", t.ticket_id, { rotate_code: true });
  assert.equal(r.status, 200);
  assert.notEqual(r.body.access_code, t.access_code);
  assert.equal((await view(t.ticket_id, t.access_code)).status, 404);
  assert.equal((await view(t.ticket_id, r.body.access_code)).status, 200);
  assert.ok(!JSON.stringify(w.db.rows("SELECT * FROM support_events")).includes(r.body.access_code));
  assert.equal((await opsPost("fulfillA", t.ticket_id, { rotate_code: true })).status, 403);
});

test("closed tickets cannot be escalated, reassigned or have their code rotated", async () => {
  const t = (await intake("support", { message: "done" })).body;
  assert.equal((await opsPost("support", t.ticket_id, { status: "closed" })).status, 200);
  for (const b of [{ escalate: "x" }, { assign_to: OPERATORS.support.id }, { rotate_code: true }]) {
    assert.equal((await opsPost("manager", t.ticket_id, b)).status, 409);
  }
});

test("customer view never exposes verification, escalation, staff ids or order data", async () => {
  const o = w.seedOrder({ status: "delivered" });
  const t = (await intake("support", { order_id: o.pub, message: "hi", ...V })).body;
  await opsPost("support", t.ticket_id, { escalate: "internal note", message: "We are checking" });
  const v = await view(t.ticket_id, t.access_code);
  const s = JSON.stringify(v.body);
  for (const leak of ["internal note", "op-support", "whatsapp_number_match", "staff_verified", o.pub, "Synthetic Customer", "cust@example.test", "assisted_intake"]) {
    assert.ok(!s.includes(leak), leak);
  }
});

test("fulfillment sees only tickets on their own assigned orders; unlinked tickets are invisible to them", async () => {
  const mine = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id });
  const theirs = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillB.id });
  const a = (await intake("support", { order_id: mine.pub, message: "a", ...V })).body;
  const b = (await intake("support", { order_id: theirs.pub, message: "b", ...V })).body;
  const c = (await intake("support", { message: "c" })).body;
  const l = await opsList("fulfillA");
  assert.deepEqual(l.body.tickets.map(t => t.ticket_id), [a.ticket_id]);
  assert.equal((await opsGet("fulfillA", b.ticket_id)).status, 404);
  assert.equal((await opsGet("fulfillA", c.ticket_id)).status, 404);
});

test("per-order open-ticket cap also applies to assisted intake", async () => {
  const o = w.seedOrder({ status: "delivered" });
  for (let i = 0; i < 5; i++) assert.equal((await intake("support", { order_id: o.pub, message: "m" + i, ...V })).status, 201);
  assert.equal((await intake("support", { order_id: o.pub, message: "m6", ...V })).status, 429);
});
