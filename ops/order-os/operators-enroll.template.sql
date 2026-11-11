-- SaveOnSub staff enrollment TEMPLATE. The CEO runs this himself in the
-- Cloudflare D1 console of database "saveonsub-order-os" (never the storefront,
-- never another business's DB), AFTER schema.sql is applied.
-- Replace the two <...> email placeholders with the exact Google login emails.
-- Do not commit real emails to this public repository.
-- Roles (CEO decision 2026-11-06): EMON = owner, Ripon = fulfillment.

INSERT INTO operators (id, email, display_name, role, active, created_at, updated_at)
VALUES
  ('op-emon',  lower('<EMON_LOGIN_EMAIL>'),  'EMON',  'owner',       1, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('op-ripon', lower('<RIPON_LOGIN_EMAIL>'), 'Ripon', 'fulfillment', 1, strftime('%Y-%m-%dT%H:%M:%fZ','now'), strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Check:
-- SELECT id, email, role, active FROM operators;

-- Remove someone's access (also remove them from the Access policy):
-- UPDATE operators SET active = 0, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = 'op-ripon';
