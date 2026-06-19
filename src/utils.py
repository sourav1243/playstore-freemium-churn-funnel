import os
import sys
import logging
from typing import Optional

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR: str = os.path.join(PROJECT_ROOT, 'sql')
PROCESSED_DIR: str = os.path.join(PROJECT_ROOT, 'data', 'processed')
SYNTHETIC_DIR: str = os.path.join(PROJECT_ROOT, 'data', 'synthetic')
CONFIG_DIR: str = os.path.join(PROJECT_ROOT, 'config')
REPORTS_DIR: str = os.path.join(PROJECT_ROOT, 'reports')
FIGURES_DIR: str = os.path.join(REPORTS_DIR, 'figures')
DB_PATH: str = os.path.join(PROJECT_ROOT, 'warehouse.duckdb')

def setup_logging(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True,
    )
    return logging.getLogger(name) if name else logging.getLogger()
