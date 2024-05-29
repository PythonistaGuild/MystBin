CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS pastes (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires TIMESTAMP WITH TIME ZONE,
    password TEXT DEFAULT NULL,
    views INTEGER DEFAULT 0,
    safety TEXT UNIQUE
);

CREATE UNIQUE INDEX IF NOT EXISTS pastes_safety_idx ON pastes (safety);
-- Index by safety keys for faster lookup to delete.

CREATE TABLE IF NOT EXISTS files (
    parent_id TEXT REFERENCES pastes(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    filename TEXT NOT NULL,
    loc INTEGER NOT NULL,
    charcount INTEGER GENERATED ALWAYS AS (LENGTH(content)) STORED,
    file_index SERIAL NOT NULL,
    annotation TEXT,
    warning_positions INTEGER[],
    PRIMARY KEY (parent_id, file_index)
);
