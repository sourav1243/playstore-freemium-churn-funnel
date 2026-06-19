<div align="center">
  <h1>Google Play Store Freemium App<br>Churn & Funnel Analysis</h1>
  <p><em>End-to-end product analytics pipeline — from synthetic data generation to ML-powered insights</em></p>
  <p>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python" alt="Python"></a>
    <a href="https://github.com/sourav1243/playstore-freemium-churn-funnel/actions"><img src="https://img.shields.io/github/actions/workflow/status/sourav1243/playstore-freemium-churn-funnel/ci.yml?logo=github" alt="CI"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Black"></a>
    <a href="https://duckdb.org"><img src="https://img.shields.io/badge/DuckDB-FFF000?logo=duckdb&logoColor=000" alt="DuckDB"></a>
    <a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit" alt="Streamlit"></a>
    <a href="https://scikit-learn.org"><img src="https://img.shields.io/badge/scikit--learn-F7931E?logo=scikit-learn&logoColor=fff" alt="scikit-learn"></a>
  </p>
  <p>
    <a href="#key-findings">Key Findings</a> •
    <a href="#visualizations">Visualizations</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#pipeline-stages">Pipeline</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#design-decisions">Design</a> •
    <a href="#deployment">Deploy</a>
  </p>
</div>

---

An end-to-end product analytics pipeline that traces **120,000 synthetic user journeys** through a freemium mobile-app conversion funnel. Built with **Python**, **SQL (DuckDB)**, **scikit-learn**, and **statistical hypothesis testing**, demonstrating the full analytical workflow: synthetic data generation, behavioral bot filtering, SQL funnel/cohort/churn analysis, A/B testing with pre-experiment power analysis, ML propensity modeling, and interactive dashboards.

---

## Key Findings

| Metric | Value |
|--------|-------|
| **Funnel conversion** | 115K installs → 84.9% signup → 87.9% first session → 85.0% feature use → 65.0% trial → **46.0% trial-to-paid** |
| **Day-6 engagement cliff** | Trial user activity drops **27.4pp** on Day 6 — 24 hours before trial expiration |
| **A/B test validated** | Day-6 push notification: **+7.8% relative lift** (p=3.3e-14, power=100%) |
| **Top conversion driver** | Early collaboration feature usage is strongest predictor (RF importance: **0.97**) |
| **Bot filtering** | 100% precision / 100% recall — behavioral heuristics perfectly identify synthetic bots |

## Visualizations

<div align="center">
  <table>
    <tr>
      <td width="50%"><img src="reports/figures/funnel_bars.png" alt="Conversion Funnel" width="100%"></td>
      <td width="50%"><img src="reports/figures/retention_heatmap.png" alt="Cohort Retention Heatmap" width="100%"></td>
    </tr>
    <tr>
      <td><em>Conversion funnel — 115K installs drop to ~36K purchases across 6 stages</em></td>
      <td><em>Cohort retention heatmap showing engagement decay by monthly cohort</em></td>
    </tr>
    <tr>
      <td width="50%"><img src="reports/figures/trial_dropoff_curve.png" alt="Trial Drop-off Curve" width="100%"></td>
      <td width="50%"><img src="reports/figures/feature_adoption_conversion.png" alt="Feature Adoption vs Conversion" width="100%"></td>
    </tr>
    <tr>
      <td><em>Trial drop-off curve — Day 6 shows the steepest decline (27.4pp)</em></td>
      <td><em>Feature adoption rates segmented by converted vs. non-converted users</em></td>
    </tr>
  </table>
</div>

---

## Quick Start

```bash
# Clone and enter
git clone https://github.com/sourav1243/playstore-freemium-churn-funnel.git
cd playstore-freemium-churn-funnel

# Create virtual environment (Python 3.10+)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install & run
pip install -r requirements.txt
python src/run_pipeline.py     # ~2-3 min: generates data, SQL, stats, ML, reports
streamlit run src/app.py       # Launch interactive dashboard
```

### Docker (One Command)
```bash
docker compose up    # Runs pipeline + launches dashboard at http://localhost:8501
```

---

## Pipeline Stages

```
Data Acquisition ──> Synthetic Events ──> SQL Warehouse ──> A/B Testing ──> ML Model ──> Dashboard
    (Kaggle /          (120K users,          (DuckDB:           (Power        (Random        (Streamlit +
     seed data)          945K events)         funnel,            analysis,     Forest,         Plotly,
                                               cohort,           z-test,       5-fold CV)      HTML,
                                               churn,            chi-square)                   PowerBI)
                                               segments)
```

