CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    token TEXT,
    emails TEXT[],
    discord_id BIGINT,
    github_id BIGINT,
    google_id BIGINT,
    admin BOOLEAN NOT NULL,
    theme TEXT DEFAULT 'default',
    subscriber BOOLEAN DEFAULT false,
    banned BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS pastes (
    id TEXT PRIMARY KEY,
    author_id BIGINT REFERENCES users(id),
    nick TEXT,
    syntax TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires TIMESTAMP WITH TIME ZONE,
    last_edited TIMESTAMP WITH TIME ZONE,
    password TEXT,
    views INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS paste_content (
    parent_id TEXT REFERENCES pastes(id) ON DELETE CASCADE,
    index SERIAL,
    content TEXT NOT NULL,
    loc INTEGER NOT NULL,
    charcount INTEGER GENERATED ALWAYS AS (LENGTH(content)) STORED,
    PRIMARY KEY (parent_id, index)
);