// Synthetic, in-memory migration compatibility for a new *full* SaveOnSub D1.
// No Cloudflare bindings, customer data or remote database is accessed.
// Checks the common Order OS + commerce + business + support stack together.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const migrations = [
  "ops/order-os/schema.sql",
  "ops/commerce/001_catalog_content_foundation.sql",
  "ops/order-os/business-schema.sql",
  "ops/order-os/lifecycle-finance-schema.sql",
  "ops/order-os/support-tickets-schema.sql",
  "ops/order-os/support-tickets-intake-schema.sql",
];

test("fresh full-stack staging D1 accepts the documented six SQL files in order", () => {
  const db = new DatabaseSync(":memory:");
  try {
    db.exec("PRAGMA foreign_keys=ON");
    for (const rel of migrations) {
      assert.doesNotThrow(() => db.exec(readFileSync(resolve(root, rel), "utf8")), rel);
    }
    const tables = new Set(db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all().map(r => r.name));
    for (const table of [
      "operators", "orders", "order_events", "support_threads", "support_events",
      "commerce_products", "commerce_plans", "business_records",
      "order_costs", "order_refunds", "order_service_periods",
    ]) assert.ok(tables.has(table), `missing table ${table}`);

    const columns = new Set(db.prepare("PRAGMA table_info(support_threads)").all().map(c => c.name));
    for (const col of [
      "public_ticket_id", "access_token_hash", "category", "verification_status",
      "verification_method", "verified_by", "verified_at", "channel",
      "escalated_at", "escalation_reason", "assigned_operator_id",
    ]) assert.ok(columns.has(col), `missing support_threads.${col}`);

    const fkFailures = db.prepare("PRAGMA foreign_key_check").all();
    assert.deepEqual(fkFailures, [], "fresh D1 has no invalid references");

    const triggers = new Set(db.prepare("SELECT name FROM sqlite_master WHERE type='trigger'").all().map(r => r.name));
    for (const name of ["trg_support_events_no_update", "trg_support_events_no_delete",
       "trg_support_threads_closed_immutable", "trg_support_verified_needs_actor",
       "trg_support_unverified_no_order"]) assert.ok(triggers.has(name), `missing trigger ${name}`);
  } finally { db.close(); }
});

test("ticket ALTER migrations are non-idempotent and must not be replayed against existing D1", () => {
  const db = new DatabaseSync(":memory:");
  try {
    db.exec(readFileSync(resolve(root, "ops/order-os/schema.sql"), "utf8"));
    const migration = readFileSync(resolve(root, "ops/order-os/support-tickets-schema.sql"), "utf8");
    db.exec(migration);
    assert.throws(() => db.exec(migration), /duplicate column name/i);
  } finally { db.close(); }
});
