import os
import pandas as pd
import subprocess
from src.utils import PROJECT_ROOT, PROCESSED_DIR, setup_logging

log = setup_logging(__name__)

RAW_DIR: str = os.path.join(PROJECT_ROOT, "data", "raw")
SEED_DIR: str = os.path.join(PROJECT_ROOT, "data", "seed")

def fetch_data() -> None:
    for d in [RAW_DIR, SEED_DIR, PROCESSED_DIR]:
        os.makedirs(d, exist_ok=True)

    kaggle_success: bool = False
    try:
        log.info("Attempting to download from Kaggle...")
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d", "lava18/google-play-store-apps", "-p", RAW_DIR, "--unzip"],
            capture_output=True, text=True, timeout=60
        )
        kaggle_success = result.returncode == 0
        if kaggle_success:
            log.info("Downloaded successfully from Kaggle.")
        else:
            log.warning(f"Kaggle download failed: {result.stderr}")
    except FileNotFoundError:
        log.warning("Kaggle CLI not installed. Install with: pip install kaggle")
    except Exception as e:
        log.warning(f"Kaggle download failed: {e}")

    kaggle_csv: str = os.path.join(RAW_DIR, "googleplaystore.csv")
    output_csv: str = os.path.join(PROCESSED_DIR, "apps_clean.csv")

    if kaggle_success and os.path.exists(kaggle_csv):
        log.info("Processing Kaggle dataset...")
        df = pd.read_csv(kaggle_csv)

        df['Installs'] = df['Installs'].astype(str).str.replace('+', '', regex=False).str.replace(',', '', regex=False)
        df = df[df['Installs'] != 'Free']
        df['Installs'] = pd.to_numeric(df['Installs'], errors='coerce')

        df['Price'] = df['Price'].astype(str).str.replace('$', '', regex=False)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')

        df = df.dropna(subset=['Rating', 'Installs'])
        df = df[(df['Category'] == 'PRODUCTIVITY') & (df['Rating'] >= 4.0)].copy()

        df = df.drop_duplicates(subset=['App'])
        log.info(f"After deduplication: {len(df)} unique apps")

        df['app_id'] = range(1, len(df) + 1)
        df = df.rename(columns={'App': 'app_name', 'Category': 'category'})
        df = df[['app_id', 'app_name', 'category', 'Rating', 'Installs', 'Price']]

        df.to_csv(output_csv, index=False)
        log.info(f"Kaggle data processed. {len(df)} rows saved to {output_csv}")
    else:
        log.info("Falling back to seed data...")
        seed_data: dict = {
            'app_name': [
                'Todoist', 'Notion', 'Evernote', 'Microsoft To Do', 'Google Keep',
                'TickTick', 'Any.do', 'Asana', 'Trello', 'Slack', 'ClickUp',
                'Monday.com', 'Forest - Stay Focused', 'Habitica', 'Google Tasks',
                'Microsoft OneNote', 'Toggl Track', 'Focus To-Do', 'Workflowy', 'Remember The Milk'
            ],
            'category': ['PRODUCTIVITY'] * 20,
            'Rating': [4.5, 4.8, 4.2, 4.6, 4.4, 4.7, 4.3, 4.5, 4.4, 4.3, 4.6, 4.5, 4.8, 4.7, 4.6, 4.5, 4.6, 4.7, 4.5, 4.4],
            'Installs': [10000000, 5000000, 100000000, 10000000, 1000000000, 5000000, 10000000, 50000000, 50000000, 50000000, 1000000, 5000000, 10000000, 1000000, 50000000, 500000000, 1000000, 5000000, 100000, 1000000],
            'Price': [0.0] * 20
        }
        df = pd.DataFrame(seed_data)
        df['app_id'] = range(1, len(df) + 1)
        df = df[['app_id', 'app_name', 'category', 'Rating', 'Installs', 'Price']]
        seed_csv: str = os.path.join(SEED_DIR, "productivity_apps_fallback.csv")
        df.to_csv(seed_csv, index=False)
        df.to_csv(output_csv, index=False)
        log.info(f"Seed data created and processed. {len(df)} rows saved.")

if __name__ == "__main__":
    fetch_data()
