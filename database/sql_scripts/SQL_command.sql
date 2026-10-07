-- Schema for WeatherWise Planner (matches models/db_models).
-- Safe to re-run: drops and recreates the tables, so ALL DATA IS LOST.
-- To update a database that is already in use, run the numbered
-- migrations (001_accounts.sql, ...) instead.

DROP TABLE IF EXISTS eventxprofile;
DROP TABLE IF EXISTS profile;
DROP TABLE IF EXISTS event;
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

-- Table: event (each belongs to one account)
CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    location VARCHAR NOT NULL,
    user_id INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE
);

CREATE INDEX event_user_id_idx ON event (user_id);


-- Sample data: one account with a few events
INSERT INTO app_user (name, is_demo) VALUES ('Sample user', TRUE);

INSERT INTO event (name, start_time, end_time, location, user_id) VALUES
('Tech Conference', '2026-10-12 09:00:00', '2026-10-12 17:00:00', 'London', 1),
('C++ Workshop', '2026-10-15 10:00:00', '2026-10-15 15:00:00', 'Online', 1),
('Music Concert', '2026-10-20 14:00:00', '2026-10-20 22:00:00', 'Manchester', 1);
