COPY (
WITH funnel_flags AS (
    SELECT u.user_id, u.app_id,
        MAX(CASE WHEN e.event_name = 'account_created' THEN 1 ELSE 0 END) AS reached_signup,
        MAX(CASE WHEN e.event_name = 'first_session' THEN 1 ELSE 0 END) AS reached_first_session,
        MAX(CASE WHEN e.event_name = 'feature_used' THEN 1 ELSE 0 END) AS reached_feature,
        MAX(CASE WHEN e.event_name = 'trial_started' THEN 1 ELSE 0 END) AS reached_trial,
        MAX(CASE WHEN e.event_name = 'purchase_completed' THEN 1 ELSE 0 END) AS reached_purchase
    FROM clean_users u
    LEFT JOIN clean_events e USING (user_id)
    GROUP BY u.user_id, u.app_id
)
SELECT
    COUNT(*) AS n_install,
    SUM(reached_signup) AS n_signup,
    SUM(reached_first_session) AS n_first_session,
    SUM(reached_feature) AS n_feature,
    SUM(reached_trial) AS n_trial,
    SUM(reached_purchase) AS n_purchase,
    ROUND(100.0*SUM(reached_signup)/COUNT(*), 2) AS pct_install_to_signup,
    ROUND(100.0*SUM(reached_first_session)/NULLIF(SUM(reached_signup),0), 2) AS pct_signup_to_session,
    ROUND(100.0*SUM(reached_feature)/NULLIF(SUM(reached_first_session),0), 2) AS pct_session_to_feature,
    ROUND(100.0*SUM(reached_trial)/NULLIF(SUM(reached_feature),0), 2) AS pct_feature_to_trial,
    ROUND(100.0*SUM(reached_purchase)/NULLIF(SUM(reached_trial),0), 2) AS pct_trial_to_purchase
FROM funnel_flags
) TO 'data/processed/funnel_summary.csv' (HEADER, DELIMITER ',');