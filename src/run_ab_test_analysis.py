import os
import yaml
import pandas as pd
import numpy as np
import duckdb
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from src.utils import PROJECT_ROOT, PROCESSED_DIR, setup_logging

log = setup_logging(__name__)

def run_analysis() -> None:
    db_path: str = os.path.join(PROJECT_ROOT, 'warehouse.duckdb')
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"warehouse.duckdb not found at {db_path}. Run db_setup.py first.")
    with duckdb.connect(db_path) as conn:
        query: str = """
            SELECT
                u.ab_group,
                COUNT(u.user_id) as n_users,
                SUM(CASE WHEN e.event_name = 'purchase_completed' THEN 1 ELSE 0 END) as n_purchases
            FROM clean_users u
            LEFT JOIN clean_events e ON u.user_id = e.user_id AND e.event_name = 'purchase_completed'
            WHERE u.ab_group IS NOT NULL
            GROUP BY u.ab_group
        """
        df_ab: pd.DataFrame = conn.execute(query).fetchdf()

    control = df_ab[df_ab['ab_group'] == 'control'].iloc[0]
    treatment = df_ab[df_ab['ab_group'] == 'treatment'].iloc[0]

    n_c: int = int(control['n_users'])
    p_c: int = int(control['n_purchases'])
    n_t: int = int(treatment['n_users'])
    p_t: int = int(treatment['n_purchases'])

    rate_c: float = p_c / n_c
    rate_t: float = p_t / n_t

    expected_freq: list = [(n_c + n_t) / 2, (n_c + n_t) / 2]
    observed_freq: list = [n_c, n_t]
    srm_chi2, srm_p = stats.chisquare(f_obs=observed_freq, f_exp=expected_freq)
    has_srm: bool = srm_p < 0.001

    config_path: str = os.path.join(PROJECT_ROOT, "config", "simulation_config.yaml")
    with open(config_path, "r") as f:
        config: dict = yaml.safe_load(f)
    assumed_baseline: float = config['probabilities']['control_purchase_mean']
    t_multiplier: float = config['probabilities']['treatment_multiplier']
    expected_relative_lift: float = t_multiplier - 1.0
    mde_absolute: float = assumed_baseline * expected_relative_lift
    effect_size: float = sm.stats.proportion_effectsize(assumed_baseline + mde_absolute, assumed_baseline)
    power_analysis = NormalIndPower()
    req_n: float = power_analysis.solve_power(effect_size=effect_size, alpha=0.05, power=0.8, ratio=1, alternative='larger')
    is_adequately_powered: bool = n_c >= req_n and n_t >= req_n

    obs_effect_size: float = sm.stats.proportion_effectsize(rate_c * t_multiplier, rate_c) if rate_c > 0 else 0.0
    obs_power: float = power_analysis.solve_power(effect_size=obs_effect_size, nobs1=n_c, alpha=0.05, ratio=1, alternative='larger') if rate_c > 0 else 0.0

    counts: np.ndarray = np.array([p_t, p_c])
    nobs: np.ndarray = np.array([n_t, n_c])
    stat, pval = proportions_ztest(counts, nobs, alternative='larger')

    ci_t = proportion_confint(p_t, n_t, alpha=0.05, method='normal')
    ci_c = proportion_confint(p_c, n_c, alpha=0.05, method='normal')

    abs_lift: float = rate_t - rate_c
    rel_lift: float = abs_lift / rate_c if rate_c > 0 else 0.0

    ab_results: pd.DataFrame = pd.DataFrame([{
        'metric': 'A/B Test - Day 6 Trial Extension',
        'control_n': n_c,
        'treatment_n': n_t,
        'control_rate': rate_c,
        'treatment_rate': rate_t,
        'relative_lift_pct': rel_lift * 100,
        'absolute_lift_pp': abs_lift * 100,
        'z_stat': stat,
        'p_value': pval,
        'is_significant': bool(pval < 0.025),
        'srm_p_value': srm_p,
        'has_srm': bool(has_srm),
        'required_n_per_arm': round(req_n, 0),
        'is_adequately_powered': bool(is_adequately_powered),
        'observed_power': round(obs_power, 4),
        'ci_lower_t': ci_t[0],
        'ci_upper_t': ci_t[1],
        'ci_lower_c': ci_c[0],
        'ci_upper_c': ci_c[1]
    }])

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    ab_results.to_csv(os.path.join(PROCESSED_DIR, 'ab_test_results.csv'), index=False)

    log.info("--- A/B Test Results ---")
    for k, v in ab_results.iloc[0].items():
        log.info(f"{k}: {v}")

    behavioral_path: str = os.path.join(PROCESSED_DIR, 'behavioral_stats.csv')
    if os.path.exists(behavioral_path):
        df_beh: pd.DataFrame = pd.read_csv(behavioral_path)
        if len(df_beh) == 2:
            not_used = df_beh[df_beh['used_collab'] == 0].iloc[0]
            used = df_beh[df_beh['used_collab'] == 1].iloc[0]

            obs: np.ndarray = np.array([
                [int(used['total_purchases']), int(used['total_users'] - used['total_purchases'])],
                [int(not_used['total_purchases']), int(not_used['total_users'] - not_used['total_purchases'])]
            ])
            chi2, p_val, dof, ex = stats.chi2_contingency(obs)

            p_val_display: float = max(p_val, 1e-300)
            bonferroni_alpha: float = 0.05 / 2  # two tests: A/B z-test + chi-square
            beh_results: pd.DataFrame = pd.DataFrame([{
                'test': 'Chi-Square: Collaboration Feature vs Conversion',
                'chi2_stat': chi2,
                'p_value': p_val_display,
                'is_significant': bool(p_val < bonferroni_alpha),
                'bonferroni_alpha': bonferroni_alpha
            }])
            beh_results.to_csv(os.path.join(PROCESSED_DIR, 'behavioral_chi2_results.csv'), index=False)

if __name__ == "__main__":
    run_analysis()
