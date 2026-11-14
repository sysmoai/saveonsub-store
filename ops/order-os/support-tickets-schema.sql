-- Support tickets on the EXISTING support_threads / support_events tables
-- (schema.sql). No second ticket schema. Apply ONCE, in order, after schema.sql
-- (SQLite ADD COLUMN is not idempotent; the indexes and triggers are).
-- NON-PRODUCTION until staging D1, Turnstile secret, Access MFA and the
-- fulfillment-role login test have passed (see PR description).

-- Customer-facing, non-sequential identifier (random, never derived from a counter)
ALTER TABLE support_threads ADD COLUMN public_ticket_id TEXT;
-- SHA-256 of the per-ticket secret shown to the customer once. The secret itself is never stored.
ALTER TABLE support_threads ADD COLUMN access_token_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_support_public_ticket
  ON support_threads(public_ticket_id) WHERE public_ticket_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_support_token_hash
  ON support_threads(access_token_hash) WHERE access_token_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_support_threads_order ON support_threads(order_id, status);
CREATE INDEX IF NOT EXISTS idx_support_events_thread ON support_events(thread_id, id);

-- Conversation history is append-only, like order_events.
CREATE TRIGGER IF NOT EXISTS trg_support_events_no_update
BEFORE UPDATE ON support_events
BEGIN SELECT RAISE(ABORT, 'SUPPORT_EVENTS_APPEND_ONLY'); END;

CREATE TRIGGER IF NOT EXISTS trg_support_events_no_delete
BEFORE DELETE ON support_events
BEGIN SELECT RAISE(ABORT, 'SUPPORT_EVENTS_APPEND_ONLY'); END;

-- A closed ticket cannot be reopened or edited by any code path.
CREATE TRIGGER IF NOT EXISTS trg_support_threads_closed_immutable
BEFORE UPDATE ON support_threads
WHEN OLD.status = 'closed'
BEGIN SELECT RAISE(ABORT, 'TICKET_CLOSED_IMMUTABLE'); END;
