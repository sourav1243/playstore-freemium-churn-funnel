import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from src.utils import PROJECT_ROOT, PROCESSED_DIR, FIGURES_DIR, setup_logging

log = setup_logging(__name__)

def generate_visualizations() -> None:
    os.makedirs(FIGURES_DIR, exist_ok=True)

    retention_path = os.path.join(PROCESSED_DIR, 'cohort_retention.csv')
    funnel_path = os.path.join(PROCESSED_DIR, 'funnel_summary.csv')
    dropoff_path = os.path.join(PROCESSED_DIR, 'trial_dropoff_curve.csv')
    beh_path = os.path.join(PROCESSED_DIR, 'behavioral_stats.csv')

    for p in [retention_path, funnel_path, dropoff_path, beh_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required file not found: {p}")

    retention_df = pd.read_csv(retention_path)
    retention_df['cohort_month'] = pd.to_datetime(retention_df['cohort_month']).dt.strftime('%Y-%m')
    heatmap_data = retention_df.set_index('cohort_month')[['d1_retention_pct', 'd7_retention_pct', 'd14_retention_pct', 'd30_retention_pct']]

    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="YlGnBu", mask=heatmap_data.isnull())
    plt.title('Cohort Retention Heatmap (%)')
    plt.ylabel('Cohort Month')
    plt.xlabel('Retention Day')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'retention_heatmap.png'))
    plt.close()

    funnel_df = pd.read_csv(funnel_path).iloc[0]
    stages = ['Install', 'Signup', 'First Session', 'Feature Used', 'Trial', 'Purchase']
    counts = [funnel_df['n_install'], funnel_df['n_signup'], funnel_df['n_first_session'], funnel_df['n_feature'], funnel_df['n_trial'], funnel_df['n_purchase']]
    pcts = [100, funnel_df['pct_install_to_signup'], funnel_df['pct_signup_to_session'], funnel_df['pct_session_to_feature'], funnel_df['pct_feature_to_trial'], funnel_df['pct_trial_to_purchase']]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(stages, counts, color='#3498db')
    ax.set_title('Conversion Funnel')
    ax.set_ylabel('Number of Users')
    max_count = max(counts)
    for bar, pct, cnt in zip(bars, pcts, counts):
        yval = bar.get_height()
        offset = max_count * 0.02
        label = f"{cnt:,.0f}" if pct == 100 else f"{pct}%\n({cnt:,.0f})"
        ax.text(bar.get_x() + bar.get_width()/2, yval + offset, label, ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'funnel_bars.png'))
    plt.close()

    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = ["Install", "Signup", "First Session", "Feature Used", "Trial", "Purchase", "Drop-Off"],
          color = "blue"
        ),
        link = dict(
          source = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4],
          target = [1, 6, 2, 6, 3, 6, 4, 6, 5, 6],
          value = [
              counts[1], counts[0]-counts[1],
              counts[2], counts[1]-counts[2],
              counts[3], counts[2]-counts[3],
              counts[4], counts[3]-counts[4],
              counts[5], counts[4]-counts[5]
          ]
      ))])
    fig.update_layout(title_text="Funnel Sankey Diagram", font_size=10)
    fig.write_html(os.path.join(FIGURES_DIR, 'funnel_sankey.html'))

    dropoff_df = pd.read_csv(dropoff_path)
    plt.figure(figsize=(10, 6))
    plt.plot(dropoff_df['day_offset'], dropoff_df['pct_active'], marker='o', linestyle='-', color='r', label='% Active')

    steepest_idx = dropoff_df['day_over_day_change_pp'].idxmin()
    steepest_day = dropoff_df.loc[steepest_idx]
    plt.annotate('Steepest Drop (Cliff)', xy=(steepest_day['day_offset'], steepest_day['pct_active']),
                 xytext=(steepest_day['day_offset']+1, steepest_day['pct_active']+10),
                 arrowprops=dict(facecolor='red', shrink=0.05))

    plt.title('Trial User Active % by Day Offset')
    plt.xlabel('Days Since Trial Start')
    plt.ylabel('% of Trial Users Active')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'trial_dropoff_curve.png'))
    plt.close()

    beh_df = pd.read_csv(beh_path)
    beh_df = beh_df.sort_values('used_collab')
    beh_labels = ['No Collab Feature' if r['used_collab'] == 0 else 'Used Collab Feature' for _, r in beh_df.iterrows()]
    plt.figure(figsize=(8, 6))
    bars = plt.bar(beh_labels, beh_df['conversion_rate'], color=['#95a5a6', '#2ecc71'])
    plt.title('Trial-to-Paid Conversion Rate by Feature Adoption')
    plt.ylabel('Conversion Rate (%)')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval}%", ha='center', va='bottom', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, 'feature_adoption_conversion.png'))
    plt.close()

    log.info("Visualizations generated in reports/figures/")

if __name__ == "__main__":
    generate_visualizations()
