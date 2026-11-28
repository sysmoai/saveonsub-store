// Origin rule on the Order OS catalog and media write handlers (2026-11-26).
// A signed-in operator's browser must not be usable from another origin to
// create a catalog draft or upload media. Synthetic data only: in-memory
// SQLite, an in-memory bucket, generated keys and fake operators.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { makeWorld, restoreFetch, OPERATORS, handler, signJwt } from "./harness.mjs";

console.warn = () => {};
console.error = () => {};

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SELF = "https://staging.test";
const FOREIGN = "https://evil.example";

class FakeBucket {
  constructor() { this.objects = new Map(); this.puts = 0; }
  async put(key, value) { this.puts += 1; this.objects.set(key, value); }
  async get(key) { return this.objects.has(key) ? { body: this.objects.get(key) } : null; }
  async delete(key) { this.objects.delete(key); }
}

const PNG = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 0]);
const MP4 = new Uint8Array([0, 0, 0, 24, 0x66, 0x74, 0x79, 0x70, 0x69, 0x73, 0x6f, 0x6d, 0, 0, 0, 0]);
const DRAFT = { slug: "synthetic-product", title: "Synthetic Product", category: "testing", kind: "subscription" };

let w, bucket, env;
beforeEach(async () => {
  w = await makeWorld();
  w.db.db.exec(readFileSync(resolve(root, "ops/commerce/001_catalog_content_foundation.sql"), "utf8"));
  bucket = new FakeBucket();
  env = { ...w.env, MEDIA_BUCKET: bucket };
});
afterEach(() => restoreFetch());

// One request to a write handler. `origin` null means "no Origin header" (curl, server-to-server).
async function post(file, who, { origin = null, type, body, extra = {} }) {
  const fn = await handler(file, "onRequestPost");
  const headers = { "content-type": type, ...extra };
  if (who) headers["cf-access-jwt-assertion"] = await signJwt(w.keys, { email: OPERATORS[who].email, sub: `sub-${who}` });
  if (origin) headers.origin = origin;
  const request = new Request(`${SELF}/api/ops/x`, { method: "POST", headers, body });
  const response = await fn({ request, env, params: {} });
  return { status: response.status, body: await response.json() };
}

const catalog = (who, origin, draft = DRAFT) =>
  post("api/ops/catalog/index.ts", who, { origin, type: "application/json", body: JSON.stringify(draft) });
const image = (who, origin) =>
  post("api/ops/media/index.ts", who, { origin, type: "image/png", body: PNG, extra: { "x-sos-title": "Synthetic image" } });
const video = (who, origin) =>
  post("api/ops/media/videos/index.ts", who, { origin, type: "video/mp4", body: MP4, extra: { "x-sos-title": "Synthetic video" } });

const count = (table) => w.db.one(`SELECT COUNT(*) n FROM ${table}`).n;

test("ORIGIN-01: a foreign origin cannot create a catalog draft, even as owner", async () => {
  const r = await catalog("owner", FOREIGN);
  assert.equal(r.status, 403);
  assert.equal(r.body.error, "FORBIDDEN_ORIGIN");
  assert.equal(count("commerce_products"), 0);
  assert.equal(count("commerce_audit_events"), 0);
});

test("ORIGIN-02: a foreign origin cannot upload an image or a video; nothing is stored", async () => {
  for (const send of [image, video]) {
    const r = await send("owner", FOREIGN);
    assert.equal(r.status, 403);
    assert.equal(r.body.error, "FORBIDDEN_ORIGIN");
  }
  assert.equal(bucket.puts, 0);
  assert.equal(count("commerce_media_assets"), 0);
  assert.equal(count("commerce_audit_events"), 0);
});

test("ORIGIN-03: same-origin and no-Origin requests still work (the rule does not over-block)", async () => {
  const same = await catalog("manager", SELF);
  assert.equal(same.status, 201, JSON.stringify(same.body));
  const bare = await catalog("manager", null, { ...DRAFT, slug: "synthetic-product-2" });
  assert.equal(bare.status, 201, JSON.stringify(bare.body));
  assert.equal(count("commerce_products"), 2);

  const img = await image("manager", SELF);
  assert.equal(img.status, 201, JSON.stringify(img.body));
  const vid = await video("manager", null);
  assert.equal(vid.status, 201, JSON.stringify(vid.body));
  assert.equal(bucket.puts, 2);
  assert.equal(count("commerce_media_assets"), 2);
});

test("ORIGIN-04: authentication and role checks still answer first for a foreign origin", async () => {
  for (const send of [catalog, image, video]) {
    assert.equal((await send(null, FOREIGN)).status, 401);
    const viewer = await send("viewer", FOREIGN);
    assert.equal(viewer.status, 403);
    assert.notEqual(viewer.body.error, "FORBIDDEN_ORIGIN");
  }
  assert.equal(bucket.puts, 0);
});
