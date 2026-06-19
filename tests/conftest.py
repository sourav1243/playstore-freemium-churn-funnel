import os
import pytest
import duckdb
import pandas as pd
from typing import Iterator, Any

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH: str = os.path.join(PROJECT_ROOT, 'warehouse.duckdb')
PROCESSED_DIR: str = os.path.join(PROJECT_ROOT, 'data', 'processed')


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "pipeline: marks tests that require pipeline execution")


@pytest.fixture(scope="session")
def db_conn() -> Iterator[duckdb.DuckDBPyConnection]:
    if not os.path.exists(DB_PATH):
        pytest.skip("warehouse.duckdb not found. Run pipeline first.")
    conn = duckdb.connect(DB_PATH)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def processed_dir() -> str:
    if not os.path.isdir(PROCESSED_DIR):
        pytest.skip(f"Processed directory not found: {PROCESSED_DIR}")
    return PROCESSED_DIR


@pytest.fixture
def csv_loader(processed_dir: str) -> Any:
    def _load(name: str) -> pd.DataFrame:
        path = os.path.join(processed_dir, name)
        if not os.path.exists(path):
            pytest.skip(f"File not found: {name}")
        return pd.read_csv(path)
    return _load
