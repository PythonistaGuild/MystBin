ALTER TABLE users DROP COLUMN token;

CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    token_name VARCHAR(32) NOT NULL,
    token_description VARCHAR(256),
    token_key UUID NOT NULL,
    UNIQUE (user_id, token_name),
    is_main BOOLEAN NOT NULL DEFAULT FALSE,
    uses INTEGER NOT NULL DEFAULT 0
);

ALTER TABLE pastes ADD COLUMN token_id INTEGER REFERENCES tokens(id);