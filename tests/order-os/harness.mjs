// Test harness for the Order OS Pages Functions. Everything here is synthetic:
// in-memory SQLite, generated RSA keys, fake operators and fake orders. No
// network, no Cloudflare binding and no real customer data is touched.
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export const handler = async (rel, name) =>
  (await import(pathToFileURL(resolve(root, "functions", rel)).href))[name];

// ---- D1 adapter over node:sqlite (same semantics for what the code uses) ----
class Statement {
  constructor(d1, sql) { this.d1 = d1; this.sql = sql; this.args = []; }
  bind(...args) { this.args = args; return this; }
  _exec() {
    const stmt = this.d1.db.prepare(this.sql);
    if (/^\s*(select|with)\b/i.test(this.sql)) {
      return { results: stmt.all(...this.args), meta: { changes: 0 } };
    }
    const info = stmt.run(...this.args);
    return { results: [], meta: { changes: Number(info.changes) } };
  }
  async first() { this.d1.reads++; return this.d1.db.prepare(this.sql).get(...this.args) ?? null; }
  async all() { this.d1.reads++; return this._exec(); }
  async run() { return this._exec(); }
}

export class FakeD1 {
  constructor() {
    this.db = new DatabaseSync(":memory:");
    this.db.exec(readFileSync(resolve(root, "ops/order-os/schema.sql"), "utf8"));
    this.reads = 0;
    this.beforeBatch = null; // simulate another writer slipping in between read and write
  }
  prepare(sql) { return new Statement(this, sql); }
  async batch(statements) {
    if (this.beforeBatch) { const hook = this.beforeBatch; this.beforeBatch = null; hook(this.db); }
    this.db.exec("BEGIN");
    try {
      const out = statements.map(s => s._exec());
      this.db.exec("COMMIT");
      return out;
    } catch (e) {
      this.db.exec("ROLLBACK");
      throw e;
    }
  }
  one(sql, ...args) { return this.db.prepare(sql).get(...args); }
  rows(sql, ...args) { return this.db.prepare(sql).all(...args); }
  run(sql, ...args) { return this.db.prepare(sql).run(...args); }
}

// ---- Cloudflare Access JWTs ----
export const TEAM_DOMAIN = "https://saveonsub-test.cloudflareaccess.com";
export const AUD = "test-policy-aud-0123456789";
const enc = new TextEncoder();
const b64u = (bytes) => Buffer.from(bytes).toString("base64url");
const b64uJson = (obj) => b64u(enc.encode(JSON.stringify(obj)));

