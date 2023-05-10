ALTER TABLE users DROP COLUMN token;

CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    token_name VARCHAR(32) NOT NULL CHECK (LENGTH(token_name) > 2),
    token_description VARCHAR(256),
    token_key UUID NOT NULL,
    UNIQUE (user_id, token_name),
    is_main BOOLEAN NOT NULL DEFAULT FALSE,
    uses INTEGER NOT NULL DEFAULT 0
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

ALTER TABLE pastes ADD COLUMN token_id INTEGER REFERENCES tokens(id);

CREATE TABLE requested_pastes (
    id TEXT,
    requester BIGINT NOT NULL REFERENCES users(id),
    PRIMARY KEY (id, requester),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT ((NOW() AT TIME ZONE 'utc') + INTERVAL '15 minutes')
);

CREATE FUNCTION deleteOldPasteRequests() RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM requested_pastes WHERE expires_at < now() AT TIME ZONE 'utc';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER oldRequestPasteExpiry
    AFTER INSERT OR UPDATE
    ON requested_pastes
    FOR STATEMENT
    EXECUTE PROCEDURE deleteOldPasteRequests();