CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    emails TEXT[] NOT NULL DEFAULT '{}',
    discord_id TEXT,
    github_id TEXT,
    google_id TEXT,
    admin BOOLEAN NOT NULL DEFAULT false,
    theme TEXT NOT NULL DEFAULT 'dark',
    subscriber BOOLEAN DEFAULT false,
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    token_name VARCHAR(32) NOT NULL CHECK (LENGTH(token_name) > 2),
    token_description VARCHAR(256),
    token_key UUID NOT NULL,
    UNIQUE (user_id, token_name),
    is_main BOOLEAN NOT NULL DEFAULT FALSE,
    uses INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pastes (
    id TEXT PRIMARY KEY,
    author_id BIGINT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires TIMESTAMP WITH TIME ZONE,
    last_edited TIMESTAMP WITH TIME ZONE,
    password TEXT,
    views INTEGER DEFAULT 0,
    origin_ip TEXT,
    token_id INTEGER REFERENCES tokens(id)
);

CREATE TABLE IF NOT EXISTS files (
    parent_id TEXT REFERENCES pastes(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    filename TEXT,
    loc INTEGER NOT NULL,
    charcount INTEGER GENERATED ALWAYS AS (LENGTH(content)) STORED,
    index SERIAL NOT NULL,
    attachment TEXT,
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

CREATE TABLE styles (
    userid BIGINT PRIMARY KEY REFERENCES users(id),
    primary_bg CHAR(6),
    secondary_bg CHAR(6),
    primary_font VARCHAR(16),
    secondary_font VARCHAR(16),
    accent CHAR(6),
    prism_theme VARCHAR(16)
);

CREATE TABLE IF NOT EXISTS logs (
    ip TEXT NOT NULL,
    userid BIGINT REFERENCES users(id),
    accessed TIMESTAMP,
    cf_ray TEXT,
    cf_country TEXT,
    web_route TEXT NOT NULL,
    body TEXT,
    response_code INTEGER NOT NULL,
    response TEXT
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
