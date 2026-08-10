-- SAVEONSUB shadow schema v2: observability + non-public media drafts
-- This migration adds no customer order/payment functionality and no public admin.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS operational_events (
  event_id TEXT PRIMARY KEY,
  request_id TEXT,
  event_type TEXT NOT NULL,
  route TEXT,
  result_code TEXT,
  http_status INTEGER,
  latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
  catalog_version TEXT,
  price_version TEXT,
  provider_version TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_operational_events_request ON operational_events(request_id);
CREATE INDEX IF NOT EXISTS idx_operational_events_created ON operational_events(created_at);

CREATE TABLE IF NOT EXISTS media_drafts (
  media_id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  plan_id TEXT,
  kind TEXT NOT NULL CHECK (kind IN ('image', 'video', 'graphic', 'document')),
  role TEXT NOT NULL CHECK (role IN ('hero', 'gallery', 'screenshot', 'feature', 'comparison', 'plan', 'thumbnail', 'poster', 'social', 'download', 'demo', 'howto')),
  provider TEXT NOT NULL CHECK (provider IN ('local', 'cloudflare_images', 'cloudflare_stream', 'r2')),
  source_id TEXT NOT NULL,
  alt_en TEXT NOT NULL,
  alt_bn TEXT NOT NULL,
  caption_en TEXT,
  caption_bn TEXT,
  width INTEGER CHECK (width IS NULL OR width > 0),
  height INTEGER CHECK (height IS NULL OR height > 0),
  duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
  poster_media_id TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  state TEXT NOT NULL DEFAULT 'draft' CHECK (state IN ('draft', 'reviewed', 'approved', 'retired')),
  authority_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_media_drafts_product ON media_drafts(product_id, state, sort_order);
CREATE INDEX IF NOT EXISTS idx_media_drafts_plan ON media_drafts(plan_id, state, sort_order);

CREATE TABLE IF NOT EXISTS admin_audit_events (
  event_id TEXT PRIMARY KEY,
  actor_subject TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  before_sha256 TEXT,
  after_sha256 TEXT,
  authority_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO schema_meta(key, value, updated_at)
VALUES ('schema_version', '2-observability-media-drafts', CURRENT_TIMESTAMP);
