COPY (
WITH user_sessions AS (
    SELECT user_id, COUNT(*) as session_count
    FROM clean_events WHERE event_name = 'session_start'
    GROUP BY user_id
),
user_purchases AS (
    SELECT user_id, MAX(day_offset) as purchase_day
    FROM clean_events WHERE event_name = 'purchase_completed'
    GROUP BY user_id
),
user_first_event AS (
    SELECT user_id, MIN(day_offset) as first_event_day
    FROM clean_events GROUP BY user_id
),
user_last_event AS (
    SELECT user_id, MAX(day_offset) as last_event_day
    FROM clean_events GROUP BY user_id
),
user_lifetime AS (
    SELECT user_id, last_event_day - first_event_day as lifetime_days
    FROM user_first_event JOIN user_last_event USING (user_id)
),
ranked_users AS (
    SELECT
        u.user_id,
        COALESCE(us.session_count, 0) as session_count,
        COALESCE(up.purchase_day, -1) as purchase_day,
        RANK() OVER (ORDER BY COALESCE(us.session_count, 0) DESC) as session_rank,
        NTILE(4) OVER (ORDER BY COALESCE(us.session_count, 0) DESC) as engagement_quartile,
        PERCENT_RANK() OVER (ORDER BY COALESCE(us.session_count, 0) DESC) as engagement_pct_rank
    FROM clean_users u
    LEFT JOIN user_sessions us USING (user_id)
    LEFT JOIN user_purchases up USING (user_id)
),
weekly_cohorts AS (
    SELECT
        date_trunc('week', CAST(u.install_timestamp AS DATE)) as cohort_week,
        COUNT(DISTINCT u.user_id) as installs,
        COUNT(DISTINCT CASE WHEN up.purchase_day >= 0 THEN u.user_id END) as conversions
    FROM clean_users u
    LEFT JOIN user_purchases up USING (user_id)
    WHERE u.install_timestamp IS NOT NULL
    GROUP BY date_trunc('week', CAST(u.install_timestamp AS DATE))
)
SELECT 'top_10_pct_avg_sessions' as metric, COALESCE(ROUND(AVG(session_count), 1), 0) as value
FROM ranked_users WHERE engagement_pct_rank <= 0.1
UNION ALL
SELECT 'median_user_sessions', COALESCE(ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY session_count), 1), 0)
FROM ranked_users
UNION ALL
SELECT 'bottom_10_pct_avg_sessions', COALESCE(ROUND(AVG(session_count), 1), 0)
FROM ranked_users WHERE engagement_pct_rank >= 0.9
UNION ALL
SELECT 'q1_avg_sessions', COALESCE(ROUND(AVG(session_count), 1), 0)
FROM ranked_users WHERE engagement_quartile = 1
UNION ALL
SELECT 'q2_avg_sessions', COALESCE(ROUND(AVG(session_count), 1), 0)
FROM ranked_users WHERE engagement_quartile = 2
UNION ALL
SELECT 'q3_avg_sessions', COALESCE(ROUND(AVG(session_count), 1), 0)
FROM ranked_users WHERE engagement_quartile = 3
UNION ALL
SELECT 'q4_avg_sessions', COALESCE(ROUND(AVG(session_count), 1), 0)
FROM ranked_users WHERE engagement_quartile = 4
UNION ALL
SELECT 'avg_lifetime_days', COALESCE(ROUND(AVG(lifetime_days), 1), 0)
FROM user_lifetime
UNION ALL
SELECT 'max_lifetime_days', COALESCE(CAST(MAX(lifetime_days) AS VARCHAR), '0')
FROM user_lifetime
UNION ALL
SELECT 'median_lifetime_days', COALESCE(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY lifetime_days) AS VARCHAR), '0')
FROM user_lifetime
UNION ALL
SELECT 'weekly_conv_rate_min', COALESCE(ROUND(MIN(CAST(conversions AS DOUBLE) / NULLIF(installs, 0)) * 100, 2), 0)
FROM weekly_cohorts
UNION ALL
SELECT 'weekly_conv_rate_max', COALESCE(ROUND(MAX(CAST(conversions AS DOUBLE) / NULLIF(installs, 0)) * 100, 2), 0)
FROM weekly_cohorts
) TO 'data/processed/advanced_analytics.csv' (HEADER, DELIMITER ',');
