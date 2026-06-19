import os
import sys
import subprocess
import shutil
from utils import PROJECT_ROOT, setup_logging

log = setup_logging(__name__)

def run_command(command, description):
    log.info("=" * 50)
    log.info(f"Running: {description}")
    log.info("=" * 50)
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=PROJECT_ROOT)
    if result.stdout.strip():
        log.info("\n" + result.stdout.strip())

def sync_exports():
    export_dir = os.path.join(PROJECT_ROOT, 'dashboard', 'exports')
    processed_dir = os.path.join(PROJECT_ROOT, 'data', 'processed')
    os.makedirs(export_dir, exist_ok=True)
    csv_count = 0
    for fname in os.listdir(processed_dir):
        if fname.endswith('.csv') or fname.endswith('.txt'):
            src = os.path.join(processed_dir, fname)
            dst = os.path.join(export_dir, fname)
            shutil.copy2(src, dst)
            csv_count += 1
    log.info(f"Synced {csv_count} files to dashboard/exports/")

def main():
    log.info("Freemium App Churn & Funnel Analysis Pipeline\n")

    steps = [
        ("python src/fetch_playstore_apps.py", "Phase 1: Fetch Play Store Apps"),
        ("python src/generate_synthetic_events.py", "Phase 2: Generate Synthetic Event Log"),
        ("python src/db_setup.py", "Phases 3-8: DuckDB SQL Warehouse Processing"),
        ("python src/run_ab_test_analysis.py", "Phase 9: Statistical A/B Validation"),
        ("python src/run_predictive_model.py", "Phase 10: Train Propensity-to-Convert ML Model"),
        ("python src/make_visualizations.py", "Phase 11: Generate Static Visualizations"),
        ("python src/generate_html_dashboard.py", "Phase 12: Generate Interactive HTML Dashboard"),
        ("python src/generate_markdowns.py", "Phase 13: Generate Business Reports"),
        ("python src/generate_powerbi_export.py", "Phase 14: Generate PowerBI Dashboard Exports"),
    ]

    for command, description in steps:
        try:
            run_command(command, description)
        except subprocess.CalledProcessError as e:
            log.error(f"Pipeline failed during {description}.")
            log.error(f"Command: {e.cmd}")
            log.error(f"Exit code: {e.returncode}")
            if e.stdout:
                log.error(f"Output:\n{e.stdout[:2000]}")
            if e.stderr:
                log.error(f"Errors:\n{e.stderr[:2000]}")
            sys.exit(1)

    sync_exports()

    log.info("=" * 50)
    log.info("Running: Automated Data Quality Tests (7 integration + 19 unit)")
    log.info("=" * 50)
    test_dir = os.path.join(PROJECT_ROOT, "tests")
    if os.path.isdir(test_dir):
        result = subprocess.run(["pytest", test_dir, "-v", "--tb=short"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        log.info(result.stdout.strip() if result.stdout.strip() else "(no output)")
        if result.returncode != 0:
            log.warning(f"Some tests FAILED (exit code {result.returncode}).")
            if result.stderr:
                log.warning(result.stderr[:1000])
        else:
            passed = result.stdout.count(" PASSED") if result.stdout else 0
            skipped = result.stdout.count(" SKIPPED") if result.stdout else 0
            log.info(f"Tests: {passed} passed, {skipped} skipped.")
    else:
        log.warning("tests/ directory not found.")

    log.info("=" * 50)
    log.info("Pipeline execution complete!")
    log.info("=" * 50)
    log.info("Generated outputs:")
    log.info("  - data/processed/*.csv        (analytics results)")
    log.info("  - reports/figures/*.png       (static visualizations)")
    log.info("  - reports/interactive_dashboard.html")
    log.info("  - reports/business_recommendation.md")
    log.info("  - reports/executive_presentation.md")
    log.info("  - dashboard/exports/*.csv     (BI-ready exports)")

if __name__ == "__main__":
    import sys
    main()
