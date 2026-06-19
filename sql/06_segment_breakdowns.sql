COPY (
WITH user_sessions AS (
    SELECT user_id, COUNT(*) as session_count
    FROM clean_events WHERE event_name = 'session_start'
    GROUP BY user_id
),
user_purchases AS (
    SELECT user_id FROM clean_events WHERE event_name = 'purchase_completed' GROUP BY user_id
),
last_activity AS (
    SELECT user_id, MAX(event_timestamp) as last_event_ts FROM clean_events GROUP BY user_id
),
max_date_cte AS (
    SELECT MAX(event_timestamp) as max_date FROM clean_events
),
percentiles AS (
    SELECT percentile_cont(0.9) WITHIN GROUP (ORDER BY session_count) as p90_sessions
    FROM user_sessions
),
segmentation AS (
    SELECT
        u.user_id,
        CASE WHEN up.user_id IS NOT NULL THEN 'Converted'
             WHEN la.last_event_ts IS NULL THEN 'Churned (>14d inactive)'
             WHEN date_diff('day', CAST(la.last_event_ts AS DATE), CAST((SELECT max_date FROM max_date_cte) AS DATE)) > 14 THEN 'Churned (>14d inactive)'
             WHEN us.session_count >= (SELECT p90_sessions FROM percentiles) THEN 'Power User'
             ELSE 'At-Risk / Average'
        END AS user_segment
    FROM clean_users u
    LEFT JOIN user_sessions us USING (user_id)
    LEFT JOIN user_purchases up USING (user_id)
    LEFT JOIN last_activity la USING (user_id)
)
SELECT user_segment, COUNT(*) as user_count, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM clean_users), 2) as pct_of_total
FROM segmentation GROUP BY user_segment
) TO 'data/processed/user_segmentation.csv' (HEADER, DELIMITER ',');