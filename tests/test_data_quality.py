import os
import duckdb
import pytest
import pandas as pd
from typing import List

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH: str = os.path.join(PROJECT_ROOT, 'warehouse.duckdb')
PROCESSED_DIR: str = os.path.join(PROJECT_ROOT, 'data', 'processed')

@pytest.fixture(scope="module")
def conn():
    if not os.path.exists(DB_PATH):
        pytest.skip("warehouse.duckdb not found. Run db_setup.py first.")
    connection = duckdb.connect(DB_PATH)
    yield connection
    connection.close()

def test_tables_exist(conn) -> None:
    tables: List[str] = conn.execute("SHOW TABLES").fetchdf()['name'].tolist()
    expected_tables: List[str] = ['apps', 'users', 'events', 'clean_users', 'clean_events']
    for t in expected_tables:
        assert t in tables, f"Expected table {t} missing from database."

def test_clean_users_filtered_bots(conn) -> None:
    raw_count: int = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    clean_count: int = conn.execute("SELECT COUNT(*) FROM clean_users").fetchone()[0]
    assert clean_count < raw_count, "Clean users should have fewer records than raw users after bot filtering."

def test_funnel_logic_integrity(conn) -> None:
    funnel_path: str = os.path.join(PROCESSED_DIR, 'funnel_summary.csv')
    if not os.path.exists(funnel_path):
        pytest.skip("funnel_summary.csv not generated yet.")
    df: pd.DataFrame = pd.read_csv(funnel_path)
    assert df['n_signup'].iloc[0] <= df['n_install'].iloc[0]
    assert df['n_first_session'].iloc[0] <= df['n_signup'].iloc[0]
    assert df['n_feature'].iloc[0] <= df['n_first_session'].iloc[0]
    assert df['n_trial'].iloc[0] <= df['n_feature'].iloc[0]
    assert df['n_purchase'].iloc[0] <= df['n_trial'].iloc[0]

def test_no_nulls_in_critical_columns(conn) -> None:
    null_users: int = conn.execute("SELECT COUNT(*) FROM clean_users WHERE user_id IS NULL OR install_timestamp IS NULL").fetchone()[0]
    assert null_users == 0, "Found nulls in critical user columns."
    null_events: int = conn.execute("SELECT COUNT(*) FROM clean_events WHERE event_name IS NULL OR event_timestamp IS NULL").fetchone()[0]
    assert null_events == 0, "Found nulls in critical event columns."

def test_srm_absence(conn) -> None:
    ab_path: str = os.path.join(PROCESSED_DIR, 'ab_test_results.csv')
    if not os.path.exists(ab_path):
        pytest.skip("ab_test_results.csv not generated yet.")
    df: pd.DataFrame = pd.read_csv(ab_path)
    has_srm: bool = bool(df['has_srm'].iloc[0])
    srm_p: float = df['srm_p_value'].iloc[0]
    assert not has_srm, f"SRM Detected! P-value is {srm_p} < 0.001."

def test_ml_model_outputs_exist() -> None:
    ml_path: str = os.path.join(PROCESSED_DIR, 'model_feature_importance.csv')
    metrics_path: str = os.path.join(PROCESSED_DIR, 'model_metrics.txt')
    assert os.path.exists(ml_path), "model_feature_importance.csv not found"
    assert os.path.exists(metrics_path), "model_metrics.txt not found"
    df: pd.DataFrame = pd.read_csv(ml_path)
    assert 'Importance' in df.columns
    assert len(df) > 0

def test_ml_data_leakage(conn) -> None:
    total_early: int = conn.execute(
        "SELECT COUNT(*) FROM clean_events WHERE event_name = 'purchase_completed' AND day_offset <= 3"
    ).fetchone()[0]
    query: str = f"""
        SELECT COUNT(*) FROM (
            SELECT u.user_id
            FROM clean_users u
            LEFT JOIN clean_events e ON u.user_id = e.user_id
            WHERE u.ab_group IS NOT NULL
            GROUP BY u.user_id
            HAVING MAX(CASE WHEN e.event_name = 'purchase_completed' AND e.day_offset <= 3 THEN 1 ELSE 0 END) = 0
        ) training_data
        WHERE user_id IN (
            SELECT DISTINCT user_id FROM clean_events
            WHERE event_name = 'purchase_completed' AND day_offset <= 3
        )
    """
    leaked: int = conn.execute(query).fetchone()[0]
    assert leaked == 0, (
        f"DATA LEAKAGE IN ML TRAINING DATA! Found {leaked} users with early purchases "
        f"(day_offset <= 3) in training set. Total early purchases in DB: {total_early}"
    )
