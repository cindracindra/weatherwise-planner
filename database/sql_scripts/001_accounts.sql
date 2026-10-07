-- Migration 001: user accounts, one calendar per person.
--
-- Adds app_user and gives every event an owner. Profiles and the
-- event-profile link table are removed. Events created before accounts
-- existed have no owner, so they are discarded (sample data only;
-- decided 2026-10-07).
--
-- Safe to run more than once: the discarding and dropping only happen
-- the first time, while event has no user_id column.

CREATE TABLE IF NOT EXISTS app_user (
    id SERIAL PRIMARY KEY,
    google_sub VARCHAR UNIQUE,          -- Google's permanent account ID
    email VARCHAR,
    name VARCHAR NOT NULL,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'event' AND column_name = 'user_id'
    ) THEN
        DROP TABLE IF EXISTS eventxprofile;
        DROP TABLE IF EXISTS profile;
        DELETE FROM event;
        ALTER TABLE event
            ADD COLUMN user_id INTEGER NOT NULL
            REFERENCES app_user(id) ON DELETE CASCADE;
        CREATE INDEX event_user_id_idx ON event (user_id);
    END IF;
END $$;
