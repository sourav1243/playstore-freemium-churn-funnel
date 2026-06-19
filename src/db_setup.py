import os
import duckdb
import pandas as pd
from typing import Set
from src.utils import PROJECT_ROOT, SQL_DIR, PROCESSED_DIR, SYNTHETIC_DIR, setup_logging

log = setup_logging(__name__)

def run_sql() -> None:
    required_files = [
        os.path.join(SYNTHETIC_DIR, 'users.csv'),
        os.path.join(SYNTHETIC_DIR, 'events.csv'),
        os.path.join(PROCESSED_DIR, 'apps_clean.csv'),
    ]
    for f in required_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Required file not found: {f}. Run generate_synthetic_events.py first.")

    with duckdb.connect(os.path.join(PROJECT_ROOT, 'warehouse.duckdb')) as conn:
        log.info("Running 01_schema.sql...")
        with open(os.path.join(SQL_DIR, '01_schema.sql'), 'r') as f:
            conn.execute(f.read())

        log.info("Running 02_clean_bot_filter.sql...")
        with open(os.path.join(SQL_DIR, '02_clean_bot_filter.sql'), 'r') as f:
            conn.execute(f.read())

        df_users: pd.DataFrame = pd.read_csv(os.path.join(SYNTHETIC_DIR, 'users.csv'))
        df_clean: pd.DataFrame = conn.execute("SELECT user_id FROM clean_users").fetchdf()

        ground_truth_bots: Set[int] = set(df_users[df_users['is_bot_ground_truth'] == True]['user_id'])
        clean_ids: Set[int] = set(df_clean['user_id'])
        flagged_bots: Set[int] = set(df_users['user_id']) - clean_ids

        true_positives: int = len(ground_truth_bots.intersection(flagged_bots))
        false_positives: int = len(flagged_bots - ground_truth_bots)
        false_negatives: int = len(ground_truth_bots - flagged_bots)

        precision: float = true_positives / len(flagged_bots) if flagged_bots else 0.0
        recall: float = true_positives / len(ground_truth_bots) if ground_truth_bots else 0.0
        log.info(f"Bot Filter - Precision: {precision:.2f}, Recall: {recall:.2f}")
        log.info(f"  True Positives: {true_positives}, False Positives: {false_positives}, False Negatives: {false_negatives}")
        log.info(f"  Total Flagged: {len(flagged_bots)}, Total Bots: {len(ground_truth_bots)}")

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        log.info("Running 03_funnel_cte.sql...")
        with open(os.path.join(SQL_DIR, '03_funnel_cte.sql'), 'r') as f:
            conn.execute(f.read())

        log.info("Running 04_cohort_retention_cte.sql...")
        with open(os.path.join(SQL_DIR, '04_cohort_retention_cte.sql'), 'r') as f:
            conn.execute(f.read())

        log.info("Running 05_churn_analysis.sql...")
        with open(os.path.join(SQL_DIR, '05_churn_analysis.sql'), 'r') as f:
            conn.execute(f.read())

        log.info("Running 06_segment_breakdowns.sql...")
        with open(os.path.join(SQL_DIR, '06_segment_breakdowns.sql'), 'r') as f:
            conn.execute(f.read())

        log.info("Running 07_advanced_analytics.sql...")
        with open(os.path.join(SQL_DIR, '07_advanced_analytics.sql'), 'r') as f:
            conn.execute(f.read())

    log.info("Database processing and aggregations complete.")

if __name__ == "__main__":
    run_sql()
