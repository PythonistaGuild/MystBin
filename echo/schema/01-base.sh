#!/bin/sh
set -euf -o pipefail

psql -v ON_ERROR_STOP=1 --username "echo" --dbname "echo" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    CREATE TABLE IF NOT EXISTS pastes (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
        expires_at TIMESTAMPTZ,
        views BIGINT NOT NULL DEFAULT 0,
        max_views SMALLINT,
        password TEXT,
        safety TEXT UNIQUE
    );

    -- Index by safety keys for faster lookup to delete.
    CREATE UNIQUE INDEX IF NOT EXISTS pastes_safety_idx ON pastes (safety);

    CREATE TABLE IF NOT EXISTS files (
        id BIGSERIAL PRIMARY KEY NOT NULL,
        paste_id TEXT REFERENCES pastes(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        language TEXT, -- highlight.js syntax highlighting language
        lines INTEGER NOT NULL GENERATED ALWAYS AS (LENGTH(REGEXP_REPLACE(content, '[^\n]', '', 'g')) + 1) STORED,
        characters INTEGER NOT NULL GENERATED ALWAYS AS (LENGTH(content)) STORED
    );

    CREATE TABLE IF NOT EXISTS annotations (
        id BIGSERIAL PRIMARY KEY NOT NULL,
        file_id BIGINT REFERENCES files(id) ON DELETE CASCADE,
        head_line INTEGER NOT NULL,
        head_char INTEGER NOT NULL,
        tail_line INTEGER NOT NULL,
        tail_char INTEGER NOT NULL,
        content TEXT NOT NULL
    );
EOSQL
