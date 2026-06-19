import os
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker
from typing import Any, Dict
from src.utils import PROJECT_ROOT, setup_logging

log = setup_logging(__name__)

def load_config() -> Dict[str, Any]:
    config_path: str = os.path.join(PROJECT_ROOT, "config", "simulation_config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found at {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def generate_data() -> None:
    config: Dict[str, Any] = load_config()
    np.random.seed(config['simulation']['random_seed'])
    fake = Faker()
    Faker.seed(config['simulation']['random_seed'])

    apps_path = os.path.join(PROJECT_ROOT, "data", "processed", "apps_clean.csv")
    if not os.path.exists(apps_path):
        raise FileNotFoundError(f"apps_clean.csv not found at {apps_path}. Run fetch_playstore_apps.py first.")
    apps_df = pd.read_csv(apps_path)
    app_ids = apps_df['app_id'].values
    app_probs = apps_df['Installs'].values / apps_df['Installs'].sum()

    n_users = config['simulation']['num_installs']
    user_ids = np.arange(1, n_users + 1)

    end_date = datetime.now() - timedelta(days=40)
    start_date = end_date - timedelta(weeks=config['simulation']['weeks_history'])
    date_range = (end_date - start_date).days

    random_days = np.random.randint(0, date_range, n_users)
    install_timestamps = [start_date + timedelta(days=int(d)) for d in random_days]
    cohort_months = [d.replace(day=1).date() for d in install_timestamps]

    countries = ['US', 'IN', 'UK', 'BR', 'DE', 'CA', 'AU', 'OTHER']
    country_assignments = np.random.choice(countries, n_users, p=[0.4, 0.2, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05])

    channels = ['organic_search', 'paid_social', 'paid_search', 'referral', 'app_store_featured', 'internal_qa']
    channel_assignments = np.random.choice(channels, n_users, p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.05])

    is_bot = np.random.rand(n_users) < config['probabilities']['bot_flag_rate']

    bot_emails_pool = [f"test_bot_{i}@example.com" for i in range(5000)] + [f"qa_automation_{i}@test.com" for i in range(5000)]

    bot_device_pool = [fake.uuid4() for _ in range(12)]

    emails = []
    device_ids = []
    for i in range(n_users):
        if is_bot[i]:
            emails.append(np.random.choice(bot_emails_pool))
            if np.random.rand() < 0.9:
                device_ids.append(np.random.choice(bot_device_pool))
            else:
                device_ids.append(fake.uuid4())
            if np.random.rand() < 0.5:
                channel_assignments[i] = 'internal_qa'
        else:
            emails.append(fake.email())
            device_ids.append(fake.uuid4())

    users_app_ids = np.random.choice(app_ids, n_users, p=app_probs)

    p_signup = config['probabilities']['install_to_signup']
    p_first_session = config['probabilities']['signup_to_first_session']
    p_feature = config['probabilities']['first_session_to_feature']
    p_trial = config['probabilities']['feature_to_trial']

    rand_signup = np.random.rand(n_users)
    rand_first_session = np.random.rand(n_users)
    rand_feature = np.random.rand(n_users)
    rand_trial = np.random.rand(n_users)

    reached_signup = (rand_signup < p_signup)
    reached_first_session = reached_signup & (rand_first_session < p_first_session)
    reached_feature = reached_first_session & (rand_feature < p_feature)
    reached_trial = reached_feature & (rand_trial < p_trial)

    trial_indices = np.where(reached_trial)[0]
    ab_groups = np.array(['control', 'treatment'])[np.random.randint(0, 2, len(trial_indices))]

    ab_assignment = np.full(n_users, None, dtype=object)
    ab_assignment[trial_indices] = ab_groups

    events_data = []
    event_id_counter = 1

    cliff_day = config['trial']['cliff_day']
    cliff_mult = config['trial']['cliff_multiplier']
    max_day = config['trial']['max_trial_day']
    t_lift = config['probabilities']['treatment_multiplier']
    c_mean = config['probabilities']['control_purchase_mean']

    log.info("Generating events...")
    rand_f_sub = np.random.rand(n_users)

    for i in range(n_users):
        u_id = user_ids[i]
        a_id = users_app_ids[i]
        t_base = install_timestamps[i]
        is_b = is_bot[i]

        events_data.append((event_id_counter, u_id, a_id, 'install', None, t_base, 0))
        event_id_counter += 1

        if reached_signup[i]:
            events_data.append((event_id_counter, u_id, a_id, 'account_created', None, t_base, 0))
            event_id_counter += 1

        if reached_first_session[i]:
            events_data.append((event_id_counter, u_id, a_id, 'first_session', None, t_base, 0))
            event_id_counter += 1

        if reached_feature[i]:
            f_sub = 'collaboration_feature' if rand_f_sub[i] < 0.3 else 'standard_feature'
            t_off = np.random.randint(0, 2)
            ts = t_base + timedelta(days=t_off, minutes=np.random.randint(1, 60))
            events_data.append((event_id_counter, u_id, a_id, 'feature_used', f_sub, ts, t_off))
            event_id_counter += 1

        if reached_trial[i]:
            t_start_offset = np.random.randint(0, 2)
            ts = t_base + timedelta(days=int(t_start_offset), minutes=np.random.randint(1, 60))
            events_data.append((event_id_counter, u_id, a_id, 'trial_started', None, ts, t_start_offset))
            event_id_counter += 1

            grp = ab_assignment[i]
            purchased = False
            has_collab = (reached_feature[i] and rand_f_sub[i] < 0.3)

            active_prob = 0.9
            rand_daily_active = np.random.rand(max_day + 1)
            rand_daily_feature = np.random.rand(max_day + 1)

            for d in range(1, max_day + 1):
                day_offset = t_start_offset + d
                current_prob = active_prob

                if d == cliff_day:
                    current_prob *= cliff_mult

                if rand_daily_active[d] < current_prob:
                    ts = t_base + timedelta(days=int(day_offset), minutes=np.random.randint(1, 60))
                    events_data.append((event_id_counter, u_id, a_id, 'session_start', None, ts, day_offset))
                    event_id_counter += 1
                    if rand_daily_feature[d] < 0.5:
                        ts2 = t_base + timedelta(days=int(day_offset), minutes=np.random.randint(1, 60))
                        events_data.append((event_id_counter, u_id, a_id, 'feature_used', 'standard_feature', ts2, day_offset))
                        event_id_counter += 1

                active_prob *= 0.85

                if d == cliff_day and grp == 'treatment' and not purchased:
                    ts = t_base + timedelta(days=int(day_offset), minutes=np.random.randint(1, 60))
                    events_data.append((event_id_counter, u_id, a_id, 'trial_reminder_shown', 'day6_trial_extension', ts, day_offset))
                    event_id_counter += 1

                if not purchased:
                    purchase_prob = c_mean
                    if d < 7:
                        purchase_prob *= 0.15
                    elif d == 7:
                        purchase_prob *= 1.0
                    else:
                        purchase_prob *= 0.05
                    if has_collab:
                        purchase_prob *= 3.5
                    if grp == 'treatment':
                        purchase_prob *= t_lift

                    ts = t_base + timedelta(days=int(day_offset), minutes=np.random.randint(1, 60))
                    if np.random.rand() < purchase_prob:
                        events_data.append((event_id_counter, u_id, a_id, 'purchase_completed', None, ts, day_offset))
                        purchased = True
                        event_id_counter += 1
                    elif d == 7:
                        events_data.append((event_id_counter, u_id, a_id, 'trial_expired_no_purchase', None, ts, day_offset))
                        event_id_counter += 1

    events = pd.DataFrame(events_data, columns=['event_id', 'user_id', 'app_id', 'event_name', 'event_subtype', 'event_timestamp', 'day_offset'])

    users = pd.DataFrame({
        'user_id': user_ids,
        'app_id': users_app_ids,
        'install_timestamp': install_timestamps,
        'cohort_month': cohort_months,
        'device_id': device_ids,
        'country': country_assignments,
        'acquisition_channel': channel_assignments,
        'email': emails,
        'ab_group': ab_assignment,
        'is_bot_ground_truth': is_bot
    })

    synthetic_dir = os.path.join(PROJECT_ROOT, "data", "synthetic")
    os.makedirs(synthetic_dir, exist_ok=True)
    users.to_csv(os.path.join(synthetic_dir, "users.csv"), index=False)
    events.to_csv(os.path.join(synthetic_dir, "events.csv"), index=False)

    log.info(f"Generated {len(users)} users and {len(events)} events.")
    log.info(f"Bots: {users['is_bot_ground_truth'].sum()} ({users['is_bot_ground_truth'].mean()*100:.1f}%)")
    log.info(f"Trial starters: {reached_trial.sum()}")
    log.info(f"Treatment: {(users['ab_group'] == 'treatment').sum()} | Control: {(users['ab_group'] == 'control').sum()}")

if __name__ == "__main__":
    generate_data()
