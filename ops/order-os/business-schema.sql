-- Private SaveOnSub D1 only. Apply after schema.sql; never ship with storefront.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS business_records (
 id TEXT PRIMARY KEY,
 kind TEXT NOT NULL CHECK(kind IN ('lead','task','expense','price_review')),
 title TEXT NOT NULL CHECK(length(title) BETWEEN 2 AND 160),
 details TEXT NOT NULL DEFAULT '',
 status TEXT NOT NULL CHECK(status IN ('open','working','blocked','done','pending','approved','rejected')),
 amount_minor INTEGER NOT NULL DEFAULT 0 CHECK(amount_minor>=0),
 created_by TEXT NOT NULL REFERENCES operators(id),
 decided_by TEXT REFERENCES operators(id),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 CHECK(kind NOT IN ('expense','price_review') OR status IN ('pending','approved','rejected')),
 CHECK(status<>'approved' OR (decided_by IS NOT NULL AND decided_by<>created_by))
);
CREATE TABLE IF NOT EXISTS business_audit (
 id TEXT PRIMARY KEY, record_id TEXT NOT NULL REFERENCES business_records(id),
 actor_id TEXT NOT NULL REFERENCES operators(id), action TEXT NOT NULL,
 from_status TEXT, to_status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS business_audit_no_update BEFORE UPDATE ON business_audit
 BEGIN SELECT RAISE(ABORT,'AUDIT_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS business_audit_no_delete BEFORE DELETE ON business_audit
 BEGIN SELECT RAISE(ABORT,'AUDIT_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS business_decision_immutable BEFORE UPDATE ON business_records
 WHEN OLD.status IN ('approved','rejected') BEGIN SELECT RAISE(ABORT,'DECISION_IMMUTABLE'); END;
CREATE INDEX IF NOT EXISTS business_records_queue ON business_records(kind,status,created_at);
