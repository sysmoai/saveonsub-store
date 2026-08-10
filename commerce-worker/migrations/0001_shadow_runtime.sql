-- SAVEONSUB commerce shadow schema v1
-- No customer PII, payment destination, or production order table is created in
-- this migration. This phase exists only to validate server-authoritative plan
-- eligibility and price quoting once approved runtime rows are explicitly loaded.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plan_runtime (
  plan_id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  commercial_state TEXT NOT NULL DEFAULT 'unknown'
    CHECK (commercial_state IN ('allowed', 'direct_provider_only', 'blocked', 'unknown')),
  price_bdt INTEGER
    CHECK (price_bdt IS NULL OR price_bdt >= 0),
  currency TEXT NOT NULL DEFAULT 'BDT'
    CHECK (currency = 'BDT'),
  effective_from TEXT,
  effective_to TEXT,
  authority_ref TEXT,
  source_sha256 TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_plan_runtime_product ON plan_runtime(product_id);
CREATE INDEX IF NOT EXISTS idx_plan_runtime_state ON plan_runtime(commercial_state);

CREATE TABLE IF NOT EXISTS quote_audit (
  request_id TEXT PRIMARY KEY,
  result_code TEXT NOT NULL,
  item_count INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
  total_bdt INTEGER CHECK (total_bdt IS NULL OR total_bdt >= 0),
  source_sha256 TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  detail_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO schema_meta(key, value, updated_at)
VALUES ('schema_version', '1-shadow-runtime', CURRENT_TIMESTAMP);
