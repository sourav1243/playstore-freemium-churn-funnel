CREATE OR REPLACE TABLE clean_users AS
WITH device_reuse AS (
    SELECT device_id, COUNT(DISTINCT user_id) AS distinct_users_on_device
    FROM users GROUP BY device_id
),
flagged AS (
    SELECT u.user_id,
        CASE
            WHEN dr.distinct_users_on_device > 200 THEN TRUE
            WHEN u.acquisition_channel = 'internal_qa' AND u.email ILIKE '%test%' THEN TRUE
            WHEN u.email ILIKE '%test%' OR u.email ILIKE '%qa%' OR u.email ILIKE '%bot%' THEN TRUE
            ELSE FALSE
        END AS is_suspected_bot
    FROM users u
    LEFT JOIN device_reuse dr ON u.device_id = dr.device_id
)
SELECT u.* FROM users u
JOIN flagged f USING (user_id)
WHERE f.is_suspected_bot = FALSE;

CREATE OR REPLACE TABLE clean_events AS
SELECT e.* FROM events e
JOIN clean_users cu ON e.user_id = cu.user_id;