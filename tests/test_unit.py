import os
import tempfile
import yaml
import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH: str = os.path.join(PROJECT_ROOT, 'config', 'simulation_config.yaml')


def _make_temp_config(override: Dict[str, Any] = None) -> str:
    with open(CONFIG_PATH, 'r') as f:
        cfg: Dict[str, Any] = yaml.safe_load(f)
    if override:
        _deep_merge(cfg, override)
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
    yaml.dump(cfg, tmp)
    tmp.close()
    return tmp.name


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    for k, v in overrides.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


class TestConfigLoading:
    def test_config_exists(self) -> None:
        assert os.path.exists(CONFIG_PATH), "simulation_config.yaml not found"

    def test_config_valid_yaml(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        assert 'probabilities' in cfg
        assert 'trial' in cfg
        assert 'simulation' in cfg

    def test_probabilities_sum_to_plausible_range(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        probs = cfg['probabilities']
        install_to_trial = (
            probs['install_to_signup'] *
            probs['signup_to_first_session'] *
            probs['first_session_to_feature'] *
            probs['feature_to_trial']
        )
        assert 0.3 <= install_to_trial <= 0.6, f"Overall funnel conversion {install_to_trial:.3f} outside expected range"

    def test_bot_rate_in_range(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        rate: float = cfg['probabilities']['bot_flag_rate']
        assert 0.01 <= rate <= 0.10, f"Bot rate {rate} outside expected range"

    def test_all_probabilities_in_zero_one_range(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        probs = cfg['probabilities']
        exclude = {'treatment_multiplier'}  # multiplier, not a probability
        for key, val in probs.items():
            if isinstance(val, (int, float)) and key not in exclude:
                assert 0 <= val <= 1, f"Probability '{key}' = {val} outside [0, 1]"

    def test_treatment_multiplier_above_one(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        mult: float = cfg['probabilities']['treatment_multiplier']
        assert mult >= 1.0, f"Treatment multiplier {mult} < 1.0 (would decrease conversion)"

    def test_config_keys_present(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        assert 'probabilities' in cfg
        assert 'trial' in cfg
        assert 'simulation' in cfg
        assert 'ml' in cfg
        assert 'revenue' in cfg
        assert cfg['ml']['n_estimators'] >= 10
        assert cfg['ml']['max_depth'] >= 1
        assert cfg['revenue']['monthly_trial_volume'] > 0
        assert cfg['revenue']['arpu'] > 0


class TestFunnelLogic:
    def test_funnel_monotonic_decreasing(self) -> None:
        funnel_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'funnel_summary.csv')
        if not os.path.exists(funnel_path):
            pytest.skip("funnel_summary.csv not generated")
        df: pd.DataFrame = pd.read_csv(funnel_path)
        counts: list = [
            df['n_install'].iloc[0], df['n_signup'].iloc[0],
            df['n_first_session'].iloc[0], df['n_feature'].iloc[0],
            df['n_trial'].iloc[0], df['n_purchase'].iloc[0]
        ]
        for i in range(len(counts) - 1):
            assert counts[i + 1] <= counts[i], f"Funnel NOT monotonic at stage {i}: {counts[i]} -> {counts[i+1]}"

    def test_pct_calculations_consistent(self) -> None:
        funnel_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'funnel_summary.csv')
        if not os.path.exists(funnel_path):
            pytest.skip("funnel_summary.csv not generated")
        df: pd.DataFrame = pd.read_csv(funnel_path)
        row = df.iloc[0]
        computed_pct_signup = row['n_signup'] / row['n_install'] * 100
        assert abs(computed_pct_signup - row['pct_install_to_signup']) < 0.01

    def test_signup_rate_matches_config_within_margin(self) -> None:
        funnel_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'funnel_summary.csv')
        if not os.path.exists(funnel_path):
            pytest.skip("funnel_summary.csv not generated")
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        expected_signup: float = cfg['probabilities']['install_to_signup']
        df: pd.DataFrame = pd.read_csv(funnel_path)
        actual_signup: float = df['n_signup'].iloc[0] / df['n_install'].iloc[0]
        assert abs(actual_signup - expected_signup) < 0.02, (
            f"Signup rate {actual_signup:.4f} deviates from config {expected_signup} by more than 2pp"
        )


class TestABTestResults:
    def test_ab_results_exist(self) -> None:
        ab_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'ab_test_results.csv')
        if not os.path.exists(ab_path):
            pytest.skip("ab_test_results.csv not generated")
        df: pd.DataFrame = pd.read_csv(ab_path)
        assert len(df) == 1
        assert df['control_n'].iloc[0] > 0
        assert df['treatment_n'].iloc[0] > 0

    def test_conversion_rates_plausible(self) -> None:
        ab_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'ab_test_results.csv')
        if not os.path.exists(ab_path):
            pytest.skip("ab_test_results.csv not generated")
        df: pd.DataFrame = pd.read_csv(ab_path)
        row = df.iloc[0]
        assert 0.25 <= row['control_rate'] <= 0.60, f"Control rate {row['control_rate']:.3f} outside expected range (independent daily draws, collab multiplier)"
        assert 0.25 <= row['treatment_rate'] <= 0.65, f"Treatment rate {row['treatment_rate']:.3f} outside expected range"


class TestMLModel:
    def test_feature_importance_exists(self) -> None:
        ml_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'model_feature_importance.csv')
        if not os.path.exists(ml_path):
            pytest.skip("model_feature_importance.csv not generated")
        df: pd.DataFrame = pd.read_csv(ml_path)
        assert 'Feature' in df.columns
        assert 'Importance' in df.columns
        assert len(df) > 0

    def test_importance_sums_to_one(self) -> None:
        ml_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'model_feature_importance.csv')
        if not os.path.exists(ml_path):
            pytest.skip("model_feature_importance.csv not generated")
        df: pd.DataFrame = pd.read_csv(ml_path)
        total: float = df['Importance'].sum()
        assert abs(total - 1.0) < 0.01, f"Feature importances sum to {total:.4f}, expected ~1.0"


