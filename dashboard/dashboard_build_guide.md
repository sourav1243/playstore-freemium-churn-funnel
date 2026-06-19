# Power BI Elite Dashboard — Build Guide

This guide provides step-by-step instructions to build an interactive Power BI dashboard
using the pipeline-generated data exports.

## Quick Start: Import Pre-Built Excel

1. Open Power BI Desktop
2. **Get Data → Excel** → Select `dashboard/exports/powerbi_dashboard_data.xlsx`
3. All 9 tables load automatically with correct column names
4. **Model View**: Tables are pre-aggregated — no relationships needed
5. **Start building pages** using the layout below

## Dashboard Pages & Visual Layout

### Page 1: Executive Summary (KPIs)
| Visual | Data Source | Fields |
|--------|-------------|--------|
| KPI Card | `funnel_summary` | `n_install` — "Total Installs" |
| KPI Card | `funnel_summary` | `n_trial` / `n_install` — "Trial Start Rate" |
| KPI Card | `funnel_summary` | `n_purchase` / `n_trial` — "Trial-to-Paid Conversion" |
| KPI Card | `ab_test_results` | `relative_lift_pct` — "A/B Relative Lift" |
| Donut Chart | `user_segmentation` | `user_segment` (Legend), `pct_of_total` (Values) |
| Bar Chart | `model_feature_importance` | `Feature` (Axis), `Importance` (Values) |

### Page 2: Funnel & Churn Analysis
- **Stacked Bar Chart** (funnel): 6 stages from `funnel_summary`
- **Line Chart** (trial drop-off): `trial_dropoff_curve` — X=`day_offset`, Y=`pct_active`
- **Marker**: Add analytics annotation on Day 6 (steepest drop: 27.1pp)

### Page 3: Cohort Retention
- **Matrix Visual**: `cohort_retention`
  - Rows: `cohort_month`
  - Columns: `d1_retention_pct`, `d7_retention_pct`, `d14_retention_pct`, `d30_retention_pct`
  - Apply conditional formatting (background color scale: white → dark blue)

### Page 4: A/B Test & ML
- **Cards**: Control Rate (45.2%), Treatment Rate (47.3%), Lift (+4.5%)
- **Horizontal Bar Chart**: `model_feature_importance` — Feature vs Importance
- **DAX Measures**: See `metrics_formulas.md` for P-value display, SRM check, significance flags

### Page 5: Advanced Analytics
- **Cards**: From `advanced_analytics` — Avg Lifetime, Top 10% Sessions, Weekly Conversion Range
- **Table**: `behavioral_stats` — Collaboration Feature vs Conversion comparison

## DAX Measures to Create

```dax
Trial-to-Paid Conversion % = DIVIDE(MAX('funnel_summary'[n_purchase]), MAX('funnel_summary'[n_trial]), 0)

Relative Lift = MAX('ab_test_results'[relative_lift_pct])

P-Value Display = "P-Value: " & FORMAT(MAX('ab_test_results'[p_value]), "0.0000")

Significance Flag = IF(MAX('ab_test_results'[is_significant]) = TRUE(), "Significant (α=0.025)", "Not Significant")

Top Feature = CALCULATE(MAX('model_feature_importance'[Feature]), TOPN(1, ALL('model_feature_importance'), 'model_feature_importance'[Importance], DESC))
```

## Live Data Summary (from pipeline run)

| Metric | Value |
|--------|-------|
| Total Installs | 115,022 |
| Signup Rate | 85.0% |
| Trial Starters | 47,795 |
| Trial-to-Paid Conversion | 46.3% |
| A/B Relative Lift | +4.5% (p=4.10e-06) |
| Steepest Drop | Day 6 (27.1pp) |
| Collab Conversion Rate | 77.2% (vs 32.6%) |
| Control Group Size | 23795 |
| Treatment Group Size | 24000 |
| ML ROC-AUC | 0.68 (5-Fold CV) |
| Churned Users | 80.4% |

## Interview Talking Points

- **Power BI is the presentation layer only** — all heavy compute (SQL window functions, CTEs, ML, statistics) executes headlessly in DuckDB/Python
- **Pre-experiment power analysis**: Uses config baseline (12%) and MDE (8%), not observed effect size — no post-hoc invalidity
- **Bot filter validation**: Precision/Recall against ground-truth labels — a rare sophistication for synthetic data projects
- **Bonferroni correction**: Adjusted α=0.025 for two tests — demonstrates statistical rigor
- **Cohort maturity masking**: D14/D30 cells are NULL for immature cohorts — prevents misleading retention reporting
- **Day-7 activity spike**: Activity rises from 20.0% (Day 6) to 33.5% (Day 7) as users return for purchase/expiration
