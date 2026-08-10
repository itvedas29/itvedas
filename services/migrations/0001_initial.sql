-- ITVedas Services — initial schema (Cloudflare D1 / SQLite).
--
-- V1 stores enquiries only; customer accounts, invoices and payments are
-- deliberately not built yet. The tables below are shaped so they can be
-- added later without a rewrite: companies/customers already exist as
-- separate rows keyed off each requirement, and quotes/projects are
-- separate tables rather than columns on requirements.

-- Companies a requirement came from. Deduplicated loosely by name+country;
-- V1 never merges automatically, admin can do it manually later.
CREATE TABLE IF NOT EXISTS companies (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT,
  country      TEXT,
  website      TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- The person who submitted. Not an account — no password, no login.
-- Phase 2 customer accounts will add auth columns here rather than a new table.
CREATE TABLE IF NOT EXISTS customers (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id   INTEGER REFERENCES companies(id) ON DELETE SET NULL,
  name         TEXT NOT NULL,
  email        TEXT NOT NULL,
  phone        TEXT,
  country      TEXT,
  preferred_contact TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- The catalog of services shown on the site. Seeded in 0002_seed.sql.
-- Kept in the DB (not just hardcoded in HTML) so the admin can eventually
-- toggle availability and adjust indicative pricing centrally.
CREATE TABLE IF NOT EXISTS service_catalog (
  slug          TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  description   TEXT,
  starting_price_usd INTEGER,
  is_active     INTEGER NOT NULL DEFAULT 1,
  sort_order    INTEGER NOT NULL DEFAULT 0
);

-- The core table. One row per submitted IT requirement.
CREATE TABLE IF NOT EXISTS requirements (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  reference     TEXT NOT NULL UNIQUE,          -- ITV-XXXX shown to the customer
  customer_id   INTEGER REFERENCES customers(id) ON DELETE SET NULL,
  company_id    INTEGER REFERENCES companies(id) ON DELETE SET NULL,

  description   TEXT NOT NULL,

  -- environment (all optional)
  users_count       TEXT,
  devices_count     TEXT,
  windows_devices   TEXT,
  mac_devices       TEXT,
  productivity_suite TEXT,                     -- microsoft-365 / google-workspace / other / none
  endpoint_solution TEXT,
  other_technology  TEXT,

  budget_range  TEXT,                          -- under-50 / 50-100 / ... / not-sure
  urgency       TEXT,                          -- normal / soon / urgent / critical
  extra_message TEXT,

  status        TEXT NOT NULL DEFAULT 'new',
  -- new | reviewing | contacted | qualified | quoted | fiverr_upwork
  -- | in_progress | completed | follow_up | cancelled

  source        TEXT,                          -- utm/referrer bucket, for analytics
  ip_country    TEXT,                          -- CF-provided, coarse — no full IP stored
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_requirements_status ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_requirements_created ON requirements(created_at DESC);

-- Many-to-many: a requirement can span several service categories.
CREATE TABLE IF NOT EXISTS requirement_categories (
  requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  category       TEXT NOT NULL,
  PRIMARY KEY (requirement_id, category)
);

-- Attachment metadata. The file body lives in R2; this table only holds
-- the key and metadata so the DB stays small.
CREATE TABLE IF NOT EXISTS requirement_attachments (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  r2_key         TEXT NOT NULL,
  filename       TEXT NOT NULL,
  content_type   TEXT,
  size_bytes     INTEGER,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_attachments_req ON requirement_attachments(requirement_id);

-- Internal admin notes. Never shown to the customer.
CREATE TABLE IF NOT EXISTS requirement_notes (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  admin_user_id  INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
  body           TEXT NOT NULL,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notes_req ON requirement_notes(requirement_id, created_at DESC);

-- Quotes issued against a requirement. V1 records them; automated quote
-- generation and customer-facing quote pages are Phase 2.
CREATE TABLE IF NOT EXISTS quotes (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  amount_usd     REAL,
  scope          TEXT,
  notes          TEXT,
  sent_at        TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_quotes_req ON quotes(requirement_id);

-- A requirement that became actual work.
CREATE TABLE IF NOT EXISTS projects (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  platform       TEXT,          -- see project_platforms
  project_url    TEXT,
  project_ref    TEXT,
  agreed_price_usd REAL,
  notes          TEXT,
  started_at     TEXT,
  completed_at   TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_projects_req ON projects(requirement_id);

-- Lookup table rather than a CHECK constraint so new platforms (direct
-- invoicing in Phase 2) can be added without a migration on projects.
CREATE TABLE IF NOT EXISTS project_platforms (
  slug  TEXT PRIMARY KEY,
  name  TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1
);

-- Every status transition, for an auditable trail.
CREATE TABLE IF NOT EXISTS status_history (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  from_status    TEXT,
  to_status      TEXT NOT NULL,
  admin_user_id  INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_status_history_req ON status_history(requirement_id, created_at DESC);

-- Outbound email log — lets the admin see what the customer actually received.
CREATE TABLE IF NOT EXISTS email_events (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id INTEGER REFERENCES requirements(id) ON DELETE CASCADE,
  template       TEXT NOT NULL,   -- customer_received | admin_notify | ...
  recipient      TEXT NOT NULL,
  status         TEXT NOT NULL,   -- sent | failed | skipped
  error          TEXT,
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_email_events_req ON email_events(requirement_id, created_at DESC);

-- Admin accounts. Passwords are PBKDF2-SHA256, never plaintext.
CREATE TABLE IF NOT EXISTS admin_users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  email         TEXT NOT NULL UNIQUE,
  name          TEXT,
  password_hash TEXT NOT NULL,   -- pbkdf2$<iterations>$<salt_b64>$<hash_b64>
  is_active     INTEGER NOT NULL DEFAULT 1,
  last_login_at TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Server-side sessions. A cookie holds only an opaque random token, so
-- revoking access is a row delete rather than a secret rotation.
CREATE TABLE IF NOT EXISTS admin_sessions (
  token         TEXT PRIMARY KEY,
  admin_user_id INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
  expires_at    TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON admin_sessions(expires_at);

-- Configurable business settings (business name, Fiverr/Upwork profile URLs,
-- analytics IDs, notification email). Avoids hardcoding these in HTML.
CREATE TABLE IF NOT EXISTS settings (
  key        TEXT PRIMARY KEY,
  value      TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