class TestCohortRetention:
    def test_retention_pcts_in_range(self) -> None:
        cohort_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'cohort_retention.csv')
        if not os.path.exists(cohort_path):
            pytest.skip("cohort_retention.csv not generated")
        df: pd.DataFrame = pd.read_csv(cohort_path)
        for col in ['d1_retention_pct', 'd7_retention_pct', 'd14_retention_pct', 'd30_retention_pct']:
            non_null = df[col].dropna()
            assert (non_null >= 0).all(), f"Negative retention in {col}"
            assert (non_null <= 100).all(), f"Retention > 100 in {col}"

    def test_d1_higher_than_d7(self) -> None:
        cohort_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'cohort_retention.csv')
        if not os.path.exists(cohort_path):
            pytest.skip("cohort_retention.csv not generated")
        df: pd.DataFrame = pd.read_csv(cohort_path)
        non_null = df.dropna(subset=['d1_retention_pct', 'd7_retention_pct'])
        assert (non_null['d1_retention_pct'] >= non_null['d7_retention_pct']).all()


class TestSegmentation:
    def test_segments_sum_to_100(self) -> None:
        seg_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'user_segmentation.csv')
        if not os.path.exists(seg_path):
            pytest.skip("user_segmentation.csv not generated")
        df: pd.DataFrame = pd.read_csv(seg_path)
        total_pct: float = df['pct_of_total'].sum()
        assert abs(total_pct - 100) < 0.1, f"Segment percentages sum to {total_pct:.2f}%"


class TestDropoffCurve:
    def test_steepest_drop_matches_config(self) -> None:
        with open(CONFIG_PATH, 'r') as f:
            cfg: Dict[str, Any] = yaml.safe_load(f)
        expected_cliff_day: int = cfg['trial']['cliff_day']
        dropoff_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'trial_dropoff_curve.csv')
        if not os.path.exists(dropoff_path):
            pytest.skip("trial_dropoff_curve.csv not generated")
        df: pd.DataFrame = pd.read_csv(dropoff_path)
        steepest_idx = df['day_over_day_change_pp'].idxmin()
        steepest_day: int = int(df.loc[steepest_idx]['day_offset'])
        assert steepest_day == expected_cliff_day, (
            f"Steepest drop is Day {steepest_day}, expected Day {expected_cliff_day} "
            f"from config (cliff_day={expected_cliff_day})"
        )

    def test_dropoff_monotonic_after_peak(self) -> None:
        dropoff_path: str = os.path.join(PROJECT_ROOT, 'data', 'processed', 'trial_dropoff_curve.csv')
        if not os.path.exists(dropoff_path):
            pytest.skip("trial_dropoff_curve.csv not generated")
        df: pd.DataFrame = pd.read_csv(dropoff_path)
        after_peak = df[df['day_offset'] >= 8]
        for i in range(len(after_peak) - 1):
            assert after_peak.iloc[i]['pct_active'] >= after_peak.iloc[i + 1]['pct_active'], \
                f"Dropoff NOT monotonic after peak at day {after_peak.iloc[i]['day_offset']}"
