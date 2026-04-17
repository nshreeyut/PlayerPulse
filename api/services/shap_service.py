"""
SHAP Service
=============
Handles live SHAP computation for any player using a cached TreeExplainer.

Live computation (vs pre-computed values) works for ANY player — not just the
200 test-set rows. The explainer object is cached with @lru_cache so it's only
built once per API process lifetime.
"""

import numpy as np
import shap
from functools import lru_cache

from api.services.model_service import FEATURE_COLUMNS, load_model, load_scaler

# Human-readable labels for every feature in FEATURE_COLUMNS.
# Used by the LangChain agent to generate plain-English explanations.
FEATURE_LABELS = {
    "games_7d":                "Games played in the last 7 days",
    "games_14d":               "Games played in the last 14 days",
    "games_30d":               "Games played in the last 30 days",
    "playtime_7d_hours":       "Hours played in the last 7 days",
    "playtime_14d_hours":      "Hours played in the last 14 days",
    "playtime_30d_hours":      "Hours played in the last 30 days",
    "avg_daily_sessions_7d":   "Average daily sessions (last 7 days)",
    "avg_daily_sessions_14d":  "Average daily sessions (last 14 days)",
    "avg_daily_sessions_30d":  "Average daily sessions (last 30 days)",
    "max_gap_days_30d":        "Longest break between games (last 30 days)",
    "games_trend_7d_vs_14d":   "Activity trend (recent vs earlier — above 0.5 = increasing)",
    "playtime_trend_7d_vs_14d":"Playtime trend (recent vs earlier)",
    "win_rate_7d":             "Win rate in the last 7 days",
    "win_rate_30d":            "Win rate in the last 30 days",
    "rating_change_30d":       "Rating change over last 30 days",
    "unique_peers_30d":        "Unique teammates in the last 30 days",
    "peer_games_30d":          "Games played with teammates (last 30 days)",
    "engagement_score":        "Overall engagement score (0–100 composite)",
    "days_since_last_game":    "Days since their last game",
    "abandon_rate":            "Fraction of games abandoned mid-match",
    "abnormal_duration_rate":  "Fraction of games with abnormal duration",
    "short_session_rate":      "Fraction of sessions shorter than 10 minutes",
    "remake_rate":             "Fraction of games that were remade (< 5 min)",
    "early_exit_rate":         "Fraction of games exited early",
    "avg_sinr_db":             "Average signal quality (SINR dB)",
    "peak_hour_latency_ms":    "Peak hour latency (ms)",
    "platform_encoded":        "Gaming platform",
}


@lru_cache(maxsize=1)
def _get_explainer():
    """Build and cache a SHAP TreeExplainer for LightGBM (called once per process).

    LightGBM is used here because XGBoost 2.x has a known SHAP serialization
    incompatibility (base_score stored as string). LightGBM gives equivalent
    SHAP quality and works reliably.
    """
    model = load_model("lightgbm")
    return shap.TreeExplainer(model)


def compute_shap_live(features: dict) -> list[dict]:
    """
    Compute SHAP feature contributions for any player on-the-fly.

    Args:
        features: dict of {feature_name: value} covering all FEATURE_COLUMNS

    Returns sorted list (most impactful first):
    [
        {
            "feature":    "days_since_last_game",
            "label":      "Days since their last game",
            "shap_value": 0.42,
            "direction":  "increases_churn",
        },
        ...
    ]
    """
    explainer = _get_explainer()
    scaler = load_scaler()

    values = [features.get(col, 0) for col in FEATURE_COLUMNS]
    X = np.array(values).reshape(1, -1)
    X_scaled = scaler.transform(X)

    shap_row = explainer.shap_values(X_scaled)[0]

    pairs = [
        {
            "feature":    col,
            "label":      FEATURE_LABELS.get(col, col),
            "shap_value": round(float(shap_row[i]), 4),
            "direction":  "increases_churn" if shap_row[i] > 0 else "decreases_churn",
        }
        for i, col in enumerate(FEATURE_COLUMNS)
    ]
    return sorted(pairs, key=lambda x: abs(x["shap_value"]), reverse=True)


def get_player_shap(player_id: str, platform: str) -> list[dict] | None:
    """
    Get SHAP values for a player already in the dataset (via their features).
    Returns None — callers should use compute_shap_live() with live features instead.

    Pre-computed SHAP over a fixed test set is no longer used; live computation
    works for any player including new ones not in the training data.
    """
    return None
