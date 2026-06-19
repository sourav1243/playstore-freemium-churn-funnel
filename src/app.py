import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.utils import PROJECT_ROOT, PROCESSED_DIR

st.set_page_config(page_title="Freemium Analytics | Data Analytics Portfolio", layout="wide", page_icon="📊")

@st.cache_data
def load_data():
    files = {
        'funnel': os.path.join(PROCESSED_DIR, 'funnel_summary.csv'),
        'cohort': os.path.join(PROCESSED_DIR, 'cohort_retention.csv'),
        'dropoff': os.path.join(PROCESSED_DIR, 'trial_dropoff_curve.csv'),
        'ab': os.path.join(PROCESSED_DIR, 'ab_test_results.csv'),
        'seg': os.path.join(PROCESSED_DIR, 'user_segmentation.csv'),
        'ml': os.path.join(PROCESSED_DIR, 'model_feature_importance.csv'),
        'chi2': os.path.join(PROCESSED_DIR, 'behavioral_chi2_results.csv'),
        'advanced': os.path.join(PROCESSED_DIR, 'advanced_analytics.csv'),
    }
    missing = [k for k, v in files.items() if not os.path.exists(v)]
    if missing:
        st.error(f"Required files not found: {', '.join(missing)}. Run the pipeline first: `python src/run_pipeline.py`")
        st.info("Need to run the full pipeline to generate data. See README for setup instructions.")
        st.stop()
    try:
        return {k: pd.read_csv(v) for k, v in files.items()}
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

data = load_data()
funnel_df = data['funnel'].iloc[0]
cohort_df = data['cohort']
dropoff_df = data['dropoff']
ab_df = data['ab'].iloc[0]
seg_df = data['seg']
ml_df = data['ml']
chi2_df = data['chi2'].iloc[0] if data['chi2'] is not None else None
adv_df = data['advanced']

st.sidebar.title("Navigation")
st.sidebar.markdown("---")
page = st.sidebar.radio("Go to", ["Executive Summary", "Funnel & Churn", "Cohort Retention", "A/B Test & ML Model", "Behavioral & Advanced Analytics"])

