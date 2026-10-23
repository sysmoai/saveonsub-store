import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { makeWorld, makeKeys, signJwt, stubJwks, restoreFetch, TEAM_DOMAIN, AUD, OPERATORS } from "./harness.mjs";

let w;
beforeEach(async () => { w = await makeWorld(); });
afterEach(() => restoreFetch());

const goodClaims = (who) => ({ email: OPERATORS[who].email, sub: `sub-${who}` });
const listWith = (token, env) => w.api.list(null, "", { token });

test("valid Access JWT for an active operator is accepted", async () => {
  const r = await w.api.list("manager");
  assert.equal(r.status, 200);
  assert.equal(r.body.operator.role, "manager");
});

test("missing token, garbage token and wrong segment count are 401", async () => {
  for (const token of ["", "abc", "a.b", "a.b.c.d", "....", "x".repeat(9000)]) {
    const r = await listWith(token);
    assert.equal(r.status, 401, `token=${token.slice(0, 12)}`);
    assert.equal(r.body.error, "UNAUTHENTICATED");
  }
});

test("wrong issuer is rejected", async () => {
  const token = await signJwt(w.keys, { ...goodClaims("owner"), iss: "https://evil.cloudflareaccess.com" });
  assert.equal((await listWith(token)).status, 401);
});

test("wrong audience is rejected (string and array forms)", async () => {
  for (const aud of ["other-aud", ["other-aud"], [], undefined]) {
    const token = await signJwt(w.keys, { ...goodClaims("owner"), aud });
    assert.equal((await listWith(token)).status, 401, JSON.stringify(aud));
  }
});

test("audience array containing the right audience among others is accepted", async () => {
  const token = await signJwt(w.keys, { ...goodClaims("owner"), aud: ["x", AUD] });
  assert.equal((await listWith(token)).status, 200);
});

test("expired, missing-exp, non-numeric exp and not-yet-valid tokens are rejected", async () => {
  const now = Math.floor(Date.now() / 1000);
  const cases = [{ exp: now - 10 }, { exp: undefined }, { exp: String(now + 600) }, { nbf: now + 3600 }];
  for (const extra of cases) {
    const token = await signJwt(w.keys, { ...goodClaims("owner"), ...extra });
    assert.equal((await listWith(token)).status, 401, JSON.stringify(extra));
  }
});

test("tampered payload (valid-looking, bad signature) is rejected", async () => {
  const token = await signJwt(w.keys, goodClaims("viewer"));
  const [h, , s] = token.split(".");
  const forged = Buffer.from(JSON.stringify({ iss: TEAM_DOMAIN, aud: [AUD], exp: 9999999999, sub: "x", type: "app", email: OPERATORS.owner.email })).toString("base64url");
  assert.equal((await listWith(`${h}.${forged}.${s}`)).status, 401);
});

test("token signed by a different key with the same kid is rejected", async () => {
  const attacker = await makeKeys("kid-1");
  const token = await signJwt(attacker, goodClaims("owner"));
  assert.equal((await listWith(token)).status, 401);
});

test("unknown kid is rejected", async () => {
  const other = await makeKeys("kid-unknown");
  const token = await signJwt(other, goodClaims("owner"));
  assert.equal((await listWith(token)).status, 401);
});

test("alg none / HS256 / missing kid are rejected", async () => {
  for (const header of [{ alg: "none" }, { alg: "HS256" }, { kid: undefined }]) {
    const token = await signJwt(w.keys, goodClaims("owner"), header);
    assert.equal((await listWith(token)).status, 401, JSON.stringify(header));
  }
});

test("service-token style identity (no email / no sub) and non-app type are rejected", async () => {
  for (const claims of [{ email: undefined, sub: "s" }, { email: OPERATORS.owner.email, sub: undefined }, { ...goodClaims("owner"), type: "service" }]) {
    const token = await signJwt(w.keys, claims);
    assert.equal((await listWith(token)).status, 401, JSON.stringify(claims));
  }
});

test("a valid Access identity that is not an operator is 403, not 200", async () => {
  const token = await signJwt(w.keys, { email: "stranger@example.test", sub: "s" });
  const r = await listWith(token);
  assert.equal(r.status, 403);
  assert.equal(r.body.error, "FORBIDDEN");
});

test("a deactivated operator is refused", async () => {
  const r = await w.api.list("gone");
  assert.equal(r.status, 403);
});

test("operator email match is case-insensitive via the verified token", async () => {
  const token = await signJwt(w.keys, { email: "OWNER@Example.TEST", sub: "s" });
  assert.equal((await listWith(token)).status, 200);
});

