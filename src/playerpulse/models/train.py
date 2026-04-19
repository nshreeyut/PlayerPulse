"""Model training pipeline with MLflow tracking.

Usage: python -m playerpulse.models.train
"""

from __future__ import annotations

import logging

import joblib
import mlflow
import numpy as np
import polars as pl
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from playerpulse.models.synthetic import generate_synthetic_data
from playerpulse.utils.config import FEATURES_DIR, MLFLOW_DIR, MODELS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

FEATURE_COLS = [
    "games_7d",
    "games_14d",
    "games_30d",
    "playtime_7d_hours",
    "playtime_14d_hours",
    "playtime_30d_hours",
    "avg_daily_sessions_7d",
    "avg_daily_sessions_14d",
    "avg_daily_sessions_30d",
    "max_gap_days_30d",
    "games_trend_7d_vs_14d",
    "playtime_trend_7d_vs_14d",
    "win_rate_7d",
    "win_rate_30d",
    "rating_change_30d",
    "unique_peers_30d",
    "peer_games_30d",
    "engagement_score",
    "days_since_last_game",
    # Real network proxy features (behavioral signals from API data)
    "abandon_rate",           # OpenDota: fraction of games with leaver_status != 0
    "abnormal_duration_rate", # OpenDota: fraction of games with abnormal duration
    "short_session_rate",     # Steam: fraction of sessions < 10 min
    "remake_rate",            # Riot LoL: fraction of games < 5 min
    "early_exit_rate",        # Riot LoL/Valorant: fraction of games with early exit
    # Sionna-grounded network features (avg_sinr kept; grounded by ping in live lookup)
    "avg_sinr_db",
    "peak_hour_latency_ms",
    # Game platform (encoded): 0=opendota, 1=steam, 2=riot_lol, 3=riot_valorant
    "platform_encoded",
]

TARGET_COL = "churned"


def load_features() -> pl.DataFrame:
    """Load feature data from parquet file.

    Requires real data collected from the game APIs.
    Run `make collect && make features` first to generate this file.

    For a demo without real data, use the explicit demo mode in the frontend
    which loads synthetic data through /api/v1/demo — not this pipeline.
    """
    parquet_path = FEATURES_DIR / "player_features.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"No feature data found at {parquet_path}.\n"
            "Run the collection pipeline first:\n"
            "  make collect   ← pulls data from OpenDota + Steam APIs\n"
            "  make features  ← engineers features from raw data\n"
            "  make train     ← trains models on real data\n"
            "\n"
            "For demo purposes without API keys, use the frontend Demo Mode toggle\n"
            "which serves synthetic data through /api/v1/demo."
        )
    log.info("Loading features from %s", parquet_path)
    return pl.read_parquet(parquet_path)


