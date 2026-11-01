CREATE TABLE IF NOT EXISTS users (
  id         text PRIMARY KEY,
  email      text UNIQUE NOT NULL,
  name       text NOT NULL DEFAULT '',
  pw_hash    text NOT NULL,
  role       text NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
  active     boolean NOT NULL DEFAULT true,
  created    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash text PRIMARY KEY,
  user_id    text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created    timestamptz NOT NULL DEFAULT now(),
  expires    timestamptz NOT NULL
);
-- Firestore-style tree: a document path has an even number of segments, its collection (parent) the leading odd ones.
CREATE TABLE IF NOT EXISTS docs (
  path       text PRIMARY KEY,
  parent     text NOT NULL,
  id         text NOT NULL,
  data       jsonb NOT NULL,
  updated    timestamptz NOT NULL DEFAULT now(),
  updated_by text
);
CREATE INDEX IF NOT EXISTS docs_parent ON docs (parent);
CREATE TABLE IF NOT EXISTS assets (
  id      text PRIMARY KEY,
  name    text,
  mime    text,
  size    integer NOT NULL,
  data    bytea NOT NULL,
  owner   text,
  created timestamptz NOT NULL DEFAULT now()
);
