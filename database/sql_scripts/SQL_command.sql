-- Table: event_mock
CREATE TABLE event (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    "end" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    location VARCHAR NULL
);

-- Table: profile_mock
CREATE TABLE profile (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL
);

-- Table: event_profile_mock
CREATE TABLE eventxprofile (
    id SERIAL PRIMARY KEY,
    eventid INTEGER NOT NULL,
    profileid INTEGER NOT NULL,

    CONSTRAINT fk_event
        FOREIGN KEY(eventid) REFERENCES event_mock(id),

    CONSTRAINT fk_profile
        FOREIGN KEY(profileid) REFERENCES profile_mock(id)
);


-- Sample Data Insertion
INSERT INTO event (name, start, "end", location) VALUES
('Tech Conference', '2025-12-01 09:00:00', '2025-12-01 17:00:00', 'London'),
('C++ Workshop', '2025-12-05 10:00:00', '2025-12-05 15:00:00', NULL),
('Music Concert', '2025-12-10 14:00:00', '2025-12-10 22:00:00', 'Manchester');

INSERT INTO profile (name) VALUES
('A Profile'),
('B Profile'),
('C Profile');

INSERT INTO eventxprofile (eventid, profileid) VALUES
(1, 1), 
(1, 2), 
(2, 3);
