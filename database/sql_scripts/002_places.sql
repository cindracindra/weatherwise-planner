-- Migration 002: places, suggestion settings, and events linked to places.
--
-- A place is somewhere an account likes to go and the weather it suits;
-- suggestions match places against the forecast. user_settings holds how
-- each account wants suggestions (an account without a row uses the
-- defaults). An event made from a suggestion remembers its place;
-- deleting the place keeps the event.
--
-- Safe to run more than once.

CREATE TABLE IF NOT EXISTS place (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    address VARCHAR,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    notes VARCHAR,
    suits_sunny BOOLEAN NOT NULL DEFAULT TRUE,
    suits_cloudy BOOLEAN NOT NULL DEFAULT TRUE,
    suits_rainy BOOLEAN NOT NULL DEFAULT FALSE,
    temp_min INTEGER,
    temp_max INTEGER,
    visit_minutes INTEGER NOT NULL DEFAULT 120,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS place_user_id_idx ON place (user_id);

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE
        REFERENCES app_user(id) ON DELETE CASCADE,
    suggest_days VARCHAR NOT NULL DEFAULT '0123456',  -- Monday 0 .. Sunday 6
    weekday_start INTEGER NOT NULL DEFAULT 18,
    weekday_end INTEGER NOT NULL DEFAULT 21,
    weekend_start INTEGER NOT NULL DEFAULT 9,
    weekend_end INTEGER NOT NULL DEFAULT 18,
    skip_busy_days BOOLEAN NOT NULL DEFAULT FALSE,
    show_today BOOLEAN NOT NULL DEFAULT TRUE
);

ALTER TABLE event ADD COLUMN IF NOT EXISTS place_id INTEGER
    REFERENCES place(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS event_place_id_idx ON event (place_id);
