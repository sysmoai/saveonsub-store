-- Staff-assisted ticket intake, categories, escalation. ADDITIVE to
-- support-tickets-schema.sql (apply once, after it). Still the same two tables
-- support_threads / support_events: no second ticket schema.
-- NON-PRODUCTION until staging D1, Turnstile, Access MFA and the fulfillment-role
-- login test have passed.

-- What the ticket is about. Basic subscription support is the default and is
-- never gated; ai_training_inquiry is an optional paid service enquiry kept apart
-- so it cannot be mistaken for, or crowd out, subscription support.
ALTER TABLE support_threads ADD COLUMN category TEXT NOT NULL DEFAULT 'subscription_support'
  CHECK (category IN ('subscription_support','order_status','renewal','ai_training_inquiry','other'));
-- How the customer's ownership of the linked order was established.
--   order_token  customer proved it with the Order OS tracking token
--   staff_verified  a named operator checked it out-of-band (see verification_method)
--   unverified   no order is linked; the ticket carries no order data
ALTER TABLE support_threads ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'order_token'
  CHECK (verification_status IN ('order_token','staff_verified','unverified'));
ALTER TABLE support_threads ADD COLUMN verification_method TEXT
  CHECK (verification_method IS NULL OR verification_method IN ('whatsapp_number_match','payment_ref_last4','order_details_match'));
ALTER TABLE support_threads ADD COLUMN verified_by TEXT REFERENCES operators(id) ON DELETE SET NULL;
ALTER TABLE support_threads ADD COLUMN verified_at TEXT;
ALTER TABLE support_threads ADD COLUMN channel TEXT NOT NULL DEFAULT 'web'
  CHECK (channel IN ('web','whatsapp_assisted'));
ALTER TABLE support_threads ADD COLUMN escalated_at TEXT;
ALTER TABLE support_threads ADD COLUMN escalation_reason TEXT;

-- A staff-verified link must name who verified it, how and when.
CREATE TRIGGER IF NOT EXISTS trg_support_verified_needs_actor
BEFORE INSERT ON support_threads
WHEN NEW.verification_status = 'staff_verified'
 AND (NEW.verified_by IS NULL OR NEW.verified_at IS NULL OR NEW.verification_method IS NULL OR NEW.order_id IS NULL)
BEGIN SELECT RAISE(ABORT, 'STAFF_VERIFIED_NEEDS_ACTOR_METHOD_ORDER'); END;

-- An unverified ticket must never be linked to an order.
CREATE TRIGGER IF NOT EXISTS trg_support_unverified_no_order
BEFORE INSERT ON support_threads
WHEN NEW.verification_status = 'unverified' AND NEW.order_id IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'UNVERIFIED_TICKET_CANNOT_LINK_ORDER'); END;

CREATE INDEX IF NOT EXISTS idx_support_threads_assignee ON support_threads(assigned_operator_id, status);
