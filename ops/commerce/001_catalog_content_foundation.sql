-- SaveOnSub-only commerce extension. Apply AFTER ops/order-os/schema.sql.
-- Production remains unchanged until CEO-approved D1 staging, backup and migration QA.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS commerce_products (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('subscription','service','bundle')),
  provider_name TEXT,
  provider_official_url TEXT,
  summary TEXT NOT NULL DEFAULT '',
  lifecycle TEXT NOT NULL DEFAULT 'draft' CHECK (lifecycle IN ('draft','review','approved','published','paused','blocked','archived')),
  authorization TEXT NOT NULL DEFAULT 'unknown' CHECK (authorization IN ('unknown','verified','restricted','blocked')),
  source_verified_at TEXT,
  rights_evidence_ref TEXT,
  revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
  created_by TEXT NOT NULL REFERENCES operators(id),
  updated_by TEXT NOT NULL REFERENCES operators(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (lifecycle NOT IN ('approved','published') OR (authorization = 'verified' AND rights_evidence_ref IS NOT NULL AND source_verified_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_commerce_products_lifecycle ON commerce_products(lifecycle,category);

CREATE TABLE IF NOT EXISTS commerce_plans (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL REFERENCES commerce_products(id) ON DELETE RESTRICT,
  label TEXT NOT NULL,
  access_model TEXT NOT NULL CHECK (access_model IN ('personal','provider_team','authorized_family','service','inquiry','blocked')),
  duration_label TEXT,
  price_minor INTEGER CHECK (price_minor IS NULL OR price_minor >= 0),
  currency TEXT NOT NULL DEFAULT 'BDT' CHECK (currency='BDT'),
  pricing_source_ref TEXT,
  pricing_verified_at TEXT,
  lifecycle TEXT NOT NULL DEFAULT 'draft' CHECK (lifecycle IN ('draft','review','approved','published','paused','blocked')),
  approval_id TEXT REFERENCES commerce_approvals(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (lifecycle NOT IN ('approved','published') OR (price_minor IS NOT NULL AND pricing_source_ref IS NOT NULL AND pricing_verified_at IS NOT NULL AND approval_id IS NOT NULL)),
  CHECK (access_model NOT IN ('inquiry','blocked') OR lifecycle NOT IN ('approved','published'))
);
CREATE INDEX IF NOT EXISTS idx_commerce_plans_product ON commerce_plans(product_id,lifecycle);

CREATE TABLE IF NOT EXISTS commerce_media_assets (
  id TEXT PRIMARY KEY,
  storage_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('image','video','poster','document')),
  mime_type TEXT NOT NULL,
  byte_count INTEGER NOT NULL CHECK (byte_count >= 0),
  sha256_hex TEXT NOT NULL CHECK (length(sha256_hex)=64),
  alt_text TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  rights_type TEXT NOT NULL CHECK (rights_type IN ('created_by_business','licensed','provider_supplied','unknown')),
  rights_evidence_ref TEXT,
  lifecycle TEXT NOT NULL DEFAULT 'draft' CHECK (lifecycle IN ('draft','review','approved','published','archived','blocked')),
  uploaded_by TEXT NOT NULL REFERENCES operators(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (lifecycle NOT IN ('approved','published') OR (rights_type <> 'unknown' AND rights_evidence_ref IS NOT NULL AND length(alt_text) > 0))
);
CREATE INDEX IF NOT EXISTS idx_commerce_media_status ON commerce_media_assets(lifecycle,kind);

CREATE TABLE IF NOT EXISTS commerce_product_media (
  product_id TEXT NOT NULL REFERENCES commerce_products(id) ON DELETE CASCADE,
  media_id TEXT NOT NULL REFERENCES commerce_media_assets(id) ON DELETE RESTRICT,
  usage_type TEXT NOT NULL CHECK (usage_type IN ('hero','gallery','poster','social','demo_video','tutorial')),
  sort_order INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (product_id,media_id,usage_type)
);

CREATE TABLE IF NOT EXISTS commerce_content (
  id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES commerce_products(id) ON DELETE SET NULL,
  channel TEXT NOT NULL CHECK (channel IN ('website','blog','facebook','instagram','tiktok','youtube','whatsapp')),
  format TEXT NOT NULL CHECK (format IN ('article','caption','poster','carousel','short_video','long_video','email')),
  title TEXT NOT NULL,
  copy_draft TEXT NOT NULL DEFAULT '',
  claim_sources_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(claim_sources_json)),
  media_id TEXT REFERENCES commerce_media_assets(id) ON DELETE SET NULL,
  lifecycle TEXT NOT NULL DEFAULT 'draft' CHECK (lifecycle IN ('draft','review','approved','scheduled','published','rejected','archived')),
  approval_id TEXT REFERENCES commerce_approvals(id),
  platform_post_id TEXT,
  platform_post_url TEXT,
  published_at TEXT,
  created_by TEXT NOT NULL REFERENCES operators(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (lifecycle NOT IN ('approved','scheduled','published') OR approval_id IS NOT NULL),
  CHECK (lifecycle <> 'published' OR (platform_post_id IS NOT NULL AND platform_post_url IS NOT NULL AND published_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_commerce_content_channel_status ON commerce_content(channel,lifecycle);

CREATE TABLE IF NOT EXISTS commerce_approvals (
  id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL CHECK (target_type IN ('product','plan','media','content','refund','deployment','vendor')),
  target_id TEXT NOT NULL,
  requested_action TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','expired')),
  requested_by TEXT NOT NULL REFERENCES operators(id),
  reviewed_by TEXT REFERENCES operators(id),
  reason TEXT NOT NULL DEFAULT '',
  evidence_ref TEXT,
  requested_at TEXT NOT NULL,
  reviewed_at TEXT,
  CHECK (status = 'pending' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_commerce_approvals_status ON commerce_approvals(status,requested_at);

CREATE TABLE IF NOT EXISTS commerce_inventory (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES commerce_plans(id) ON DELETE RESTRICT,
  availability TEXT NOT NULL CHECK (availability IN ('unknown','available','limited','unavailable','blocked')),
  available_units INTEGER CHECK (available_units IS NULL OR available_units >= 0),
  provider_evidence_ref TEXT,
  verified_at TEXT,
  updated_by TEXT NOT NULL REFERENCES operators(id),
  updated_at TEXT NOT NULL,
  UNIQUE(plan_id)
);

CREATE TABLE IF NOT EXISTS commerce_cost_entries (
  id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
  kind TEXT NOT NULL CHECK (kind IN ('provider_cost','payment_fee','fx_fee','fulfilment_cost','support_cost','refund','loss_reserve')),
  amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
  currency TEXT NOT NULL DEFAULT 'BDT' CHECK(currency='BDT'),
  evidence_ref TEXT,
  verification TEXT NOT NULL DEFAULT 'unverified' CHECK (verification IN ('unverified','verified','disputed')),
  verified_by TEXT REFERENCES operators(id),
  verified_at TEXT,
  created_at TEXT NOT NULL,
  CHECK (verification <> 'verified' OR (evidence_ref IS NOT NULL AND verified_by IS NOT NULL AND verified_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_commerce_cost_order ON commerce_cost_entries(order_id,verification);

CREATE TABLE IF NOT EXISTS commerce_agent_jobs (
  id TEXT PRIMARY KEY,
  tenant TEXT NOT NULL DEFAULT 'SOS' CHECK (tenant='SOS'),
  job_type TEXT NOT NULL,
  subject_ref TEXT,
  state TEXT NOT NULL DEFAULT 'queued' CHECK (state IN ('queued','running','awaiting_review','approved','completed','failed','cancelled')),
  risk_level TEXT NOT NULL DEFAULT 'a2' CHECK (risk_level IN ('a1','a2','a3','a4')),
  idempotency_key TEXT NOT NULL UNIQUE,
  created_by TEXT NOT NULL,
  assigned_agent TEXT,
  approval_id TEXT REFERENCES commerce_approvals(id),
  input_evidence_ref TEXT,
  output_evidence_ref TEXT,
  verification_ref TEXT,
  estimated_cost_minor INTEGER NOT NULL DEFAULT 0 CHECK (estimated_cost_minor >= 0),
  actual_cost_minor INTEGER CHECK (actual_cost_minor IS NULL OR actual_cost_minor >= 0),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT,
  CHECK (state <> 'completed' OR verification_ref IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_commerce_agent_jobs_state ON commerce_agent_jobs(state,created_at);

CREATE TABLE IF NOT EXISTS commerce_audit_events (
  id TEXT PRIMARY KEY,
  tenant TEXT NOT NULL DEFAULT 'SOS' CHECK (tenant='SOS'),
  actor_type TEXT NOT NULL CHECK (actor_type IN ('operator','system','agent')),
  actor_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_commerce_audit_entity ON commerce_audit_events(entity_type,entity_id,created_at);
CREATE TRIGGER IF NOT EXISTS commerce_audit_no_update BEFORE UPDATE ON commerce_audit_events BEGIN SELECT RAISE(ABORT,'AUDIT_EVENTS_IMMUTABLE'); END;
CREATE TRIGGER IF NOT EXISTS commerce_audit_no_delete BEFORE DELETE ON commerce_audit_events BEGIN SELECT RAISE(ABORT,'AUDIT_EVENTS_IMMUTABLE'); END;

CREATE TABLE IF NOT EXISTS commerce_import_batches (
  id TEXT PRIMARY KEY,
  source_ref TEXT NOT NULL,
  source_sha256 TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','review','approved','rejected')),
  total_products INTEGER NOT NULL DEFAULT 0 CHECK (total_products >= 0),
  total_plans INTEGER NOT NULL DEFAULT 0 CHECK (total_plans >= 0),
  blocked_plans INTEGER NOT NULL DEFAULT 0 CHECK (blocked_plans >= 0),
  review_notes TEXT NOT NULL DEFAULT '',
  reviewed_by TEXT REFERENCES operators(id),
  created_at TEXT NOT NULL,
  reviewed_at TEXT
);
