.PHONY: install setup run test clean docker-build docker-run lint format

# --- Python Environment ---
VENV_NAME := .venv
VENV_BIN := $(VENV_NAME)/Scripts
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip

install: $(VENV_NAME)
	$(PIP) install -r requirements.txt

$(VENV_NAME):
	python -m venv $(VENV_NAME)

setup: install

# --- Execution ---
run:
	$(PYTHON) src/run_pipeline.py

app:
	pip install streamlit
	streamlit run src/app.py

dashboard:
	pip install streamlit
	streamlit run src/app.py

# --- Testing ---
test:
	$(PYTHON) -m pytest tests/ -v

test-cov:
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

# --- Code Quality ---
lint:
	pip install ruff
	ruff check src/ tests/

format:
	pip install black isort
	black src/ tests/
	isort src/ tests/

# --- Docker ---
docker-build:
	docker compose build

docker-run:
	docker compose up

docker-run-detached:
	docker compose up -d

# --- Cleanup ---
clean:
	rm -rf $(VENV_NAME)
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	rm -f warehouse.duckdb
	rm -f warehouse.duckdb.wal
	rm -f data/synthetic/*.csv
	rm -f data/processed/*.csv
	rm -f data/processed/*.txt
	find . -name "*.pyc" -delete

clean-data:
	rm -f data/synthetic/*.csv
	rm -f data/processed/*.csv
	rm -f data/processed/*.txt
	rm -f warehouse.duckdb
	rm -f warehouse.duckdb.wal
