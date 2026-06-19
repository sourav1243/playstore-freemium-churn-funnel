# Google Play Store Freemium App Churn & Funnel Analysis

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)
[![CI](https://github.com/sourav1243/playstore-freemium-churn-funnel/actions/workflows/ci.yml/badge.svg)](https://github.com/sourav1243/playstore-freemium-churn-funnel/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?logo=duckdb)](https://duckdb.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)

An end-to-end product analytics pipeline that traces user behavior through a freemium mobile-app conversion funnel. Built with **Python**, **SQL (DuckDB)**, **scikit-learn**, and **statistical hypothesis testing**, this project demonstrates the full analytical workflow: synthetic data generation, behavioral bot filtering, SQL funnel/cohort/churn analysis, A/B testing with pre-experiment power analysis, ML propensity modeling, and interactive dashboards.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Pipeline Overview                       │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  1. Data     │   2. SQL     │   3. Stats   │  4. Outputs    │
│  Generation  │   Warehouse  │   & ML       │                │
│              │              │              │                │
│ Play Store   │ DuckDB       │ A/B Z-Test  │ Interactive    │
│ Apps (Kaggle)│ CTE Funnel   │ Power Anal.  │ HTML Dashboard │
│              │ Cohort Ret.  │ Chi-Square   │ Streamlit App  │
│ Synthetic    │ Churn Anal.  │ Random       │ Static Charts  │
│ User Events  │ Segments     │ Forest       │ BI Exports     │
│ (120K users) │              │              │ Reports        │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## Key Findings

- **Funnel breakdown**: 115k installs → 84.9% signup → 87.9% first session → 85.0% feature use → 65.0% trial → **46.0% trial-to-paid conversion** (control: 44.2%, treatment: 47.7%)
- **Day-6 engagement cliff**: Trial user activity drops **27.4pp** on Day 6 — the steepest single-day decline, 24 hours before trial expiration
- **A/B test validated**: A Day-6 push notification produced a **+7.8% relative lift** in conversion (p=3.3e-14, pre-experiment power at 14,650/arm, observed power=100%)
- **Top conversion driver**: Early collaboration feature usage is the strongest predictor of purchase (Random Forest importance: 0.97)
- **Bot filtering precision/recall**: 100%/100% — behavioral heuristics (device reuse, channel patterns, email patterns) perfectly identify synthetic bots

## Methodology (STAR)

| Component | Detail |
|-----------|--------|
| **Situation** | High-rated productivity apps on Google Play generate substantial install volume but struggle to convert free users into paying subscribers |
| **Task** | Trace the conversion funnel (Install → Account → Session → Feature → Trial → Purchase), identify churn points, and validate an intervention |
| **Action** | Built Python/SQL pipeline with DuckDB warehouse, behavioral bot filtering, CTE-based funnel/cohort/churn analysis, pre-experiment power analysis, two-proportion z-test, chi-square test, and Random Forest propensity model |
| **Result** | Statistically validated Day-6 notification intervention with +7.8% lift (p=3.3e-14), projected incremental MRR of ~$1,700 per 10k trials (varies by seeded run) |

## Quick Start

### Local Setup

```bash
# Clone and enter
cd playstore-freemium-churn-funnel

# Create virtual environment (Python 3.10+ required)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (generates data, runs SQL, trains ML, creates reports)
python src/run_pipeline.py

# Launch interactive dashboard
streamlit run src/app.py
```

### Docker (One-Command Deploy)

```bash
# Build and run (runs pipeline + launches dashboard)
docker compose up

# Or build first, then run
docker compose build
docker compose up

# Open http://localhost:8501
```

### Makefile (Convenience Commands)

```bash
make install      # Create venv + install deps
make run          # Execute full pipeline
make app          # Launch Streamlit dashboard
make test         # Run tests
make docker-run   # Deploy with Docker
```

## Pipeline Stages

1. **Data Acquisition** — Kaggle Google Play Store dataset or built-in seed data (20 productivity apps, Rating ≥ 4.0)
2. **Synthetic Event Generation** — 120,000 user journeys with 4-stage funnel probabilities, A/B groups, and 4.1% bot injection
3. **SQL Warehouse (DuckDB)** — Schema creation, bot filtering (behavioral heuristics), funnel CTEs, cohort retention, churn analysis, user segmentation
4. **Statistical A/B Testing** — Pre-experiment power analysis (MDE=8%, alpha=0.05, power=0.80), SRM check, two-proportion z-test, 95% CIs, chi-square behavioral test
5. **ML Propensity Model** — Random Forest trained on Days 1-3 features (no data leakage), 5-fold CV (ROC-AUC: 0.68)
6. **Visualizations & Reports** — Retention heatmap, funnel chart, Sankey diagram, trial drop-off curve, interactive HTML dashboard, business recommendation report

## Testing

```bash
# Run full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Expected: 7 integration tests + 19 unit tests = 26 total
```

### Test Coverage
- **Integration**: Table existence, bot filtering logic, funnel monotonicity, null checks, SRM absence, ML outputs, data leakage
- **Unit**: Config validation (5), funnel integrity (3), A/B plausibility (2), feature importance (2), cohort retention (2), segmentation (1), dropoff curve (2), config keys & ranges (2)

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Generation** | Python, pandas, numpy, Faker | 120k-user synthetic behavioral dataset |
| **Analytics Warehouse** | DuckDB (embedded OLAP) | Zero-infrastructure SQL with CTE/window-function support |
| **Statistics** | scipy, statsmodels | Power analysis, z-test, chi-square, confidence intervals |
| **ML** | scikit-learn (Random Forest) | Propensity-to-convert prediction, feature importance |
| **Visualization** | matplotlib, seaborn, plotly | Static charts + interactive HTML dashboard |
| **Dashboard (Interactive)** | Streamlit + Plotly | Real-time web dashboard with funnel, cohort, A/B, and ML views |
| **Dashboard (Static)** | Plotly HTML | Self-contained interactive HTML report |
| **BI Layer** | Power BI (via CSV exports) | Executive dashboard with DAX measures |
| **Deployment** | Docker, Streamlit Cloud | One-command deploy with docker compose |

## Repository Structure

```
playstore-freemium-churn-funnel/
├── config/             # YAML simulation parameters (all tunable probabilities)
├── data/
│   ├── processed/      # SQL output: funnel, cohort, churn, segmentation CSVs
│   └── synthetic/      # Generated users.csv, events.csv
├── sql/                # 7 SQL scripts: schema → bot filter → funnel → cohort → churn → segments → advanced analytics
├── src/                # Python pipeline (11 modules including utils.py)
├── tests/              # Pytest test suite (7 integration + 19 unit tests)
├── dashboard/
│   ├── exports/        # BI-ready CSV exports
│   ├── metrics_formulas.md
│   └── dashboard_build_guide.md
├── reports/
│   ├── figures/        # Retention heatmap, funnel, drop-off curve, feature adoption
│   ├── interactive_dashboard.html
│   ├── business_recommendation.md
│   └── executive_presentation.md
├── Dockerfile          # Production-ready container
├── docker-compose.yml  # One-command orchestration
├── pyproject.toml      # Modern Python packaging
├── Makefile            # Convenience commands
└── .github/workflows/  # CI/CD pipeline
```

## Deployment Options

### Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy with: `src/app.py` as entry point
4. Set Python version to 3.11 in Advanced Settings

### Docker (Any Cloud)

```bash
docker compose up
# Runs pipeline + Streamlit dashboard on port 8501
```

### Hugging Face Spaces

Create a Space → Docker → Point to this repo. The `Dockerfile` handles everything.

## Design Decisions

- **Pre-experiment power analysis**: Uses assumed baseline rate of 12% and MDE of 8% relative lift (from config), NOT observed effect size
- **One-tailed A/B test**: `alternative='larger'` because the intervention logically can only increase or have no effect
- **Bot filter validation**: Ground-truth labels allow precision/recall calculation
- **Data leakage prevention**: ML features use only `day_offset <= 3` events
- **Cohort maturity masking**: Immature cohorts return NULL rather than unreliable partial data
- **Bonferroni correction**: Two tests use adjusted alpha = 0.025
- **Data ethics**: All data is synthetically generated — no real user information

## Limitations & Future Work

- **Synthetic data realism**: Conversion rates (~46%) are higher than real-world freemium benchmarks (2-5%)
- **ML single-feature dominance**: `used_collab_early` dominates due to 3.5x multiplier in generator
- **Segmentation ordering**: `Converted` evaluated before `Churned` — paying users appear converted regardless of inactivity
- **Correlation vs causation**: Collaboration-feature chi-square identifies association, not causation
- **Pipeline parallelism**: All SQL steps run sequentially — DAG orchestrator would improve scalability

## License

MIT

---

*Built as part of the Google Data Analytics Professional Certificate portfolio.*
