-- Migration 001: user accounts.
-- Adds the app_user table and gives every profile an optional owner.
-- Safe to run more than once, and keeps all existing data.

CREATE TABLE IF NOT EXISTS app_user (
    id SERIAL PRIMARY KEY,
    google_sub VARCHAR UNIQUE,          -- Google's permanent account ID; NULL for demo accounts
    email VARCHAR,
    name VARCHAR NOT NULL,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE profile
    ADD COLUMN IF NOT EXISTS user_id INTEGER
    REFERENCES app_user(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS profile_user_id_idx ON profile (user_id);
