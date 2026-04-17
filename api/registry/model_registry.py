"""
Model Registry
===============
The single place where you register all trained ML models.

WHY A REGISTRY?
---------------
Your ML pipeline saves models as .joblib files. When you train something new
(a neural net, a tuned XGBoost, a completely different architecture), you:
  1. Save it to models/your_model.joblib
  2. Add an entry here

The API automatically exposes it via GET /api/v1/players/models.
The frontend can then let users SELECT which model to use for predictions,
making it easy to compare model outputs side by side.
No router or frontend code changes needed.

HOW THE MODEL IS USED:
-----------------------
When the frontend calls GET /api/v1/players/{platform}/{player_id}?model_id=xgboost,
the router passes model_id to model_service.py, which looks it up here, loads
the .joblib file, and runs prediction. Swap the model by changing the query param.
"""

from api.config import settings

MODEL_REGISTRY: dict[str, dict] = {
    "ensemble": {
        "display_name": "Soft-Voting Ensemble (Recommended)",
        "description": (
            "Combines XGBoost, LightGBM, CatBoost, and Logistic Regression. "
            "Each model votes and the average probability wins. "
            "Usually the most accurate — individual model weaknesses cancel out."
        ),
        "path": settings.models_dir / "ensemble.joblib",
    },
    "xgboost": {
        "display_name": "XGBoost",
        "description": "Gradient-boosted decision trees. Fast and accurate on tabular data.",
        "path": settings.models_dir / "xgboost.joblib",
    },
    "lightgbm": {
        "display_name": "LightGBM",
        "description": "Similar to XGBoost but faster on larger datasets (histogram-based splitting).",
        "path": settings.models_dir / "lightgbm.joblib",
    },
    "catboost": {
        "display_name": "CatBoost",
        "description": "Gradient boosting by Yandex. Needs less hyperparameter tuning.",
        "path": settings.models_dir / "catboost.joblib",
    },
    "logistic_regression": {
        "display_name": "Logistic Regression",
        "description": "Simple linear model. Most interpretable but less accurate on complex patterns.",
        "path": settings.models_dir / "logistic_regression.joblib",
    },
    # ──────────────────────────────────────────────────────────
    # TO ADD A NEW MODEL:
    # ──────────────────────────────────────────────────────────
    # 1. Train your model in the ML pipeline (src/playerpulse/models/train.py)
    # 2. Save it: joblib.dump(model, "models/my_new_model.joblib")
    # 3. Uncomment and fill in the entry below:
    #
    # "my_new_model": {
    #     "display_name": "My New Model",
    #     "description": "What makes this model interesting or different.",
    #     "path": settings.models_dir / "my_new_model.joblib",
    # },
}

# Used when no model_id is specified in the request
DEFAULT_MODEL = "ensemble"


def get_model_info(model_id: str) -> dict:
    """Look up a model by ID. Raises KeyError if not registered."""
    if model_id not in MODEL_REGISTRY:
        raise KeyError(
            f"Unknown model: '{model_id}'. "
            f"Registered models: {list(MODEL_REGISTRY.keys())}"
        )
    return MODEL_REGISTRY[model_id]


def list_models() -> list[dict]:
    """Returns all registered models — called by GET /api/v1/players/models."""
    return [
        {"id": model_id, **{k: str(v) if k == "path" else v for k, v in info.items()}}
        for model_id, info in MODEL_REGISTRY.items()
    ]
