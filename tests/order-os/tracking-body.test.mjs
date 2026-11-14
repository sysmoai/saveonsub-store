// Confidentiality regression for Order OS tracking bearer secrets.
// Synthetic in-memory SQLite only; no real orders, tokens or network calls.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { makeWorld, handler, restoreFetch } from "./harness.mjs";

const TOKEN = "s".repeat(48);
let w;
beforeEach(async () => { w = await makeWorld(); });
afterEach(() => restoreFetch());

const run = async (method, url, body, env = w.env) => {
  const fn = await handler("api/orders/track.ts", method === "POST" ? "onRequestPost" : "onRequestGet");
  const request = new Request(url, {
    method,
    ...(method === "POST" ? {
      headers: { "content-type": "application/json" },
      body: typeof body === "string" ? body : JSON.stringify(body),
    } : {}),
  });
  const response = await fn({ request, env });
  return { status: response.status, headers: response.headers, body: await response.json() };
};
const url = "https://staging.test/api/orders/track";

test("POST body token retrieves only redacted order status and not contact or hashes", async () => {
  const order = w.seedOrder();
  w.db.run("UPDATE orders SET tracking_token_hash=? WHERE id=?",
    createHash("sha256").update(TOKEN).digest("hex"), order.id);
  const out = await run("POST", url, { tracking_token: TOKEN });
  assert.equal(out.status, 200);
  assert.equal(out.body.order_id, order.pub);
  assert.equal(out.body.status, "payment_review");
  assert.equal(out.headers.get("cache-control"), "no-store");
  const serialized = JSON.stringify(out.body);
  for (const leak of [TOKEN, "tracking_token_hash", "customer_phone", "customer_email", "payment_reference"]) {
    assert.ok(!serialized.includes(leak), leak);
  }
});

test("GET query token never authenticates, redirects, echoes or reads database", async () => {
  const initial = w.db.reads;
  const out = await run("GET", url + "?token=" + TOKEN, undefined);
  assert.equal(out.status, 405);
  assert.equal(out.headers.get("allow"), "POST");
  assert.ok(!JSON.stringify(out.body).includes(TOKEN));
  assert.equal(w.db.reads, initial);
  assert.equal(out.headers.get("cache-control"), "no-store");
});

test("POST refuses any query bearer token even if JSON body is valid", async () => {
  const initial = w.db.reads;
  const a = await run("POST", url + "?token=" + TOKEN, { tracking_token: TOKEN });
  const b = await run("POST", url + "?tracking_token=" + TOKEN, { tracking_token: TOKEN });
  assert.equal(a.status, 400);
  assert.equal(b.status, 400);
  assert.deepEqual(a.body, b.body);
  assert.equal(w.db.reads, initial);
});

test("short, absent, malformed JSON and unknown tokens cannot expose an order", async () => {
  for (const body of [{}, { tracking_token: "short" }, { tracking_token: 42 }, "[not-json"]) {
    const r = await run("POST", url, body);
    assert.equal(r.status, 400);
  }
  const unknown = await run("POST", url, { tracking_token: "z".repeat(48) });
  assert.equal(unknown.status, 404);
  assert.deepEqual(unknown.body, { error: "ORDER_NOT_FOUND" });
});

test("missing D1 binding fails closed without accepting body secrets in URL", async () => {
  const out = await run("POST", url, { tracking_token: TOKEN }, {});
  assert.equal(out.status, 503);
  assert.equal(out.body.error, "ORDER_BACKEND_NOT_CONFIGURED");
});
