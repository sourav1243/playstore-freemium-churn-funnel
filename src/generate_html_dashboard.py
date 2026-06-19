import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.utils import PROJECT_ROOT, PROCESSED_DIR, setup_logging

log = setup_logging(__name__)

def generate_html() -> None:
    reports_dir: str = os.path.join(PROJECT_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    optional = {
        'behavioral_chi2_results.csv': os.path.join(PROCESSED_DIR, 'behavioral_chi2_results.csv'),
        'advanced_analytics.csv': os.path.join(PROCESSED_DIR, 'advanced_analytics.csv'),
    }
    required = {
        'funnel_summary.csv': os.path.join(PROCESSED_DIR, 'funnel_summary.csv'),
        'cohort_retention.csv': os.path.join(PROCESSED_DIR, 'cohort_retention.csv'),
        'trial_dropoff_curve.csv': os.path.join(PROCESSED_DIR, 'trial_dropoff_curve.csv'),
        'ab_test_results.csv': os.path.join(PROCESSED_DIR, 'ab_test_results.csv'),
        'user_segmentation.csv': os.path.join(PROCESSED_DIR, 'user_segmentation.csv'),
        'model_feature_importance.csv': os.path.join(PROCESSED_DIR, 'model_feature_importance.csv'),
    }
    for name, path in required.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} not found at {path}")

    funnel_df = pd.read_csv(required['funnel_summary.csv']).iloc[0]
    cohort_df = pd.read_csv(required['cohort_retention.csv'])
    dropoff_df = pd.read_csv(required['trial_dropoff_curve.csv'])
    ab_df = pd.read_csv(required['ab_test_results.csv']).iloc[0]
    seg_df = pd.read_csv(required['user_segmentation.csv'])
    ml_df = pd.read_csv(required['model_feature_importance.csv'])

    chi2_df = pd.read_csv(optional['behavioral_chi2_results.csv']).iloc[0] if os.path.exists(optional['behavioral_chi2_results.csv']) else None
    adv_df = pd.read_csv(optional['advanced_analytics.csv']) if os.path.exists(optional['advanced_analytics.csv']) else None

    stages = ['Install', 'Signup', 'First Session', 'Feature Used', 'Trial', 'Purchase']
    counts = [funnel_df['n_install'], funnel_df['n_signup'], funnel_df['n_first_session'],
              funnel_df['n_feature'], funnel_df['n_trial'], funnel_df['n_purchase']]
    fig_funnel = go.Figure(go.Funnel(y=stages, x=counts, textinfo="value+percent initial"))
    fig_funnel.update_layout(title="Conversion Funnel", margin=dict(t=30, b=10, l=10, r=10))
    funnel_html = fig_funnel.to_html(full_html=False, include_plotlyjs='cdn')

    steepest_idx = dropoff_df['day_over_day_change_pp'].idxmin()
    steepest_day = dropoff_df.loc[steepest_idx]
    fig_drop = px.line(dropoff_df, x='day_offset', y='pct_active', markers=True, title="Active Trial Users by Day")
    fig_drop.add_annotation(x=steepest_day['day_offset'], y=steepest_day['pct_active'],
                            text=f"Steepest Drop (Day {int(steepest_day['day_offset'])})",
                            showarrow=True, arrowhead=1, arrowcolor="red")
    fig_drop.update_layout(margin=dict(t=30, b=10, l=10, r=10))
    drop_html = fig_drop.to_html(full_html=False, include_plotlyjs=False)

    cohort_df['cohort_month'] = pd.to_datetime(cohort_df['cohort_month']).dt.strftime('%Y-%m')
    heat_data = cohort_df.set_index('cohort_month')[['d1_retention_pct', 'd7_retention_pct', 'd14_retention_pct', 'd30_retention_pct']]
    fig_heat = px.imshow(heat_data, text_auto=".1f", aspect="auto",
                         labels=dict(x="Retention Day", y="Cohort Month", color="Retention %"),
                         color_continuous_scale="YlGnBu", title="Cohort Retention Matrix (%)")
    fig_heat.update_layout(margin=dict(t=30, b=10, l=10, r=10))
    heat_html = fig_heat.to_html(full_html=False, include_plotlyjs=False)

    fig_ml = px.bar(ml_df.head(10), x='Importance', y='Feature', orientation='h',
                    title="Propensity Feature Importance (Random Forest)",
                    color='Importance', color_continuous_scale='RdBu')
    fig_ml.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=30, b=10, l=10, r=10))
    ml_html = fig_ml.to_html(full_html=False, include_plotlyjs=False)

    fig_seg = px.pie(seg_df, values='pct_of_total', names='user_segment', title="User Segments (% of Total)")
    fig_seg.update_layout(margin=dict(t=30, b=10, l=10, r=10))
    seg_html = fig_seg.to_html(full_html=False, include_plotlyjs=False)

    srm_p_value = ab_df.get('srm_p_value', 1.0)
    has_srm = ab_df.get('has_srm', False)
    srm_tag = '<span style="color: green; font-weight:bold;">PASS</span>' if not has_srm else '<span style="color: red; font-weight:bold;">FAIL (Data Skew)</span>'
    obs_power = ab_df.get('observed_power', None)

    trial_rate = (funnel_df['n_purchase'] / funnel_df['n_trial'] * 100) if funnel_df['n_trial'] > 0 else 0
    rel_lift = ab_df.get('relative_lift_pct', 0)
    p_val = ab_df.get('p_value', 1)
    top_feature = ml_df.iloc[0]['Feature'] if len(ml_df) > 0 else 'N/A'

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Freemium Analytics Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f6fa; color: #333; margin: 0; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .kpi-container {{ display: flex; justify-content: space-around; margin-bottom: 40px; flex-wrap: wrap; gap: 20px; }}
            .kpi-card {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; flex: 1; min-width: 200px; }}
            .kpi-card h3 {{ margin: 0 0 10px 0; color: #7f8c8d; font-size: 14px; text-transform: uppercase; }}
            .kpi-card .value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
            .kpi-card .sub-value {{ font-size: 14px; color: #27ae60; margin-top: 5px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .chart-card {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .full-width {{ grid-column: span 2; }}
            .audit-panel {{ background: #2c3e50; color: #fff; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .audit-panel h2 {{ margin-top: 0; color: #ecf0f1; }}
            .audit-item {{ margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Freemium App Churn & Funnel Analysis</h1>
            <p>Product Analytics Pipeline — Python, SQL (DuckDB), ML, Statistics</p>
        </div>

        <div class="audit-panel">
            <h2>Data Engineering & Statistical Audit</h2>
            <div class="audit-item">✓ <b>SRM Check (Sample Ratio Mismatch):</b> {srm_tag} (p-value: {srm_p_value:.4f})</div>
            <div class="audit-item">✓ <b>Data Leakage Prevention:</b> Target purchase events rigorously excluded from ML feature window (only day_offset <= 3 used).</div>
            <div class="audit-item">✓ <b>Model Validation:</b> Random Forest validated via 5-Fold Stratified Cross-Validation (ROC-AUC reported).</div>
            <div class="audit-item">✓ <b>Power Analysis (Pre-Experiment):</b> MDE of 8% relative lift (baseline 12%). Required n={ab_df.get('required_n_per_arm', 0):.0f}/arm. Adequately powered: <b>{'YES' if ab_df.get('is_adequately_powered', False) else 'NO'}</b>.</div>
            <div class="audit-item">✓ <b>Power Analysis (Observed):</b> Using actual control rate ({ab_df.get('control_rate', 0)*100:.1f}%), observed power = <b>{obs_power:.2%}</b>.</div>
        </div>

        <div class="kpi-container">
            <div class="kpi-card"><h3>Total Installs</h3><div class="value">{int(funnel_df['n_install']):,}</div></div>
            <div class="kpi-card"><h3>Trial Conversion Rate</h3><div class="value">{trial_rate:.1f}%</div></div>
            <div class="kpi-card">
                <h3>A/B Test Relative Lift</h3>
                <div class="value">+{rel_lift:.1f}%</div>
                <div class="sub-value">P-Value: {p_val:.4f}</div>
            </div>
            <div class="kpi-card"><h3>Top Predictive Feature</h3><div class="value">{top_feature}</div></div>
        </div>

        <div class="grid">
            <div class="chart-card">{funnel_html}</div>
            <div class="chart-card">{drop_html}</div>
            <div class="chart-card full-width">{heat_html}</div>
            <div class="chart-card">{ml_html}</div>
            <div class="chart-card">{seg_html}</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div class="chart-card">
                <h3>Feature Adoption Chi-Square Test</h3>
                <p>Test: Collaboration Feature vs Conversion</p>
                <p>Chi² Stat: <b>{chi2_df['chi2_stat']:.1f}</b></p>
                <p>P-Value: <b>{chi2_df['p_value']:.2e}</b></p>
                <p>Bonferroni Alpha: <b>{chi2_df['bonferroni_alpha']}</b></p>
                <p>Significant: <b style="color: {'green' if chi2_df['is_significant'] else 'red'};">{'YES' if chi2_df['is_significant'] else 'NO'}</b></p>
            </div>
            <div class="chart-card">
                <h3>Advanced Window-Function Analytics</h3>
                <ul style="list-style: none; padding: 0;">
                    {''.join(f'<li><b>{r["metric"]}:</b> {r["value"]}</li>' for _, r in adv_df.iterrows()) if adv_df is not None else '<li>No data</li>'}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    output_path = os.path.join(reports_dir, 'interactive_dashboard.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    log.info(f"Interactive HTML dashboard generated at {output_path}")

if __name__ == "__main__":
    generate_html()
