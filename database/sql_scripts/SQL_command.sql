-- Schema for WeatherWise Planner (matches models/db_models).
-- Safe to re-run: drops and recreates the tables, so ALL DATA IS LOST.

DROP TABLE IF EXISTS eventxprofile;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS profile;
DROP TABLE IF EXISTS app_user;

-- Table: app_user
CREATE TABLE app_user (
    id SERIAL PRIMARY KEY,
    google_sub VARCHAR UNIQUE,
    email VARCHAR,
    name VARCHAR NOT NULL,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

-- Table: event
CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    location VARCHAR NOT NULL
);

-- Table: profile
CREATE TABLE profile (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    user_id INTEGER REFERENCES app_user(id) ON DELETE CASCADE
);

CREATE INDEX profile_user_id_idx ON profile (user_id);

-- Table: eventxprofile
CREATE TABLE eventxprofile (
    id SERIAL PRIMARY KEY,
    eventid INTEGER NOT NULL,
    profileid INTEGER NOT NULL,

    CONSTRAINT fk_event
        FOREIGN KEY(eventid) REFERENCES event(id),

    CONSTRAINT fk_profile
        FOREIGN KEY(profileid) REFERENCES profile(id)
);


-- Sample Data Insertion
INSERT INTO event (name, start_time, end_time, location) VALUES
('Tech Conference', '2026-10-12 09:00:00', '2026-10-12 17:00:00', 'London'),
('C++ Workshop', '2026-10-15 10:00:00', '2026-10-15 15:00:00', 'Online'),
('Music Concert', '2026-10-20 14:00:00', '2026-10-20 22:00:00', 'Manchester');

INSERT INTO profile (name) VALUES
('A Profile'),
('B Profile'),
('C Profile');

INSERT INTO eventxprofile (eventid, profileid) VALUES
(1, 1),
(1, 2),
(2, 3);