def prepare_data(
    df: pl.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Prepare train/test splits from feature DataFrame."""
    # Ensure all feature columns exist
    available_cols = [c for c in FEATURE_COLS if c in df.columns]
    log.info("Using %d/%d feature columns", len(available_cols), len(FEATURE_COLS))

    X = df.select(available_cols).fill_null(0).to_numpy()
    y = df[TARGET_COL].cast(pl.Int32).to_numpy()

    # Stratify only when every class has >= 2 members (requires n >= 10 for 80/20 split)
    min_class_count = np.bincount(y).min()
    stratify = y if min_class_count >= 2 else None
    if stratify is None:
        log.warning("Too few samples for stratified split (%d rows) — using random split", len(y))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Save scaler
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")

    return X_train, X_test, y_train, y_test, available_cols


def build_models() -> dict:
    """Build all model instances."""
    from catboost import CatBoostClassifier
    from lightgbm import LGBMClassifier
    from xgboost import XGBClassifier

    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=42, class_weight="balanced"
        ),
        "xgboost": XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric="logloss",
            use_label_encoder=False,
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            verbose=-1,
        ),
        "catboost": CatBoostClassifier(
            iterations=200,
            depth=6,
            learning_rate=0.1,
            random_seed=42,
            verbose=0,
            train_dir=str(MLFLOW_DIR / "catboost_info"),
        ),
    }
    return models


def evaluate_model(
    model_name: str,
    model: object,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, float]:
    """Evaluate a trained model and return metrics."""
    y_pred = model.predict(X_test)  # type: ignore[union-attr]
    y_proba = model.predict_proba(X_test)[:, 1]  # type: ignore[union-attr]

    metrics = {
        "auc": roc_auc_score(y_test, y_proba),
        "f1": f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
    }

    log.info(
        "%s — AUC: %.4f | F1: %.4f | Precision: %.4f | Recall: %.4f",
        model_name,
        metrics["auc"],
        metrics["f1"],
        metrics["precision"],
        metrics["recall"],
    )

    cm = confusion_matrix(y_test, y_pred)
    log.info("%s confusion matrix:\n%s", model_name, cm)
    log.info("%s classification report:\n%s", model_name, classification_report(y_test, y_pred))

    return metrics


def train_and_log(
    models: dict,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str],
) -> dict[str, float]:
    """Train all models with MLflow tracking."""
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DIR / 'mlflow.db'}")
    mlflow.set_experiment("playerpulse")
    best_auc = 0.0
    best_model_name = ""
    all_metrics: dict[str, float] = {}

    for name, model in models.items():
        with mlflow.start_run(run_name=name):
            log.info("Training %s...", name)
            model.fit(X_train, y_train)

            metrics = evaluate_model(name, model, X_test, y_test)
            all_metrics[name] = metrics["auc"]

            # Log to MLflow — replace nan (undefined AUC on single-class test sets) with 0.0
            safe_metrics = {k: (0.0 if np.isnan(v) else v) for k, v in metrics.items()}
            mlflow.log_params({"model": name, "n_features": len(feature_names)})
            mlflow.log_metrics(safe_metrics)

            # Save locally
            model_path = MODELS_DIR / f"{name}.joblib"
            joblib.dump(model, model_path)
            log.info("Saved %s to %s", name, model_path)

            if metrics["auc"] > best_auc:
                best_auc = metrics["auc"]
                best_model_name = name

    # Build soft-voting ensemble from the trained models
    log.info("Building soft-voting ensemble...")
    with mlflow.start_run(run_name="ensemble"):
        ensemble = VotingClassifier(
            estimators=list(models.items()),
            voting="soft",
        )
        # VotingClassifier needs to be fit, but we already have trained estimators
        # Set them directly to avoid retraining
        ensemble.estimators_ = list(models.values())
        le = LabelEncoder()
        le.classes_ = np.array([0, 1])
        ensemble.le_ = le  # type: ignore[attr-defined]
        ensemble.classes_ = np.array([0, 1])

        metrics = evaluate_model("ensemble", ensemble, X_test, y_test)
        all_metrics["ensemble"] = metrics["auc"]
        safe_metrics = {k: (0.0 if np.isnan(v) else v) for k, v in metrics.items()}
        mlflow.log_params({"model": "ensemble", "n_models": len(models)})
        mlflow.log_metrics(safe_metrics)

        joblib.dump(ensemble, MODELS_DIR / "ensemble.joblib")

        if metrics["auc"] > best_auc:
            best_auc = metrics["auc"]
            best_model_name = "ensemble"

    log.info("Best model: %s (AUC=%.4f)", best_model_name, best_auc)
    return all_metrics


def generate_shap_plots(
    model_name: str,
    X_test: np.ndarray,
    feature_names: list[str],
) -> None:
    """Generate SHAP explainability plots."""
    import shap

    log.info("Generating SHAP plots for %s...", model_name)

    model = joblib.load(MODELS_DIR / f"{model_name}.joblib")

    # Use TreeExplainer for tree models, KernelExplainer for others
    tree_models = {"xgboost", "lightgbm", "catboost"}
    if model_name in tree_models:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test[:200])
    else:
        explainer = shap.KernelExplainer(model.predict_proba, X_test[:50])  # type: ignore[union-attr]
        shap_values = explainer.shap_values(X_test[:200])

    # Save SHAP values for dashboard
    shap_output = MODELS_DIR / "shap_values.joblib"
    joblib.dump(
        {
            "shap_values": shap_values,
            "feature_names": feature_names,
            "X_sample": X_test[:200],
        },
        shap_output,
    )
    log.info("SHAP values saved to %s", shap_output)


def main() -> None:
    """Run full training pipeline.

    Pass --synthetic to train on generated synthetic data (no API keys needed).
    Default: loads real feature data from data/03_features/player_features.parquet.
    """
    import sys

    use_synthetic = "--synthetic" in sys.argv

    if use_synthetic:
        from playerpulse.models.synthetic import generate_synthetic_data

        log.info("Training on synthetic data (2000 players, 5 archetypes + network features)")
        df = generate_synthetic_data(n_players=2000, seed=42)
    else:
        df = load_features()

    log.info("Dataset: %d rows, %d columns", len(df), len(df.columns))

    X_train, X_test, y_train, y_test, feature_names = prepare_data(df)
    log.info("Train: %d, Test: %d", len(X_train), len(X_test))

    models = build_models()
    train_and_log(models, X_train, X_test, y_train, y_test, feature_names)

    # Generate SHAP using LightGBM — XGBoost 2.x has a known base_score
    # serialization incompatibility with SHAP ('[6E-1]' float parse error).
    generate_shap_plots("lightgbm", X_test, feature_names)

    log.info("Training pipeline complete!")


if __name__ == "__main__":
    main()
