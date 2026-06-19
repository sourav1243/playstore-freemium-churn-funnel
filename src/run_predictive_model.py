import os
import yaml
import pandas as pd
import duckdb
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, classification_report
from src.utils import PROJECT_ROOT, DB_PATH, PROCESSED_DIR, setup_logging

log = setup_logging(__name__)

def run_model() -> None:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"warehouse.duckdb not found at {DB_PATH}. Run db_setup.py first.")

    config_path: str = os.path.join(PROJECT_ROOT, "config", "simulation_config.yaml")
    with open(config_path, "r") as f:
        config: dict = yaml.safe_load(f)
    seed: int = config['simulation']['random_seed']
    n_est: int = config['ml']['n_estimators']
    max_d: int = config['ml']['max_depth']

    log.info("Extracting features for Propensity-to-Convert model...")
    with duckdb.connect(DB_PATH) as conn:
        query: str = """
            WITH early_activity AS (
                SELECT
                    u.user_id,
                    u.country,
                    u.acquisition_channel,
                    COUNT(CASE WHEN e.event_name = 'session_start' AND e.day_offset <= 3 THEN 1 END) as early_sessions,
                    MAX(CASE WHEN e.event_subtype = 'collaboration_feature' AND e.day_offset <= 3 THEN 1 ELSE 0 END) as used_collab_early,
                    MAX(CASE WHEN e.event_name = 'purchase_completed' THEN 1 ELSE 0 END) as target_purchased
                FROM clean_users u
                LEFT JOIN clean_events e ON u.user_id = e.user_id
                WHERE u.ab_group IS NOT NULL
                GROUP BY u.user_id, u.country, u.acquisition_channel
                HAVING MAX(CASE WHEN e.event_name = 'purchase_completed' AND e.day_offset <= 3 THEN 1 ELSE 0 END) = 0
            )
            SELECT * FROM early_activity
        """
        df: pd.DataFrame = conn.execute(query).fetchdf()
    log.info(f"Feature matrix: {df.shape[0]} rows, {df.shape[1]} columns")
    log.info(f"Target distribution: {df['target_purchased'].value_counts().to_dict()}")

    X: pd.DataFrame = df[['country', 'acquisition_channel', 'early_sessions', 'used_collab_early']]
    y: pd.Series = df['target_purchased']

    categorical_features: list = ['country', 'acquisition_channel']
    numeric_features: list = ['early_sessions', 'used_collab_early']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), categorical_features)
        ])

    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(class_weight='balanced', random_state=seed, n_estimators=n_est, max_depth=max_d))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=config['simulation']['test_size'], random_state=seed, stratify=y)
    log.info(f"Train set: {X_train.shape[0]} rows, Test set: {X_test.shape[0]} rows")

    log.info("Running 5-Fold Cross Validation on TRAINING data only...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores: np.ndarray = cross_val_score(clf, X_train, y_train, cv=cv, scoring='roc_auc')
    log.info(f"5-Fold CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    log.info("Training final model...")
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    auc: float = roc_auc_score(y_test, y_proba)
    log.info(f"Final Test Set ROC-AUC: {auc:.4f}")

    report: str = classification_report(y_test, y_pred)
    log.info("\nClassification Report:\n" + report)

    feature_names: list = numeric_features + list(clf.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(categorical_features))
    importances: np.ndarray = clf.named_steps['classifier'].feature_importances_

    importance_df: pd.DataFrame = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    importance_df.to_csv(os.path.join(PROCESSED_DIR, 'model_feature_importance.csv'), index=False)

    with open(os.path.join(PROCESSED_DIR, 'model_metrics.txt'), 'w') as f:
        f.write(f"5-Fold CV ROC-AUC: {cv_scores.mean():.4f}\n")
        f.write(f"Test Set ROC-AUC: {auc:.4f}\n")
        f.write(report)

    log.info(f"\nTop 3 Features:")
    for _, row in importance_df.head(3).iterrows():
        log.info(f"  {row['Feature']}: {row['Importance']:.4f}")

if __name__ == "__main__":
    run_model()
