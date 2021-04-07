CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    token TEXT,
    emails TEXT[],
    discord_id TEXT,
    github_id TEXT,
    google_id TEXT,
    admin BOOLEAN DEFAULT false,
    theme TEXT DEFAULT 'dark',
    subscriber BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS pastes (
    id TEXT PRIMARY KEY,
    author_id BIGINT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires TIMESTAMP WITH TIME ZONE,
    last_edited TIMESTAMP WITH TIME ZONE,
    password TEXT,
    views INTEGER DEFAULT 0,
    origin_ip TEXT
);

CREATE TABLE IF NOT EXISTS files (
    parent_id TEXT REFERENCES pastes(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    filename TEXT,
    syntax TEXT,
    loc INTEGER NOT NULL,
    charcount INTEGER GENERATED ALWAYS AS (LENGTH(content)) STORED,
    index SERIAL NOT NULL,
    PRIMARY KEY (parent_id, index)
);

CREATE TABLE IF NOT EXISTS bookmarks (
    userid bigint not null references users(id) ON DELETE CASCADE,
    paste text not null references pastes(id) ON DELETE CASCADE,
    PRIMARY KEY (userid, paste),
    created_at timestamp without time zone not null default (now() at time zone 'utc')
);

CREATE TABLE IF NOT EXISTS bans (
    ip TEXT UNIQUE,
    userid BIGINT UNIQUE,
    reason TEXT
);

CREATE OR REPLACE FUNCTION deleteOldPastes() RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM pastes CASCADE WHERE expires IS NOT NULL AND expires < now() AT TIME ZONE 'utc';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS oldPastesExpiry on public.pastes;
CREATE TRIGGER oldPastesExpiry
    AFTER INSERT OR UPDATE
    ON pastes
    FOR STATEMENT
    EXECUTE PROCEDURE deleteOldPastes();
