# Dashboard DAX Formulas

These DAX measures are designed for the pre-aggregated outputs from the DuckDB/Python pipeline. Because all SQL joins, window functions, and ML predictions are computed upstream, these measures remain fast in Power BI.

## 1. Funnel & Conversion Rates

```dax
Trial-to-Paid Conversion % =
    DIVIDE(MAX('funnel_summary'[n_purchase]), MAX('funnel_summary'[n_trial]), 0)

Trial Start Rate =
    DIVIDE(MAX('funnel_summary'[n_trial]), MAX('funnel_summary'[n_install]), 0)

Signup Rate =
    DIVIDE(MAX('funnel_summary'[n_signup]), MAX('funnel_summary'[n_install]), 0)
```

## 2. A/B Test & Statistical Lift

```dax
Relative Lift = MAX('ab_test_results'[relative_lift_pct])
// Format as Decimal: 7.75 means +7.75% relative lift

A/B Test Significance Flag =
    IF(MAX('ab_test_results'[is_significant]) = TRUE(),
       "Statistically Significant (α=0.025, Bonferroni)",
       "Not Significant")

P-Value Display =
    "P-Value: " & FORMAT(MAX('ab_test_results'[p_value]), "0.0000")

SRM Check =
    IF(MAX('ab_test_results'[has_srm]) = FALSE(),
       "SRM Passed",
       "SRM FAILED - Check Sample Ratio")

Observed Power =
    MAX('ab_test_results'[observed_power])
// Format as Percentage
```

## 3. Machine Learning Feature Importance

```dax
Top Predictive Feature =
    CALCULATE(
        MAX('model_feature_importance'[Feature]),
        TOPN(1, ALL('model_feature_importance'), 'model_feature_importance'[Importance], DESC)
    )

ML Feature Weight =
    SUM('model_feature_importance'[Importance])
```

## 4. Revenue Impact Estimate

Note: `monthly_trial_volume` (10,000) and `ARPU` ($4.99) come from `config/simulation_config.yaml`.

```dax
Estimated ARPU = 4.99

Monthly Trial Volume = 10000

Baseline Monthly Conversions =
    [Monthly Trial Volume] * MAX('ab_test_results'[control_rate])
// control_rate is decimal (0.44), result: ~4,420 conversions/month

Relative Lift Decimal =
    MAX('ab_test_results'[relative_lift_pct]) / 100
// relative_lift_pct is 7.754 (% form), divide by 100 for decimal: 0.0775

Estimated Incremental Subscribers =
    [Baseline Monthly Conversions] * [Relative Lift Decimal]

Projected Incremental MRR =
    [Estimated Incremental Subscribers] * [Estimated ARPU]
```

## 5. Drop-off Curve Analytics

```dax
Daily Active Percentage =
    MAX('trial_dropoff_curve'[pct_active])

Day-over-Day Drop (pp) =
    MAX('trial_dropoff_curve'[day_over_day_change_pp])

Steepest Drop Day =
    MINX(
        TOPN(1, 'trial_dropoff_curve', 'trial_dropoff_curve'[day_over_day_change_pp], ASC),
        'trial_dropoff_curve'[day_offset]
    )

## 6. Feature Adoption Chi-Square Test

```dax
Chi-Square Statistic = MAX('behavioral_chi2_results'[chi2_stat])

Chi-Square P-Value = MAX('behavioral_chi2_results'[p_value])
// Format as Scientific: ~1.0e-300

Chi-Square Significant (Bonferroni) =
    IF(MAX('behavioral_chi2_results'[is_significant]) = TRUE(),
       "Significant (α=0.025)",
       "Not Significant")
```

## 7. Advanced Window-Function Analytics

```dax
Top 10% Avg Sessions = 
    CALCULATE(MAX('advanced_analytics'[value]),
        'advanced_analytics'[metric] = "top_10_pct_avg_sessions")

Median Lifetime Days =
    CALCULATE(VALUE(MAX('advanced_analytics'[value])),
        'advanced_analytics'[metric] = "median_lifetime_days")

Weekly Conversion Range =
    CALCULATE(MAX('advanced_analytics'[value]),
        'advanced_analytics'[metric] = "weekly_conv_rate_max")
    - CALCULATE(MAX('advanced_analytics'[value]),
        'advanced_analytics'[metric] = "weekly_conv_rate_min")
```
```
