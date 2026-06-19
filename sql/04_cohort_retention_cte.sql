COPY (
WITH max_date_cte AS (
    SELECT MAX(event_timestamp) as max_date FROM clean_events
),
activity AS (
    SELECT u.user_id, u.cohort_month,
           e.day_offset
    FROM clean_users u
    JOIN clean_events e USING (user_id)
    WHERE e.event_name IN ('session_start','feature_used','trial_started','purchase_completed')
),
flags AS (
    SELECT user_id, cohort_month,
        MAX(CASE WHEN day_offset = 1  THEN 1 ELSE 0 END) AS d1,
        MAX(CASE WHEN day_offset = 7  THEN 1 ELSE 0 END) AS d7,
        MAX(CASE WHEN day_offset = 14 THEN 1 ELSE 0 END) AS d14,
        MAX(CASE WHEN day_offset = 30 THEN 1 ELSE 0 END) AS d30
    FROM activity GROUP BY user_id, cohort_month
),
aggregated AS (
    SELECT cohort_month, COUNT(*) AS cohort_size,
        ROUND(100.0*AVG(d1), 2)  AS d1_retention_pct,
        ROUND(100.0*AVG(d7), 2)  AS d7_retention_pct,
        ROUND(100.0*AVG(d14), 2) AS d14_retention_pct,
        ROUND(100.0*AVG(d30), 2) AS d30_retention_pct
    FROM flags GROUP BY cohort_month
)
SELECT a.cohort_month, a.cohort_size,
    a.d1_retention_pct, a.d7_retention_pct,
    CASE WHEN date_diff('day', CAST(a.cohort_month AS DATE), CAST((SELECT max_date FROM max_date_cte) AS DATE)) >= 14 THEN a.d14_retention_pct ELSE NULL END AS d14_retention_pct,
    CASE WHEN date_diff('day', CAST(a.cohort_month AS DATE), CAST((SELECT max_date FROM max_date_cte) AS DATE)) >= 30 THEN a.d30_retention_pct ELSE NULL END AS d30_retention_pct
FROM aggregated a ORDER BY a.cohort_month
) TO 'data/processed/cohort_retention.csv' (HEADER, DELIMITER ',');