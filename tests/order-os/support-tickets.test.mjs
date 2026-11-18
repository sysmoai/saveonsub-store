// Support tickets on the existing support_threads/support_events tables.
// FakeD1 (in-memory SQLite), synthetic operators/orders/customers only.
// This is NOT a staging or production result: no Cloudflare D1, Turnstile,
// Access MFA or real operator login is involved.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { makeWorld, restoreFetch, handler, OPERATORS } from "./harness.mjs";

console.warn = () => {};
console.error = () => {};

let w;
const sha = (s) => createHash("sha256").update(s).digest("hex");
const TOKEN_A = "a".repeat(44);
const TOKEN_B = "b".repeat(44);

beforeEach(async () => {
  w = await makeWorld();
  w.env.TURNSTILE_SECRET_KEY = "synthetic";
  // one stub answers both Turnstile (success) and Access JWKS (keys)
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ success: true, keys: [w.keys.jwk] }) });
});
afterEach(() => restoreFetch());

function order(pub, token, over = {}) {
  const o = w.seedOrder({ status: "delivered", assignee: OPERATORS.fulfillA.id, ...over });
  w.db.run("UPDATE orders SET tracking_token_hash=? WHERE id=?", sha(token), o.id);
  return o;
}

async function pub(file, name, { method = "POST", body, headers = {}, query = "" } = {}) {
  const fn = await handler(file, name);
  const request = new Request(`https://staging.test/api/support/tickets${query}`, {
    method, headers: { "content-type": "application/json", ...headers }, body: body === undefined ? undefined : JSON.stringify(body),
  });
  const r = await fn({ request, env: w.env });
  return { status: r.status, text: await r.clone().text(), body: await r.json() };
}
const create = (b) => pub("api/support/tickets/index.ts", "onRequestPost", { body: { turnstile_token: "t", ...b } });
const view = (ticket, token) => pub("api/support/tickets/status.ts", "onRequestGet", { method: "GET", query: `?ticket=${encodeURIComponent(ticket)}`, headers: token === undefined ? {} : { "x-ticket-token": token } });
const cReply = (ticket, token, message) => pub("api/support/tickets/status.ts", "onRequestPost", { body: { ticket, message }, headers: { "x-ticket-token": token } });
const opsList = (who, query = "") => w.call("api/ops/tickets/index.ts", "onRequestGet", who, { method: "GET", query });
const opsGet = (who, id) => w.call("api/ops/tickets/[ticketId]/index.ts", "onRequestGet", who, { method: "GET", params: { ticketId: id } });
const opsPost = (who, id, body) => w.call("api/ops/tickets/[ticketId]/index.ts", "onRequestPost", who, { body, params: { ticketId: id } });

test("create: ticket is bound to the order by its tracking token; only a hash of the access token is stored", async () => {
  order(null, TOKEN_A);
  const r = await create({ tracking_token: TOKEN_A, subject: "Cannot log in", message: "Hello, I cannot log in" });
  assert.equal(r.status, 201);
  assert.match(r.body.ticket_id, /^SOS-T-[A-Z2-9]{12}$/);
  assert.ok(r.body.access_token.length >= 40);
  const row = w.db.one("SELECT * FROM support_threads WHERE public_ticket_id=?", r.body.ticket_id);
  assert.equal(row.access_token_hash, sha(r.body.access_token));
  const dump = JSON.stringify(w.db.rows("SELECT * FROM support_threads")) + JSON.stringify(w.db.rows("SELECT * FROM support_events"));
  assert.ok(!dump.includes(r.body.access_token), "raw access token must never be stored");
  assert.equal(w.db.rows("SELECT * FROM support_events").length, 1);
});

test("create: bot check is required and enforced; missing backend config fails closed", async () => {
  order(null, TOKEN_A);
  const noTok = await pub("api/support/tickets/index.ts", "onRequestPost", { body: { tracking_token: TOKEN_A, message: "hi" } });
  assert.equal(noTok.status, 400);
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ success: false }) });
  const bad = await create({ tracking_token: TOKEN_A, message: "hi" });
  assert.equal(bad.status, 403);
  delete w.env.TURNSTILE_SECRET_KEY;
  assert.equal((await create({ tracking_token: TOKEN_A, message: "hi" })).status, 503);
  assert.equal(w.db.rows("SELECT * FROM support_threads").length, 0);
});