| Stage | Description |
|-------|-------------|
| **1. Data Acquisition** | Kaggle Google Play Store dataset or built-in seed data (20 productivity apps, Rating >= 4.0) |
| **2. Synthetic Events** | 120,000 user journeys with 4-stage funnel probabilities, A/B groups, and 4.1% bot injection |
| **3. SQL Warehouse** | DuckDB schema, bot filtering, funnel CTEs, cohort retention, churn analysis, segmentation |
| **4. A/B Testing** | Pre-experiment power analysis (MDE=8%, alpha=0.05, power=0.80), SRM check, two-proportion z-test, chi-square |
| **5. ML Model** | Random Forest on Days 1-3 features (no data leakage), 5-fold CV (ROC-AUC: 0.68) |
| **6. Reports** | Retention heatmap, funnel chart, sankey diagram, trial drop-off, interactive HTML dashboard, PowerBI export |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Generation | Python, pandas, numpy, Faker |
| Analytics Warehouse | DuckDB (embedded OLAP) |
| Statistics | scipy, statsmodels |
| Machine Learning | scikit-learn (Random Forest) |
| Visualization | matplotlib, seaborn, plotly |
| Interactive Dashboard | Streamlit + Plotly |
| Static Dashboard | Plotly HTML |
| BI Layer | Power BI (via CSV exports + DAX measures) |
| Deployment | Docker, Streamlit Cloud |

---

## Repository Structure

```
playstore-freemium-churn-funnel/
├── config/             # YAML simulation parameters
├── data/               # Raw, synthetic, and processed outputs
├── sql/                # 7 SQL scripts for analysis
├── src/                # 11 Python modules (pipeline + utils)
├── tests/              # 26 pytest tests (7 integration + 19 unit)
├── dashboard/          # PowerBI exports & build guide
├── reports/            # Figures, dashboards, recommendations
├── .github/workflows/  # CI/CD pipeline (lint → test → docker)
├── Dockerfile          # Production container
└── docker-compose.yml  # One-command orchestration
```

---

## Testing

```bash
pytest tests/ -v                    # 26 tests (all pass)
pytest tests/ -v --cov=src --cov-report=term-missing   # With coverage
```

- **Integration tests (7)**: table existence, bot filtering, funnel monotonicity, null checks, SRM absence, ML outputs, data leakage
- **Unit tests (19)**: config validation (5), funnel integrity (3), A/B plausibility (2), feature importance (2), cohort retention (2), segmentation (1), dropoff curve (2), config keys & ranges (2)

---

## Design Decisions

- **Pre-experiment power analysis**: Uses assumed baseline of 12% and MDE of 8% relative lift (from config), NOT observed effect size
- **One-tailed A/B test**: `alternative='larger'` because intervention logically can only increase conversion or have no effect
- **Bot filter validation**: Ground-truth labels (injected bots) enable precise precision/recall calculation
- **Data leakage prevention**: ML features use only `day_offset <= 3` events — no future information leaks into training
- **Cohort maturity masking**: Immature cohorts return NULL rather than unreliable partial data
- **Bonferroni correction**: Two tests (A/B + chi-square) use adjusted alpha = 0.025
- **Data ethics**: All data is synthetically generated — no real user information

---

## Deployment

| Platform | Instructions |
|----------|-------------|
| **Streamlit Cloud** (free) | Go to [share.streamlit.io](https://share.streamlit.io), select repo, entry point: `src/app.py` |
| **Docker** (any cloud) | `docker compose up` — runs on port 8501 |
| **Hugging Face Spaces** | Create Space → Docker → point to this repo |

---

## Limitations & Future Work

- **Synthetic data realism**: Conversion rates (~46%) exceed real-world freemium benchmarks (2-5%)
- **ML single-feature dominance**: `used_collab_early` dominates due to 3.5x multiplier in generator
- **Segmentation ordering**: `Converted` evaluated before `Churned` — paying users appear converted regardless of inactivity
- **Pipeline parallelism**: All SQL steps run sequentially — DAG orchestrator would improve scalability

---

<div align="center">
  <p><strong>Freemium App Analytics Pipeline</strong></p>
  <p>
    <a href="https://github.com/sourav1243/playstore-freemium-churn-funnel">View on GitHub</a> •
    <a href="https://share.streamlit.io">Live Demo</a> •
    <a href="reports/executive_presentation.md">Executive Summary</a>
  </p>
</div>