export async function makeKeys(kid = "kid-1") {
  const pair = await crypto.subtle.generateKey(
    { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
    true, ["sign", "verify"]);
  const jwk = { ...(await crypto.subtle.exportKey("jwk", pair.publicKey)), kid, alg: "RS256", use: "sig" };
  return { privateKey: pair.privateKey, jwk, kid };
}

export async function signJwt(keys, claims = {}, header = {}) {
  const now = Math.floor(Date.now() / 1000);
  const h = { alg: "RS256", kid: keys.kid, typ: "JWT", ...header };
  const p = { iss: TEAM_DOMAIN, aud: [AUD], exp: now + 600, iat: now, sub: "sub-1", type: "app", ...claims };
  const body = `${b64uJson(h)}.${b64uJson(p)}`;
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", keys.privateKey, enc.encode(body));
  return `${body}.${b64u(new Uint8Array(sig))}`;
}

const realFetch = globalThis.fetch;
export function stubJwks(keys, { ok = true, throws = false } = {}) {
  globalThis.fetch = async () => {
    if (throws) throw new Error("network down");
    return { ok, json: async () => ({ keys: [keys.jwk] }) };
  };
}
export const restoreFetch = () => { globalThis.fetch = realFetch; };

// ---- Synthetic operators and orders ----
export const OPERATORS = {
  owner: { id: "op-owner", email: "owner@example.test", role: "owner" },
  manager: { id: "op-manager", email: "manager@example.test", role: "manager" },
  fulfillA: { id: "op-fulfill-a", email: "fa@example.test", role: "fulfillment" },
  fulfillB: { id: "op-fulfill-b", email: "fb@example.test", role: "fulfillment" },
  support: { id: "op-support", email: "support@example.test", role: "support" },
  viewer: { id: "op-viewer", email: "viewer@example.test", role: "viewer" },
  gone: { id: "op-gone", email: "gone@example.test", role: "manager", active: 0 },
};

export async function makeWorld() {
  const keys = await makeKeys();
  stubJwks(keys);
  const db = new FakeD1();
  const ts = "2026-01-01T00:00:00.000Z";
  for (const [name, op] of Object.entries(OPERATORS)) {
    db.run("INSERT INTO operators (id,email,display_name,role,active,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
      op.id, op.email, name, op.role, op.active ?? 1, ts, ts);
  }
  const env = { DB: db, TEAM_DOMAIN, POLICY_AUD: AUD };
  let seq = 0;

  // Creates an order through only legitimate state steps so the DB triggers are
  // never bypassed: payment_review -> (verified) payment_confirmed -> ... target.
  function seedOrder({ status = "payment_review", total = 150000, assignee = null, ref = null,
                       name = "Synthetic Customer", phone = "+8801000000000", email = "cust@example.test" } = {}) {
    seq += 1;
    const id = `ord-${seq}`;
    const pub = `SOS-TEST-${seq}`;
    db.run(`INSERT INTO orders (id,public_order_id,tracking_token_hash,idempotency_key,status,payment_method,payment_reference,
      total_minor,customer_name,customer_phone,customer_email,created_at,updated_at)
      VALUES (?,?,?,?,'payment_review','bkash',?,?,?,?,?,?,?)`,
      id, pub, `hash-${seq}`, `idem-${seq}-xxxxxxxxxxxxxxxx`, ref, total, name, phone, email, ts, ts);
    if (status === "payment_review") return { id, pub };
    if (status === "cancelled") { db.run("UPDATE orders SET status='cancelled' WHERE id=?", id); return { id, pub }; }
    db.run(`INSERT INTO payment_verifications (id,order_id,provider,txn_ref_hash,txn_ref_last4,amount_minor,currency,evidence_ref,verified_by,verified_at)
      VALUES (?,?,?,?,?,?,?,?,?,?)`, `pv-${seq}`, id, "bkash", `txn-hash-${seq}`, "0000", total, "BDT", `stmt:seed-${seq}`, OPERATORS.owner.id, ts);
    for (const step of ["payment_confirmed", "assigned", "fulfilling", "delivered", "support_open", "completed", "refunded"]) {
      if (status === step) {
        db.run("UPDATE orders SET status=?, assigned_operator_id=? WHERE id=?", step, assignee, id);
        return { id, pub };
      }
    }
    throw new Error(`cannot seed status ${status}`);
  }

  async function call(file, exportName, who, { method = "POST", body, params = {}, query = "", headers = {}, token } = {}) {
    const fn = await handler(file, exportName);
    const jwt = token !== undefined ? token : who ? await signJwt(keys, { email: OPERATORS[who].email, sub: `sub-${who}` }) : "";
    const h = { "content-type": "application/json", ...headers };
    if (jwt) h["cf-access-jwt-assertion"] = jwt;
    const request = new Request(`https://staging.test/api/ops${query}`, {
      method, headers: h, body: body === undefined ? undefined : typeof body === "string" ? body : JSON.stringify(body),
    });
    const response = await fn({ request, env, params });
    return { status: response.status, body: await response.json() };
  }

  const order = (pub) => db.one("SELECT * FROM orders WHERE public_order_id=?", pub);
  const events = (id) => db.rows("SELECT * FROM order_events WHERE order_id=? ORDER BY id", id);
  const snapshot = () => JSON.stringify({
    orders: db.rows("SELECT * FROM orders ORDER BY id"),
    events: db.rows("SELECT * FROM order_events ORDER BY id"),
    verifications: db.rows("SELECT * FROM payment_verifications ORDER BY id"),
    reversals: db.rows("SELECT * FROM order_reversals ORDER BY id"),
  });

  const api = {
    status: (who, pub, body, o) => call("api/ops/orders/[orderId]/status.ts", "onRequestPost", who, { body, params: { orderId: pub }, ...o }),
    claim: (who, pub, o) => call("api/ops/orders/[orderId]/claim.ts", "onRequestPost", who, { params: { orderId: pub }, ...o }),
    events: (who, pub, o) => call("api/ops/orders/[orderId]/events.ts", "onRequestGet", who, { method: "GET", params: { orderId: pub }, ...o }),
    list: (who, query = "", o) => call("api/ops/orders/index.ts", "onRequestGet", who, { method: "GET", query, ...o }),
    verify: (who, pub, body, o) => call("api/ops/orders/[orderId]/payment-verification.ts", "onRequestPost", who, { body, params: { orderId: pub }, ...o }),
    reverse: (who, pub, body, o) => call("api/ops/orders/[orderId]/reversal.ts", "onRequestPost", who, { body, params: { orderId: pub }, ...o }),
  };

  return { keys, db, env, seedOrder, order, events, snapshot, api, call };
}