test("create: unknown, short or malformed tracking tokens all get the same 404 and write nothing", async () => {
  order(null, TOKEN_A);
  const a = await create({ tracking_token: "z".repeat(44), message: "hi" });
  const b = await create({ tracking_token: "short", message: "hi" });
  const c = await create({ tracking_token: "x".repeat(300), message: "hi" });
  for (const r of [a, b, c]) assert.equal(r.status, 404);
  assert.equal(a.text, b.text);
  assert.equal(b.text, c.text);
  assert.equal(w.db.rows("SELECT * FROM support_threads").length, 0);
});

test("privacy: stored text is redacted (passwords, OTP, emails, numbers, links)", async () => {
  order(null, TOKEN_A);
  const msg = "my password is hunter2 and OTP: 123456, mail me at real@example.test or +8801711223344, shot https://wa.me/x/img.png";
  const r = await create({ tracking_token: TOKEN_A, subject: "pin 9999", message: msg });
  assert.equal(r.status, 201);
  const stored = w.db.one("SELECT body_redacted FROM support_events").body_redacted + w.db.one("SELECT subject FROM support_threads").subject;
  for (const leak of ["hunter2", "123456", "real@example.test", "01711223344", "wa.me", "9999"]) assert.ok(!stored.includes(leak), leak);
  assert.ok(stored.includes("[redacted]") && stored.includes("[email]") && stored.includes("[link]") && stored.includes("[number]"));
});

test("anti-enumeration: unknown id, wrong token and another customer's token are byte-identical 404s", async () => {
  order(null, TOKEN_A); order(null, TOKEN_B);
  const ta = (await create({ tracking_token: TOKEN_A, message: "A secret question" })).body;
  const tb = (await create({ tracking_token: TOKEN_B, message: "B secret question" })).body;
  const probes = [
    await view("SOS-T-NOSUCHTICKET", ta.access_token),
    await view(ta.ticket_id, "w".repeat(44)),
    await view(ta.ticket_id, tb.access_token), // customer B's token against customer A's ticket
    await view(tb.ticket_id, ta.access_token),
    await view(ta.ticket_id, undefined),
    await view(ta.ticket_id, "short"),
  ];
  for (const p of probes) { assert.equal(p.status, 404); assert.equal(p.text, probes[0].text); }
  const own = await view(ta.ticket_id, ta.access_token);
  assert.equal(own.status, 200);
  assert.deepEqual(own.body.messages.map(m => m.body), ["A secret question"]);
  assert.ok(!own.text.includes("B secret question"));
});

test("customer view never exposes operator identity, order internals or the token hash", async () => {
  order(null, TOKEN_A);
  const t = (await create({ tracking_token: TOKEN_A, message: "hello" })).body;
  assert.equal((await opsPost("support", t.ticket_id, { message: "We are checking" })).status, 200);
  const v = await view(t.ticket_id, t.access_token);
  assert.deepEqual(v.body.messages.map(m => m.from), ["you", "support"]);
  for (const leak of ["op-support", "support@example.test", "access_token_hash", "tracking_token_hash", "ord-", "customer_phone", "payment"]) {
    assert.ok(!v.text.includes(leak), leak);
  }
});

test("customer can reply; a closed ticket refuses further messages from both sides", async () => {
  order(null, TOKEN_A);
  const t = (await create({ tracking_token: TOKEN_A, message: "hello" })).body;
  assert.equal((await opsPost("support", t.ticket_id, { message: "Try again" })).status, 200);
  assert.equal(w.db.one("SELECT status FROM support_threads").status, "waiting_customer");
  assert.equal((await cReply(t.ticket_id, t.access_token, "still broken")).status, 200);
  assert.equal(w.db.one("SELECT status FROM support_threads").status, "waiting_staff");
  assert.equal((await opsPost("manager", t.ticket_id, { status: "closed" })).status, 200);
  assert.equal((await cReply(t.ticket_id, t.access_token, "one more")).status, 409);
  assert.equal((await opsPost("support", t.ticket_id, { message: "late" })).status, 409);
  assert.throws(() => w.db.run("UPDATE support_threads SET status='open' WHERE public_ticket_id=?", t.ticket_id), /TICKET_CLOSED_IMMUTABLE/);
});

test("abuse: more than five open tickets on one order are refused", async () => {
  order(null, TOKEN_A);
  for (let i = 0; i < 5; i++) assert.equal((await create({ tracking_token: TOKEN_A, message: `q${i}` })).status, 201);
  assert.equal((await create({ tracking_token: TOKEN_A, message: "q6" })).status, 429);
});

