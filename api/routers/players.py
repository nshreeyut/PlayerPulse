"""
Players Router
===============
Defines all HTTP endpoints related to player data, predictions, and metadata.

FastAPI uses Python type hints to:
  1. Parse and validate incoming data automatically
  2. Generate /docs documentation without any extra work
  3. Return helpful 422 errors when data is wrong

ENDPOINT OVERVIEW:
  GET /api/v1/players/games            → list of supported game platforms (from game_registry)
  GET /api/v1/players/models           → list of registered ML models (from model_registry)
  GET /api/v1/players                  → browse/search players in the dataset
  GET /api/v1/players/{platform}/{id}  → full analytics for one player

NOTE ON ROUTE ORDER:
FastAPI matches routes top to bottom. "/games" and "/models" must be defined
BEFORE "/{platform}/{id}" otherwise FastAPI would try to interpret "games"
as a platform parameter.

LEARN MORE:
  Path parameters:  https://fastapi.tiangolo.com/tutorial/path-params/
  Query parameters: https://fastapi.tiangolo.com/tutorial/query-params/
  HTTPException:    https://fastapi.tiangolo.com/tutorial/handling-errors/
"""

from fastapi import APIRouter, HTTPException, Query

from api.registry.game_registry import get_supported_games, get_game
from api.registry.model_registry import list_models, DEFAULT_MODEL
from api.services.data_service import get_player, list_players
from api.services.model_service import predict_churn
from api.services.shap_service import get_player_shap

# APIRouter groups related endpoints.
# Registered in main.py with prefix="/api/v1/players".
router = APIRouter()


@router.get("/games")
def get_games():
    """
    Returns the list of supported gaming platforms.
    The React frontend calls this to dynamically build the platform dropdown.
    When you add a new game to game_registry.py, it appears here automatically.
    """
    return get_supported_games()


@router.get("/models")
def get_models():
    """
    Returns all registered ML models with descriptions.
    The frontend can use this to let users choose which model powers predictions.
    """
    return list_models()


@router.get("")
def search_players(
    platform: str | None = Query(default=None, description="Filter by platform ID (e.g., opendota)"),
    limit: int = Query(default=50, ge=1, le=500, description="Max number of players to return"),
):
    """
    Browse players in the dataset, optionally filtered by platform.

    Query parameters are parsed automatically from the URL:
      GET /api/v1/players?platform=opendota&limit=20

    TODO: Implement this endpoint.
    Steps:
      1. Call list_players(platform=platform, limit=limit) from data_service
      2. Wrap in a try/except — if the features file doesn't exist, raise:
         HTTPException(status_code=503, detail="Features not ready. Run `make train`.")
      3. Return the list of player dicts
    """
    raise NotImplementedError("TODO: implement search_players()")


@router.get("/{platform}/{player_id}")
def get_player_analytics(
    platform: str,
    player_id: str,
    model_id: str = Query(default=DEFAULT_MODEL, description="Model ID to use for prediction"),
):
    """
    Core endpoint: returns full analytics for a single player.

    This powers the Player Lookup page in the React frontend.

    Response shape:
    {
        "player_id": "hikaru",
        "platform": "opendota",
        "features": { ...all feature columns... },
        "prediction": {
            "churn_probability": 0.73,
            "churn_predicted": true,
            "risk_level": "High",
            "model_used": "ensemble"
        },
        "shap_values": [
            {"feature": "days_since_last_game", "label": "...", "shap_value": 0.42, "direction": "increases_churn"},
            ...
        ]
    }

    TODO: Implement this endpoint.
    Steps:
      1. Validate platform: try get_game(platform), raise HTTPException(404) if KeyError
      2. Look up player: features = get_player(player_id, platform)
         If None: raise HTTPException(status_code=404, detail="Player not found in dataset.")
      3. Run prediction: prediction = predict_churn(features, model_id)
         Catch any exception and raise HTTPException(500) with the error message
      4. Get SHAP values: shap = get_player_shap(player_id, platform)
         (shap can be None — that's ok, just include it as-is)
      5. Return the combined dict in the shape above
    """
    raise NotImplementedError("TODO: implement get_player_analytics()")