if page == "Executive Summary":
    st.title("Executive Summary: Freemium App Analysis")
    st.markdown("This dashboard presents a comprehensive analysis of the freemium conversion funnel for Google Play Store productivity apps. All metrics are computed from generated synthetic behavioral data.")

    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Installs", f"{int(funnel_df['n_install']):,}")
    col2.metric("Trial Starters", f"{int(funnel_df['n_trial']):,}")
    trial_rate = (funnel_df['n_trial'] / funnel_df['n_install']) * 100
    col3.metric("Trial Start Rate", f"{trial_rate:.1f}%")
    conv_rate = (funnel_df['n_purchase'] / funnel_df['n_trial']) * 100 if funnel_df['n_trial'] > 0 else 0
    col4.metric("Trial-to-Paid Conversion", f"{conv_rate:.1f}%")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### User Segmentation Breakdown")
        fig = px.pie(seg_df, values='pct_of_total', names='user_segment', title="User Segments (% of Total)", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### Pipeline Overview")
        stages_count = [int(funnel_df['n_install']), int(funnel_df['n_signup']), int(funnel_df['n_trial']), int(funnel_df['n_purchase'])]
        stages_name = ['Installs', 'Signups', 'Trials', 'Purchases']
        fig2 = px.bar(x=stages_name, y=stages_count, title="Funnel Overview", color=stages_name, color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig2, use_container_width=True)

elif page == "Funnel & Churn":
    st.title("Funnel Analysis & Trial Drop-off")

    st.subheader("Conversion Funnel")
    stages = ['Install', 'Signup', 'First Session', 'Feature Used', 'Trial', 'Purchase']
    counts = [
        int(funnel_df['n_install']), int(funnel_df['n_signup']),
        int(funnel_df['n_first_session']), int(funnel_df['n_feature']),
        int(funnel_df['n_trial']), int(funnel_df['n_purchase'])
    ]
    fig_funnel = go.Figure(go.Funnel(y=stages, x=counts, textinfo="value+percent initial"))
    fig_funnel.update_layout(title="User Journey Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)

    st.markdown("---")
    st.subheader("Trial Drop-off Curve (Identifying the Cliff)")
    if 'day_over_day_change_pp' in dropoff_df.columns and not dropoff_df.empty:
        steepest_idx = dropoff_df['day_over_day_change_pp'].idxmin()
        steepest_day = dropoff_df.loc[steepest_idx]
        fig_drop = px.line(dropoff_df, x='day_offset', y='pct_active', markers=True, title="Active Trial Users by Day")
        fig_drop.add_annotation(
            x=steepest_day['day_offset'], y=steepest_day['pct_active'],
            text=f"Steepest Drop (Day {int(steepest_day['day_offset'])})",
            showarrow=True, arrowhead=1, arrowcolor="red", ax=30, ay=-40
        )
        st.plotly_chart(fig_drop, use_container_width=True)
        st.info(f"**Key Insight**: The steepest engagement drop occurs on **Day {int(steepest_day['day_offset'])}** with a {abs(steepest_day['day_over_day_change_pp']):.1f}pp decline — this is the optimal intervention point.")
    else:
        st.warning("Drop-off curve data not available.")

elif page == "Cohort Retention":
    st.title("Cohort Retention Matrix")
    cohort_df_clean = cohort_df.copy()
    cohort_df_clean['cohort_month'] = pd.to_datetime(cohort_df_clean['cohort_month']).dt.strftime('%Y-%m')
    retention_cols = [c for c in ['d1_retention_pct', 'd7_retention_pct', 'd14_retention_pct', 'd30_retention_pct'] if c in cohort_df_clean.columns]
    if retention_cols:
        heat_data = cohort_df_clean.set_index('cohort_month')[retention_cols]
        fig_heat = px.imshow(heat_data, text_auto=".1f", aspect="auto",
                             labels=dict(x="Retention Day", y="Cohort Month", color="Retention %"),
                             color_continuous_scale="YlGnBu",
                             title="Cohort Retention Heatmap (%)")
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("Note: D14/D30 cells are NULL for immature cohorts that haven't reached those days yet.")
    else:
        st.warning("Retention data not available in expected format.")

elif page == "A/B Test & ML Model":
    st.title("Statistical Validation & Predictive Modeling")

    st.subheader("Day-6 Intervention A/B Test Results")
    ab = ab_df

    col1, col2, col3 = st.columns(3)
    col1.metric("Control Conversion", f"{ab['control_rate']*100:.2f}%")
    col2.metric("Treatment Conversion", f"{ab['treatment_rate']*100:.2f}%")
    col3.metric("Relative Lift", f"{ab['relative_lift_pct']:.1f}%", delta=f"{ab['absolute_lift_pp']:.2f} pp")

    pval = ab['p_value']
    pval_display = f"{pval:.4f}" if pval >= 0.0001 else f"{pval:.2e}"
    st.info(f"**Statistical Significance:** P-Value = {pval_display}. The result is **{'statistically significant' if ab['is_significant'] else 'not significant'}**.")

    with st.expander("Data Engineering & Statistical Audit Panel", expanded=False):
        col_a1, col_a2 = st.columns(2)
        srm_ok = not bool(ab.get('has_srm', True))
        col_a1.metric("SRM Check", "PASS" if srm_ok else "FAIL", delta=f"p={ab.get('srm_p_value', 0):.4f}")
        col_a2.metric("Adequately Powered (Pre-Exp)", "YES" if ab.get('is_adequately_powered', False) else "NO", delta=f"Req: {ab.get('required_n_per_arm', 0):.0f}/arm")
        obs_power = ab.get('observed_power', None)
        col_b1, col_b2 = st.columns(2)
        col_b1.metric("Observed Power", f"{obs_power:.2%}" if obs_power else "N/A")
        col_b2.metric("Observed Control Rate", f"{ab.get('control_rate', 0)*100:.1f}%")

        st.markdown("""
        **Methodological Rigor**:
        - **Pre-experiment power analysis**: MDE of 8% relative lift on config baseline (12%), alpha=0.05, power=0.80
        - **Observed power**: Uses actual control rate as a robustness check
        - **Bonferroni correction**: Two tests (A/B z-test + chi-square) → adjusted alpha = 0.025
        - **SRM test**: Chi-square goodness-of-fit confirms proper randomization
        - **Bot filtering**: Behavioral heuristics validated against ground truth
        - **Data leakage prevention**: ML features use only `day_offset <= 3` events
        """)

    st.markdown("---")
    st.subheader("Propensity-to-Convert Machine Learning Model")
    st.markdown("Random Forest trained on early behavioral features (Days 1-3) to predict purchase likelihood among trial users.")

    if 'Importance' in ml_df.columns and 'Feature' in ml_df.columns:
        fig_ml = px.bar(ml_df.head(10), x='Importance', y='Feature', orientation='h',
                        title="Feature Importance (Random Forest)",
                        color='Importance', color_continuous_scale='RdBu')
        fig_ml.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_ml, use_container_width=True)
    else:
        st.warning(f"ML model output missing required columns. Available: {list(ml_df.columns)}")

elif page == "Behavioral & Advanced Analytics":
    st.title("Behavioral & Advanced Analytics")

    if chi2_df is not None:
        st.subheader("Chi-Square: Collaboration Feature vs. Conversion")
        chi2_pval = chi2_df['p_value']
        if chi2_pval >= 0.001:
            chi2_display = f"{chi2_pval:.4f}"
        elif chi2_pval > 1e-100:
            chi2_display = f"{chi2_pval:.2e}"
        else:
            chi2_display = "< 1e-100"
        col_c1, col_c2 = st.columns(2)
        col_c1.metric("Chi-Square Statistic", f"{chi2_df['chi2_stat']:.1f}")
        col_c2.metric("P-Value (Bonferroni α=0.025)", chi2_display,
                      delta="Significant" if chi2_df['is_significant'] else "Not Significant")
    else:
        st.info("Chi-square results not available. Run the full pipeline.")

    st.markdown("---")
    st.subheader("Session & Lifetime Distribution")
    if adv_df is not None and not adv_df.empty:
        if 'metric' in adv_df.columns and 'value' in adv_df.columns:
            adv = adv_df.set_index('metric')['value']
            col_a1, col_a2, col_a3 = st.columns(3)
            col_a1.metric("Avg Lifetime (Days)", f"{float(adv.get('avg_lifetime_days', 0)):.1f}")
            col_a2.metric("Median Lifetime (Days)", f"{int(float(adv.get('median_lifetime_days', 0)))}")
            col_a3.metric("Max Lifetime (Days)", f"{int(float(adv.get('max_lifetime_days', 0)))}")
            col_b1, col_b2 = st.columns(2)
            col_b1.metric("Top 10% Avg Sessions", f"{float(adv.get('top_10_pct_avg_sessions', 0)):.1f}")
            col_b2.metric("Median User Sessions", f"{float(adv.get('median_user_sessions', 0)):.1f}")
        else:
            st.dataframe(adv_df)
    else:
        st.info("Advanced analytics data not available.")

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("Google Data Analytics Portfolio Project")
st.sidebar.markdown("[View on GitHub](https://github.com/sourav1243/playstore-freemium-churn-funnel)")