test("staff RBAC: unauthenticated 401, deactivated/viewer refused, token-less never reads", async () => {
  order(null, TOKEN_A);
  const t = (await create({ tracking_token: TOKEN_A, message: "hello" })).body;
  assert.equal((await opsList(undefined)).status, 401);
  assert.equal((await opsGet(undefined, t.ticket_id)).status, 401);
  assert.equal((await opsPost(undefined, t.ticket_id, { message: "x" })).status, 401);
  assert.equal((await opsList("gone")).status, 403);
  for (const f of [() => opsList("viewer"), () => opsGet("viewer", t.ticket_id), () => opsPost("viewer", t.ticket_id, { message: "x" })]) {
    assert.equal((await f()).status, 403);
  }
});

test("staff RBAC: fulfillment sees only tickets on orders assigned to them and cannot reply", async () => {
  order(null, TOKEN_A);                                              // assigned to fulfillA
  order(null, TOKEN_B, { assignee: OPERATORS.fulfillB.id });         // assigned to fulfillB
  const ta = (await create({ tracking_token: TOKEN_A, message: "mine" })).body;
  const tb = (await create({ tracking_token: TOKEN_B, message: "theirs" })).body;
  const list = await opsList("fulfillA");
  assert.deepEqual(list.body.tickets.map(x => x.ticket_id), [ta.ticket_id]);
  assert.equal((await opsGet("fulfillA", ta.ticket_id)).status, 200);
  const other = await opsGet("fulfillA", tb.ticket_id);
  const unknown = await opsGet("fulfillA", "SOS-T-NOSUCHTICKET");
  assert.equal(other.status, 404);
  assert.deepEqual(other.body, unknown.body); // another operator's ticket looks like a missing one
  assert.equal((await opsPost("fulfillA", ta.ticket_id, { message: "x" })).status, 403);
  assert.equal(w.db.rows("SELECT * FROM support_events WHERE actor_type='operator'").length, 0);
});

test("staff privacy: contact data follows the existing role rules; token hash and internal ids never leave", async () => {
  const o = order(null, TOKEN_A, { name: "Rahim Uddin", phone: "+8801711223344", email: "real.looking@example.test" });
  w.db.run("UPDATE orders SET status='payment_review', assigned_operator_id=NULL WHERE id=?", o.id); // support has no relation yet
  const t = (await create({ tracking_token: TOKEN_A, message: "hello" })).body;
  const owner = await opsGet("owner", t.ticket_id);
  assert.equal(owner.body.ticket.customer_phone, "+8801711223344");
  const sup = await opsGet("support", t.ticket_id);
  assert.equal(sup.body.ticket.customer_phone, null);
  assert.equal(sup.body.ticket.customer_email, null);
  assert.equal(sup.body.ticket.customer_name, "R.");
  for (const r of [owner, sup, await opsList("owner")]) {
    for (const leak of ["access_token_hash", "tracking_token_hash", sha(TOKEN_A), "ord-"]) assert.ok(!JSON.stringify(r.body).includes(leak), leak);
  }
});

test("staff can reply and set a valid status; invalid status and empty actions change nothing", async () => {
  order(null, TOKEN_A);
  const t = (await create({ tracking_token: TOKEN_A, message: "hello" })).body;
  const before = w.db.rows("SELECT * FROM support_events").length;
  assert.equal((await opsPost("support", t.ticket_id, { status: "bogus" })).status, 400);
  assert.equal((await opsPost("support", t.ticket_id, {})).status, 400);
  assert.equal(w.db.rows("SELECT * FROM support_events").length, before);
  const ok = await opsPost("support", t.ticket_id, { message: "Password is abc123, please change it", status: "resolved" });
  assert.equal(ok.status, 200);
  assert.equal(ok.body.status, "resolved");
  const stored = w.db.rows("SELECT body_redacted FROM support_events WHERE event_type='staff_reply'")[0].body_redacted;
  assert.ok(!stored.includes("abc123"));
});

test("history is append-only at the database level", async () => {
  order(null, TOKEN_A);
  await create({ tracking_token: TOKEN_A, message: "hello" });
  assert.throws(() => w.db.run("UPDATE support_events SET body_redacted='edited'"), /SUPPORT_EVENTS_APPEND_ONLY/);
  assert.throws(() => w.db.run("DELETE FROM support_events"), /SUPPORT_EVENTS_APPEND_ONLY/);
});

test("no second ticket schema: the new migration only extends support_threads and support_events", async () => {
  const tables = w.db.rows("SELECT name FROM sqlite_master WHERE type='table' AND lower(name) LIKE '%ticket%'");
  assert.deepEqual(tables, []);
});
