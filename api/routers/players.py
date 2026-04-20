"""
Players Router
===============
HTTP endpoints for player data, predictions, and metadata.

  GET /api/v1/players/games            → supported game platforms
  GET /api/v1/players/models           → registered ML models
  GET /api/v1/players                  → browse/search players in the dataset
  GET /api/v1/players/{platform}/{id}  → full analytics for one player (live lookup)
"""

from fastapi import APIRouter, HTTPException, Query

from api.registry.game_registry import get_supported_games, get_game
from api.registry.model_registry import list_models, DEFAULT_MODEL
from api.services.data_service import list_players, get_player_live
from api.services.model_service import predict_churn
from api.services.shap_service import compute_shap_live

router = APIRouter()


@router.get("/games")
def get_games():
    """Returns the list of supported gaming platforms for the frontend dropdown."""
    return get_supported_games()


@router.get("/models")
def get_models():
    """Returns all registered ML models with descriptions."""
    return list_models()


@router.get("")
def search_players(
    platform: str | None = Query(default=None, description="Filter by platform ID (e.g., opendota)"),
    limit: int = Query(default=50, ge=1, le=500, description="Max number of players to return"),
):
    """Browse players in the dataset, optionally filtered by platform."""
    try:
        return list_players(platform=platform, limit=limit)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Features not ready. Run `make train`.")


@router.get("/{platform}/{player_id:path}")
def get_player_analytics(
    platform: str,
    player_id: str,
    model_id: str = Query(default=DEFAULT_MODEL, description="Model ID to use for prediction"),
):
    """
    Core endpoint: live analytics for a single player.

    Calls the game API in real time, engineers features, runs prediction and SHAP.
    Response shape:
    {
        "player_id": "87278757",
        "platform": "opendota",
        "features": { ...all 27 feature columns... },
        "prediction": { "churn_probability": 0.73, "risk_level": "High", ... },
        "shap_values": [{ "feature": "days_since_last_game", "shap_value": 0.42, ... }, ...]
    }
    """
    # Validate platform
    try:
        get_game(platform)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Live collect + feature engineering
    try:
        features = get_player_live(player_id, platform)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch player data: {e}")

    # Prediction
    try:
        prediction = predict_churn(features, model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    # SHAP
    shap_values = compute_shap_live(features)

    return {
        "player_id": player_id,
        "platform": platform,
        "features": features,
        "prediction": prediction,
        "shap_values": shap_values,
    }
