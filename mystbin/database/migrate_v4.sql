BEGIN TRANSACTION;

ALTER TABLE users DROP token;
ALTER TABLE logs
    DROP CONSTRAINT logs_userid_fkey
    ADD CONSTRAINT logs_userid_fkey
        FOREIGN KEY (userid)
        REFERENCES users(id)
        ON DELETE SET NULL;

ALTER TABLE pastes 
    DROP CONSTRAINT pastes_author_id_fkey,
    ADD CONSTRAINT pastes_author_id_fkey
        FOREIGN KEY (author_id)
        REFERENCES users(id)
        ON DELETE SET NULL;

CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_name VARCHAR(32) NOT NULL CHECK (LENGTH(token_name) > 2),
    token_description VARCHAR(256),
    token_key UUID NOT NULL,
    UNIQUE (user_id, token_name),
    is_main BOOLEAN NOT NULL DEFAULT FALSE,
    uses INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE styles (
    userid BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    primary_bg CHAR(6),
    secondary_bg CHAR(6),
    primary_font VARCHAR(16),
    secondary_font VARCHAR(16),
    accent CHAR(6),
    prism_theme VARCHAR(16)
);

ALTER TABLE pastes ADD COLUMN token_id INTEGER REFERENCES tokens(id);

CREATE TABLE requested_pastes (
    id TEXT UNIQUE,
    requester BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (id, requester),
    fulfilled_slug TEXT
);

CREATE OR REPLACE FUNCTION deleteUserAccount(delete_user_id INTEGER, keep_pastes BOOLEAN)
RETURNS BOOLEAN
AS $$
BEGIN
    IF (keep_pastes IS TRUE) THEN
        UPDATE pastes SET author_id = NULL WHERE author_id = delete_user_id;
    ELSE
        DELETE FROM pastes WHERE author_id = delete_user_id;
    END IF;
    
    UPDATE logs SET userid = NULL WHERE userid = delete_user_id;
    DELETE FROM users WHERE id = delete_user_id;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMIT TRANSACTION;