test("missing Access configuration fails closed with 503", async () => {
  for (const patch of [{ TEAM_DOMAIN: undefined }, { POLICY_AUD: undefined }, { TEAM_DOMAIN: "http://insecure.example" }]) {
    const saved = { ...w.env };
    Object.assign(w.env, patch);
    const r = await w.api.list("owner");
    Object.assign(w.env, saved);
    assert.equal(r.status, 503, JSON.stringify(patch));
    assert.equal(r.body.error, "STAFF_BACKEND_NOT_CONFIGURED");
  }
});

test("missing D1 binding fails closed with 503", async () => {
  const saved = w.env.DB;
  w.env.DB = undefined;
  const r = await w.api.list("owner");
  w.env.DB = saved;
  assert.equal(r.status, 503);
});

test("unreachable JWKS endpoint fails closed with 503, never open", async () => {
  stubJwks(w.keys, { throws: true });
  const r = await w.api.list("owner");
  assert.equal(r.status, 503);
  stubJwks(w.keys, { ok: false });
  assert.equal((await w.api.list("owner")).status, 503);
});

test("error responses never leak internal reason codes", async () => {
  const bad = [await listWith(""), await listWith("a.b.c"), await w.api.list("gone")];
  for (const r of bad) assert.doesNotMatch(JSON.stringify(r.body), /ACCESS_|TOKEN|JWKS|OPERATOR_NOT/);
});

test("denied requests change nothing in the database", async () => {
  const { pub } = w.seedOrder({ status: "payment_review" });
  const before = w.snapshot();
  const seenBefore = w.db.one("SELECT group_concat(coalesce(last_seen_at,'-')) s FROM operators").s;
  await w.api.status(null, pub, { status: "cancelled" }, { token: "bad.token.value" });
  await w.api.claim(null, pub, { token: "" });
  await w.api.verify(null, pub, {}, { token: "x" });
  const expired = await signJwt(w.keys, { ...goodClaims("owner"), exp: 1 });
  await w.api.status(null, pub, { status: "cancelled" }, { token: expired });
  assert.equal(w.snapshot(), before);
  assert.equal(w.db.one("SELECT group_concat(coalesce(last_seen_at,'-')) s FROM operators").s, seenBefore);
});

test("every ops order endpoint refuses unauthenticated callers", async () => {
  const { pub } = w.seedOrder();
  const results = [
    await w.api.list(null), await w.api.events(null, pub), await w.api.status(null, pub, { status: "cancelled" }),
    await w.api.claim(null, pub), await w.api.verify(null, pub, {}), await w.api.reverse(null, pub, {}),
  ];
  for (const r of results) assert.equal(r.status, 401);
});

test("T018-08: a token without a type claim is 401", async () => {
  const token = await signJwt(w.keys, { ...goodClaims("owner"), type: undefined });
  assert.equal((await listWith(token)).status, 401);
});

test("T018-08: TEAM_DOMAIN must be a *.cloudflareaccess.com origin (503 otherwise)", async () => {
  for (const domain of ["https://evil.com", "https://saveonsub.cloudflareaccess.com.evil.com",
                        "https://evil.com/x.cloudflareaccess.com", "https://a.b.cloudflareaccess.com"]) {
    const saved = w.env.TEAM_DOMAIN;
    w.env.TEAM_DOMAIN = domain;
    const r = await w.api.list("owner");
    w.env.TEAM_DOMAIN = saved;
    assert.equal(r.status, 503, domain);
  }
});

test("T018-08: last_seen_at is written at most once per 5 minutes per operator", async () => {
  let writes = 0;
  const prepare = w.db.prepare.bind(w.db);
  w.db.prepare = (sql) => {
    const stmt = prepare(sql);
    if (/^\s*UPDATE operators SET last_seen_at/i.test(sql)) {
      const run = stmt.run.bind(stmt);
      stmt.run = async () => { const r = await run(); writes += r.meta.changes; return r; };
    }
    return stmt;
  };
  assert.equal((await w.api.list("owner")).status, 200);
  assert.equal((await w.api.list("owner")).status, 200);
  assert.equal(writes, 1);
  w.db.run("UPDATE operators SET last_seen_at=? WHERE id=?", new Date(Date.now() - 6 * 60 * 1000).toISOString(), OPERATORS.owner.id);
  assert.equal((await w.api.list("owner")).status, 200);
  assert.equal(writes, 2);
});
