CREATE OR REPLACE TABLE apps (
    app_id INTEGER PRIMARY KEY,
    app_name VARCHAR,
    category VARCHAR,
    Rating DOUBLE,
    Installs BIGINT,
    Price DOUBLE
);

CREATE OR REPLACE TABLE users (
    user_id INTEGER PRIMARY KEY,
    app_id INTEGER,
    install_timestamp TIMESTAMP,
    cohort_month DATE,
    device_id VARCHAR,
    country VARCHAR,
    acquisition_channel VARCHAR,
    email VARCHAR,
    ab_group VARCHAR,
    is_bot_ground_truth BOOLEAN
);

CREATE OR REPLACE TABLE events (
    event_id BIGINT PRIMARY KEY,
    user_id INTEGER,
    app_id INTEGER,
    event_name VARCHAR,
    event_subtype VARCHAR,
    event_timestamp TIMESTAMP,
    day_offset INTEGER
);

COPY apps FROM 'data/processed/apps_clean.csv' (HEADER, DELIMITER ',');
COPY users FROM 'data/synthetic/users.csv' (HEADER, DELIMITER ',');
COPY events FROM 'data/synthetic/events.csv' (HEADER, DELIMITER ',');
