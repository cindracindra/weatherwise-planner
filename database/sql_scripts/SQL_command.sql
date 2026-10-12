-- Schema for WeatherWise Planner (matches models/db_models).
-- Safe to re-run: drops and recreates the tables, so ALL DATA IS LOST.
-- To update a database that is already in use, run the numbered
-- migrations (001_accounts.sql, ...) instead.

DROP TABLE IF EXISTS eventxprofile;
DROP TABLE IF EXISTS profile;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS user_settings;
DROP TABLE IF EXISTS place;
DROP TABLE IF EXISTS app_user;

-- Table: app_user (one per person who signs in)
CREATE TABLE app_user (
    id SERIAL PRIMARY KEY,
    google_sub VARCHAR UNIQUE,
    email VARCHAR,
    name VARCHAR NOT NULL,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

-- Table: place (somewhere an account likes to go, and the weather it suits)
CREATE TABLE place (
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

CREATE INDEX place_user_id_idx ON place (user_id);

-- Table: user_settings (how each account wants suggestions; optional)
CREATE TABLE user_settings (
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

-- Table: event (each belongs to one account, optionally at a place)
CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    location VARCHAR NOT NULL,
    user_id INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    place_id INTEGER REFERENCES place(id) ON DELETE SET NULL
);

CREATE INDEX event_user_id_idx ON event (user_id);
CREATE INDEX event_place_id_idx ON event (place_id);


-- Sample data: one account with a few events
INSERT INTO app_user (name, is_demo) VALUES ('Sample user', FALSE);

INSERT INTO event (name, start_time, end_time, location, user_id) VALUES
('Tech Conference', '2026-10-12 09:00:00', '2026-10-12 17:00:00', 'London', 1),
('C++ Workshop', '2026-10-15 10:00:00', '2026-10-15 15:00:00', 'Online', 1),
('Music Concert', '2026-10-20 14:00:00', '2026-10-20 22:00:00', 'Manchester', 1);
