-- Continuum — Supabase SQL Migration: 001_init.sql
-- Run this via: supabase db push  OR  psql $DATABASE_URL < 001_init.sql

-- Enable pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  email        TEXT UNIQUE NOT NULL,
  name         TEXT,
  avatar_url   TEXT,
  role         TEXT NOT NULL DEFAULT 'USER' CHECK (role IN ('USER','ADMIN')),
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── User Permissions ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_permissions (
  id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id           TEXT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  github_connected  BOOLEAN DEFAULT FALSE,
  github_scopes     TEXT[] DEFAULT '{}',
  github_token      TEXT,               -- encrypted via app-level AES-256
  gmail_connected   BOOLEAN DEFAULT FALSE,
  gmail_scopes      TEXT[] DEFAULT '{}',
  gmail_token       TEXT,
  youtube_connected BOOLEAN DEFAULT FALSE,
  youtube_scopes    TEXT[] DEFAULT '{}',
  youtube_token     TEXT,
  consent_version   TEXT DEFAULT '1.0',
  consent_given_at  TIMESTAMPTZ,
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── Token Quota ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS token_quotas (
  id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id             TEXT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  daily_limit_tokens  INT DEFAULT 50000,
  monthly_limit_usd   NUMERIC(8,4) DEFAULT 5.0000,
  tokens_used_today   INT DEFAULT 0,
  usd_spent_this_month NUMERIC(8,4) DEFAULT 0.0000,
  last_reset_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── Agent States ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_states (
  id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_id         TEXT NOT NULL,
  checkpoint_id  TEXT UNIQUE NOT NULL,
  graph_name     TEXT NOT NULL,
  state          JSONB NOT NULL,
  node_reached   TEXT NOT NULL,
  iteration      INT DEFAULT 0,
  status         TEXT DEFAULT 'RUNNING'
                 CHECK (status IN ('RUNNING','COMPLETED','FAILED','HITL_PENDING','REWOUND')),
  confidence     NUMERIC(4,3),
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_states_user_job ON agent_states(user_id, job_id);

-- ── Legacy Vault ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS legacy_vault (
  id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source        TEXT NOT NULL CHECK (source IN ('GITHUB','GMAIL','YOUTUBE')),
  raw_content   TEXT NOT NULL,         -- AES-256 encrypted
  content_hash  TEXT NOT NULL,         -- SHA-256 for dedup
  metadata      JSONB,
  masked_at     BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_legacy_vault_user_source ON legacy_vault(user_id, source);

-- ── Knowledge Nodes ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_nodes (
  id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title          TEXT NOT NULL,
  summary        TEXT NOT NULL,
  source         TEXT NOT NULL CHECK (source IN ('GITHUB','GMAIL','YOUTUBE')),
  source_ref     TEXT NOT NULL,
  confidence     NUMERIC(4,3) NOT NULL,
  vector_id      TEXT NOT NULL,
  namespace      TEXT NOT NULL,        -- "user_{user_id}" — never cross-user
  checkpoint_id  TEXT,
  tags           TEXT[] DEFAULT '{}',
  created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_user  ON knowledge_nodes(user_id, source);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_ns    ON knowledge_nodes(namespace);

-- ── Vector Embeddings Table (pgvector) ───────────────────────────────────────
-- Each row is a chunk embedding; namespace column enforces user isolation.
CREATE TABLE IF NOT EXISTS embeddings (
  id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  namespace   TEXT NOT NULL,           -- "user_{user_id}"
  node_id     TEXT REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
  content     TEXT NOT NULL,           -- original chunk text
  embedding   vector(1536),            -- OpenAI text-embedding-3-small dim
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_embeddings_ns ON embeddings(namespace);
-- HNSW index for fast ANN search within namespace
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
  ON embeddings USING hnsw (embedding vector_cosine_ops);

-- ── Harvest Jobs ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS harvest_jobs (
  id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  bull_job_id  TEXT UNIQUE NOT NULL,
  source       TEXT NOT NULL CHECK (source IN ('GITHUB','GMAIL','YOUTUBE')),
  status       TEXT DEFAULT 'QUEUED'
               CHECK (status IN ('QUEUED','RUNNING','COMPLETED','FAILED','HITL_PENDING')),
  tokens_used  INT DEFAULT 0,
  iterations   INT DEFAULT 0,
  error_msg    TEXT,
  started_at   TIMESTAMPTZ,
  finished_at  TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_harvest_jobs_user ON harvest_jobs(user_id);

-- ── Row-Level Security (Sovereign Storage) ────────────────────────────────────
ALTER TABLE user_permissions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_quotas      ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_states      ENABLE ROW LEVEL SECURITY;
ALTER TABLE legacy_vault      ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_nodes   ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings        ENABLE ROW LEVEL SECURITY;
ALTER TABLE harvest_jobs      ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY user_permissions_self  ON user_permissions  USING (user_id = auth.uid()::text);
CREATE POLICY token_quotas_self      ON token_quotas      USING (user_id = auth.uid()::text);
CREATE POLICY agent_states_self      ON agent_states      USING (user_id = auth.uid()::text);
CREATE POLICY legacy_vault_self      ON legacy_vault      USING (user_id = auth.uid()::text);
CREATE POLICY knowledge_nodes_self   ON knowledge_nodes   USING (user_id = auth.uid()::text);
CREATE POLICY harvest_jobs_self      ON harvest_jobs      USING (user_id = auth.uid()::text);
-- Embeddings are isolated by namespace
CREATE POLICY embeddings_ns          ON embeddings
  USING (namespace = 'user_' || auth.uid()::text);
