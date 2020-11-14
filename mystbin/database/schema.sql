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
    author BIGINT REFERENCES users(id),
    nick TEXT DEFAULT '',
    syntax TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires TIMESTAMP WITH TIME ZONE,
    last_edited TIMESTAMP WITH TIME ZONE,
    password TEXT,
    views INT DEFAULT 0,
    loc INT,
    charcount INT,
    content TEXT,
    index SERIAL
);