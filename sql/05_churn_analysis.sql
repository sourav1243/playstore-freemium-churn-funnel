COPY (
WITH trial_users AS (
    SELECT user_id, event_timestamp AS trial_start_ts, day_offset AS trial_day_offset
    FROM clean_events WHERE event_name = 'trial_started'
),
daily_activity AS (
    SELECT t.user_id, e.day_offset - t.trial_day_offset AS trial_day_offset
    FROM trial_users t
    JOIN clean_events e USING (user_id)
    WHERE e.event_name IN ('session_start','feature_used')
      AND (e.day_offset - t.trial_day_offset) BETWEEN 0 AND 30
),
daily_pct AS (
    SELECT trial_day_offset as day_offset,
           ROUND(100.0*COUNT(DISTINCT user_id)/(SELECT COUNT(*) FROM trial_users), 2) AS pct_active
    FROM daily_activity GROUP BY trial_day_offset
)
SELECT day_offset, pct_active,
       ROUND(pct_active - LAG(pct_active) OVER (ORDER BY day_offset), 2) AS day_over_day_change_pp
FROM daily_pct ORDER BY day_offset
) TO 'data/processed/trial_dropoff_curve.csv' (HEADER, DELIMITER ',');

COPY (
WITH trial_users AS (
    SELECT DISTINCT user_id FROM clean_events WHERE event_name = 'trial_started'
),
users_collab AS (
    SELECT user_id, 1 as used_collab
    FROM clean_events WHERE event_subtype = 'collaboration_feature'
      AND user_id IN (SELECT user_id FROM trial_users)
    GROUP BY user_id
),
users_purchased AS (
    SELECT user_id, 1 as purchased
    FROM clean_events WHERE event_name = 'purchase_completed'
      AND user_id IN (SELECT user_id FROM trial_users)
    GROUP BY user_id
)
SELECT
    COALESCE(uc.used_collab, 0) AS used_collab,
    COUNT(t.user_id) as total_users,
    SUM(COALESCE(up.purchased, 0)) as total_purchases,
    ROUND(100.0*SUM(COALESCE(up.purchased, 0))/COUNT(t.user_id), 2) as conversion_rate
FROM trial_users t
LEFT JOIN users_collab uc ON t.user_id = uc.user_id
LEFT JOIN users_purchased up ON t.user_id = up.user_id
GROUP BY used_collab
) TO 'data/processed/behavioral_stats.csv' (HEADER, DELIMITER ',');