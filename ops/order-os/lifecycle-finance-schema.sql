-- SaveOnSub Order OS: per-order cost (G3), refund evidence (G6) and service
-- period / renewal tracking (G4). Private SaveOnSub D1 only.
-- Apply AFTER schema.sql (and independently of business-schema.sql). Additive and
-- idempotent: creates new tables only and never rewrites existing rows.
PRAGMA foreign_keys = ON;

-- G3. What fulfilling an order actually cost (supplier seat, account, fee).
-- Append-only: a mistake is fixed with a 'correction' row (signed amount),
-- never by editing or deleting. Owner-only through the API.
CREATE TABLE IF NOT EXISTS order_costs (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  entry_type TEXT NOT NULL CHECK (entry_type IN ('cost','correction')),
  category TEXT NOT NULL CHECK (category IN ('supplier','payment_fee','other')),
  supplier_label TEXT NOT NULL CHECK (length(supplier_label) BETWEEN 2 AND 80),
  amount_minor INTEGER NOT NULL CHECK (amount_minor <> 0),
  currency TEXT NOT NULL DEFAULT 'BDT' CHECK (currency = 'BDT'),
  evidence_ref TEXT CHECK (evidence_ref IS NULL OR evidence_ref LIKE 'r2:sos/private/%' OR evidence_ref LIKE 'stmt:%'),
  note TEXT CHECK (note IS NULL OR length(note) <= 300),
  recorded_by TEXT NOT NULL REFERENCES operators(id),
  created_at TEXT NOT NULL,
  CHECK (entry_type = 'correction' OR amount_minor > 0)
);
CREATE INDEX IF NOT EXISTS idx_order_costs_order ON order_costs(order_id, created_at);
CREATE TRIGGER IF NOT EXISTS trg_order_costs_no_update BEFORE UPDATE ON order_costs
BEGIN SELECT RAISE(ABORT, 'COST_LEDGER_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS trg_order_costs_no_delete BEFORE DELETE ON order_costs
BEGIN SELECT RAISE(ABORT, 'COST_LEDGER_IMMUTABLE'); END;

-- G6. Money actually sent back to the customer when an order is refunded.
-- Written in the same guarded batch as the status change to 'refunded'.
CREATE TABLE IF NOT EXISTS order_refunds (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
  currency TEXT NOT NULL DEFAULT 'BDT' CHECK (currency = 'BDT'),
  channel TEXT NOT NULL CHECK (channel IN ('bkash','nagad','rocket','bank_transfer','other')),
  evidence_ref TEXT NOT NULL CHECK (evidence_ref LIKE 'r2:sos/private/%' OR evidence_ref LIKE 'stmt:%'),
  recorded_by TEXT NOT NULL REFERENCES operators(id),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_refunds_order ON order_refunds(order_id);
CREATE TRIGGER IF NOT EXISTS trg_order_refunds_no_update BEFORE UPDATE ON order_refunds
BEGIN SELECT RAISE(ABORT, 'REFUND_LEDGER_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS trg_order_refunds_no_delete BEFORE DELETE ON order_refunds
BEGIN SELECT RAISE(ABORT, 'REFUND_LEDGER_IMMUTABLE'); END;

-- G4. When the delivered service ends, so renewals can be followed up.
-- One current row per order; changes are recorded as order_events.
CREATE TABLE IF NOT EXISTS order_service_periods (
  order_id TEXT PRIMARY KEY REFERENCES orders(id) ON DELETE RESTRICT,
  service_starts_on TEXT NOT NULL CHECK (service_starts_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  service_ends_on TEXT NOT NULL CHECK (service_ends_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  set_by TEXT NOT NULL REFERENCES operators(id),
  updated_at TEXT NOT NULL,
  CHECK (service_ends_on > service_starts_on)
);
CREATE INDEX IF NOT EXISTS idx_service_periods_end ON order_service_periods(service_ends_on);
