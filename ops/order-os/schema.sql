PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS operators (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('owner','manager','fulfillment','support','viewer')),
  active INTEGER NOT NULL DEFAULT 1,
  last_seen_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  public_order_id TEXT NOT NULL UNIQUE,
  tracking_token_hash TEXT NOT NULL UNIQUE,
  idempotency_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN (
    'submitted','payment_review','payment_confirmed','assigned','fulfilling',
    'delivered','support_open','completed','cancelled','refunded'
  )),
  priority INTEGER NOT NULL DEFAULT 1 CHECK (priority BETWEEN 0 AND 3),
  payment_method TEXT,
  payment_reference TEXT,
  currency TEXT NOT NULL DEFAULT 'BDT',
  total_minor INTEGER NOT NULL CHECK (total_minor >= 0),
  customer_name TEXT,
  customer_phone TEXT,
  customer_email TEXT,
  customer_locale TEXT,
  source TEXT NOT NULL DEFAULT 'website',
  assigned_operator_id TEXT REFERENCES operators(id) ON DELETE SET NULL,
  sla_due_at TEXT,
  claimed_at TEXT,
  payment_confirmed_at TEXT,
  delivered_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status_priority_created
  ON orders(status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_operator_status
  ON orders(assigned_operator_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_sla
  ON orders(status, priority, sla_due_at);

CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  product_name_snapshot TEXT NOT NULL,
  plan_name_snapshot TEXT NOT NULL,
  unit_price_minor INTEGER NOT NULL CHECK (unit_price_minor >= 0),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  access_type_snapshot TEXT,
  support_terms_snapshot TEXT
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

CREATE TABLE IF NOT EXISTS order_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('customer','operator','system','agent')),
  actor_id TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_events_order_created
  ON order_events(order_id, created_at);

CREATE TABLE IF NOT EXISTS notification_outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT REFERENCES orders(id) ON DELETE CASCADE,
  channel TEXT NOT NULL,
  destination_key TEXT NOT NULL,
  template_key TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 1 CHECK (priority BETWEEN 0 AND 3),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','sending','sent','failed','dead')),
  attempt_count INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT NOT NULL,
  last_error TEXT,
  sent_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outbox_due
  ON notification_outbox(status, priority, next_attempt_at);

-- Exactly one paid-priority message per verified order and destination.
-- A customer-submitted claim must never emit this template.
CREATE UNIQUE INDEX IF NOT EXISTS ux_paid_outbox_once
  ON notification_outbox(order_id, template_key, destination_key)
  WHERE template_key='paid_order_priority';

CREATE TABLE IF NOT EXISTS support_threads (
  id TEXT PRIMARY KEY,
  order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','waiting_customer','waiting_staff','resolved','closed')),
  priority INTEGER NOT NULL DEFAULT 2 CHECK (priority BETWEEN 0 AND 3),
  assigned_operator_id TEXT REFERENCES operators(id) ON DELETE SET NULL,
  subject TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS support_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id TEXT NOT NULL REFERENCES support_threads(id) ON DELETE CASCADE,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('customer','operator','system','agent')),
  actor_id TEXT,
  event_type TEXT NOT NULL,
  body_redacted TEXT,
  created_at TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Payment provenance, terminal-state immutability and audit integrity.
-- Additive and idempotent. Application code enforces the same rules; these
-- constraints are the last line of defence if a code path is ever wrong.
-- ---------------------------------------------------------------------------

-- A human operator's attestation that settled money matching this order was
-- seen in the provider's merchant statement. A customer-submitted reference
-- (orders.payment_reference) is a claim, never proof. Only a hash and the last
-- four characters of the provider reference are stored (duplicate detection
-- needs no more); full references stay in the provider's own records.
CREATE TABLE IF NOT EXISTS payment_verifications (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  provider TEXT NOT NULL CHECK (provider IN ('bkash','nagad','rocket','bank_transfer','other')),
  txn_ref_hash TEXT NOT NULL,
  txn_ref_last4 TEXT NOT NULL,
  amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
  currency TEXT NOT NULL,
  matches_customer_reference INTEGER NOT NULL DEFAULT 0,
  evidence_note TEXT,
  -- Settlement evidence (private R2 object or merchant statement id), never a screenshot URL.
  evidence_ref TEXT NOT NULL CHECK (evidence_ref LIKE 'r2:sos/private/%' OR evidence_ref LIKE 'stmt:%'),
  receipt_source TEXT CHECK (receipt_source IN ('receiving_account_history','bank_statement')),
  verified_by TEXT NOT NULL REFERENCES operators(id),
  verified_at TEXT NOT NULL,
  voided_at TEXT,
  voided_by TEXT REFERENCES operators(id),
  void_reason TEXT
);

-- One provider reference can back one order, and an order has one active verification.
CREATE UNIQUE INDEX IF NOT EXISTS ux_payment_ref_active
  ON payment_verifications(provider, txn_ref_hash) WHERE voided_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_payment_order_active
  ON payment_verifications(order_id) WHERE voided_at IS NULL;

-- Explicit, owner-authorised exception for leaving a terminal state
-- (cancelled / refunded). One unapplied row permits exactly one such change.
CREATE TABLE IF NOT EXISTS order_reversals (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  from_status TEXT NOT NULL CHECK (from_status IN ('cancelled','refunded')),
  to_status TEXT NOT NULL,
  reason TEXT NOT NULL,
  authorized_by TEXT NOT NULL REFERENCES operators(id),
  created_at TEXT NOT NULL,
  applied_at TEXT
);

-- Orders can only be created in an unpaid state.
CREATE TRIGGER IF NOT EXISTS trg_orders_insert_unpaid_only
BEFORE INSERT ON orders
WHEN NEW.status NOT IN ('submitted','payment_review')
BEGIN
  SELECT RAISE(ABORT, 'ORDER_MUST_START_UNPAID');
END;

-- cancelled / refunded never change status without a matching, unapplied reversal.
CREATE TRIGGER IF NOT EXISTS trg_orders_terminal_immutable
BEFORE UPDATE OF status ON orders
WHEN OLD.status IN ('cancelled','refunded')
 AND NEW.status <> OLD.status
 AND NOT EXISTS (
   SELECT 1 FROM order_reversals r
   WHERE r.order_id = OLD.id AND r.from_status = OLD.status
     AND r.to_status = NEW.status AND r.applied_at IS NULL)
BEGIN
  SELECT RAISE(ABORT, 'TERMINAL_ORDER_IMMUTABLE');
END;

-- No paid-or-later state without an active verification of the exact order total.
CREATE TRIGGER IF NOT EXISTS trg_orders_paid_states_need_verification
BEFORE UPDATE OF status ON orders
WHEN NEW.status IN ('payment_confirmed','assigned','fulfilling','delivered','completed','support_open')
 AND NOT EXISTS (
   SELECT 1 FROM payment_verifications v
   WHERE v.order_id = NEW.id AND v.voided_at IS NULL
     AND v.amount_minor = NEW.total_minor AND v.currency = NEW.currency)
BEGIN
  SELECT RAISE(ABORT, 'PAYMENT_NOT_VERIFIED');
END;

-- order_events is an append-only audit log.
CREATE TRIGGER IF NOT EXISTS trg_order_events_no_update
BEFORE UPDATE ON order_events
BEGIN
  SELECT RAISE(ABORT, 'AUDIT_LOG_IMMUTABLE');
END;
