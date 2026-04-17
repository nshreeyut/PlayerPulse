"""
Model Service
==============
Handles loading trained ML models from disk and running predictions.

WHY A SERVICE LAYER?
---------------------
Routers (api/routers/) handle HTTP concerns: parsing requests, returning responses.
Services handle business logic: loading models, making predictions, crunching numbers.

Keeping these separate means:
  - You can test prediction logic without spinning up an HTTP server
  - You can swap the model loading library without touching any router
  - Code stays readable as the project grows

HOW PREDICTIONS WORK (end to end):
------------------------------------
1. load_model()  — reads the .joblib file once, caches it in memory
2. load_scaler() — reads the StandardScaler fitted during training
3. predict_churn() is called with a player's features dict
4. Features are arranged into the correct column order
5. Scaled with the same scaler used in training (CRITICAL — wrong scaler = bad predictions)
6. model.predict_proba() returns [[prob_not_churn, prob_churn]]
7. We extract prob_churn, add a risk label, and return

CACHING WITH @lru_cache:
-------------------------
@lru_cache(maxsize=None) memoizes the function — it only runs ONCE per unique
argument. After that, it returns the cached result instantly.
This matters because joblib.load() reads from disk, which is slow.
Without caching, every prediction request would reload the model file.
"""

import joblib
import numpy as np
from functools import lru_cache

from api.registry.model_registry import MODEL_REGISTRY, DEFAULT_MODEL, get_model_info
from api.config import settings

# The feature columns in the exact order the model was trained on.
# IMPORTANT: The model expects features in this specific order.
# If you add or remove features in the ML pipeline, update this list.
# Must stay in sync with FEATURE_COLS in src/playerpulse/models/train.py.
FEATURE_COLUMNS = [
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
    # Real network proxy features
    "abandon_rate",
    "abnormal_duration_rate",
    "short_session_rate",
    "remake_rate",
    "early_exit_rate",
    # Sionna-grounded network features
    "avg_sinr_db",
    "peak_hour_latency_ms",
    # Game platform (encoded): 0=opendota, 1=steam, 2=riot_lol, 3=riot_valorant
    "platform_encoded",
]


@lru_cache(maxsize=None)
def load_model(model_id: str = DEFAULT_MODEL):
    """Load a registered model from disk and cache it in memory."""
    info = get_model_info(model_id)
    path = info["path"]
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found: {path}\n"
            "Run `make train` to generate model artifacts."
        )
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_scaler():
    """Load the StandardScaler fitted during training."""
    path = settings.models_dir / "scaler.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"Scaler not found: {path}\n"
            "Run `make train` to generate model artifacts."
        )
    return joblib.load(path)


def predict_churn(features: dict, model_id: str = DEFAULT_MODEL) -> dict:
    """
    Given a player's features, return a churn prediction.

    Args:
        features: dict of {feature_name: value} — all keys in FEATURE_COLUMNS
        model_id: which registered model to use (default: ensemble)

    Returns:
        {
            "churn_probability": 0.73,
            "churn_predicted": True,
            "risk_level": "High",
            "model_used": "ensemble"
        }
    """
    model = load_model(model_id)
    scaler = load_scaler()

    values = [features.get(col, 0) for col in FEATURE_COLUMNS]
    X = np.array(values).reshape(1, -1)
    X_scaled = scaler.transform(X)

    proba = float(model.predict_proba(X_scaled)[0][1])

    if proba > 0.7:
        risk_level = "High"
    elif proba > 0.4:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "churn_probability": round(proba, 4),
        "churn_predicted": proba >= 0.5,
        "risk_level": risk_level,
        "model_used": model_id,
    }
