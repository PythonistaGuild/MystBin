CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    token TEXT,
    emails TEXT[],
    bookmarks TEXT[],
    discord_id BIGINT,
    github_id BIGINT,
    google_id BIGINT,
    admin BOOLEAN DEFAULT false,
    theme TEXT DEFAULT 'default',
    subscriber BOOLEAN DEFAULT false,
    banned BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS pastes (
    id TEXT PRIMARY KEY,
    author_id BIGINT REFERENCES users(id),
    workspace_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires TIMESTAMP WITH TIME ZONE,
    last_edited TIMESTAMP WITH TIME ZONE,
    password TEXT,
    views INTEGER DEFAULT 0
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

-- CREATE OR REPLACE FUNCTION setLastEditTime() RETURNS TRIGGER AS $$
-- BEGIN
--     UPDATE pastes SET last_edited = now() AT TIME ZONE 'utc' WHERE id = NEW.id;
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- DROP TRIGGER IF EXISTS lastEditTime on public.pastes;
-- CREATE TRIGGER lastEditTime
--     AFTER UPDATE
--     ON pastes
--     FOR EACH ROW
--     EXECUTE PROCEDURE setLastEditTime();