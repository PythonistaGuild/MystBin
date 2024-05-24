BEGIN; -- start transaction

SAVEPOINT pastes;
ALTER TABLE pastes DROP COLUMN IF EXISTS author_id CASCADE;  -- no longer storing users
ALTER TABLE pastes DROP COLUMN IF EXISTS last_edited CASCADE; -- no longer allowing edits
ALTER TABLE pastes ALTER COLUMN password SET DEFAULT NULL; -- nullable password by default
ALTER TABLE pastes DROP COLUMN IF EXISTS origin_ip CASCADE; -- no longer needed
ALTER TABLE pastes ADD COLUMN IF NOT EXISTS safety TEXT UNIQUE;  -- this is how we handle paste deletion.
UPDATE pastes SET safety = gen_random_uuid();  -- Populate with junk data.
ALTER TABLE pastes ALTER COLUMN safety SET NOT NULL;  -- add not null constraint
CREATE UNIQUE INDEX IF NOT EXISTS pastes_safety_idx ON pastes (safety); -- -- Index by safety keys for faster lookup to delete.

SAVEPOINT files;
ALTER TABLE files ALTER COLUMN filename SET NOT NULL;  -- always require filename
ALTER TABLE files DROP COLUMN IF EXISTS attachment;  -- we don't have these anymore
ALTER TABLE files ADD COLUMN IF NOT EXISTS annotation TEXT;
ALTER TABLE files RENAME COLUMN index TO file_index;  -- bad column name
ALTER TABLE files ADD COLUMN IF NOT EXISTS warning_positions INTEGER[];  -- New line warning positions

SAVEPOINT drops;
DROP TABLE IF EXISTS bans CASCADE; -- no longer needed
DROP TABLE IF EXISTS logs CASCADE; -- no longer needed
DROP TABLE IF EXISTS bookmarks CASCADE;  -- no longer needed
DROP TABLE IF EXISTS users CASCADE;  -- no longer needed

COMMIT;
