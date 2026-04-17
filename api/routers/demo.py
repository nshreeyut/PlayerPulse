"""Demo Router
=============
Serves synthetic data for frontend demo mode.

All responses include "_demo": true so the frontend can display a clear
"Running on synthetic data" banner. These endpoints are completely separate
from the real /api/v1/players routes and never touch real studio data.

Endpoints:
  GET  /api/v1/demo/summary              — fleet-level stats across all demo players
  GET  /api/v1/demo/players              — list demo players (filterable by platform)
  GET  /api/v1/demo/players/{player_id}  — full analytics for one demo player
  POST /api/v1/demo/chat                 — chat agent with demo context
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.services.demo_service import (
    get_demo_player,
    get_demo_summary,
    list_demo_players,
)

router = APIRouter()


@router.get("/summary")
def demo_summary():
    """Fleet-level churn stats across all synthetic demo players."""
    return get_demo_summary()


@router.get("/players")
def demo_players(
    platform: str | None = Query(None, description="Filter by platform: opendota or steam"),
    limit: int = Query(20, ge=1, le=50),
):
    """List synthetic demo players sorted by churn risk (highest first)."""
    players = list_demo_players(platform=platform, limit=limit)
    return {"players": players, "total": len(players), "_demo": True}


@router.get("/players/{player_id}")
def demo_player_analytics(player_id: str):
    """Full churn analytics for a single synthetic demo player."""
    player = get_demo_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=404,
            detail=f"Demo player '{player_id}' not found. "
                   "Valid IDs are 'Player_1' through 'Player_50'.",
        )
    return player


class DemoChatRequest(BaseModel):
    message: str
    player_id: str | None = None  # optionally scoped to a specific demo player
    conversation_history: list[dict] = []


@router.post("/chat")
async def demo_chat(request: DemoChatRequest):
    """Streaming chat agent with demo context.

    The agent has access to the synthetic demo dataset and answers questions
    about demo players. Clearly scoped to synthetic data.
    """
    from api.config import get_llm
    from api.services.demo_service import get_demo_player, get_demo_summary

    # Build context for the agent
    summary = get_demo_summary()
    player_context = ""
    if request.player_id:
        player = get_demo_player(request.player_id)
        if player:
            top_factors = [
                f"{s['label']} (impact: {s['shap_value']:+.3f})"
                for s in player.get("shap_values", [])[:3]
            ]
            player_context = (
                f"\nCurrently viewing player: {request.player_id}\n"
                f"Platform: {player['platform']}\n"
                f"Churn probability: {player['churn_probability']:.1%}\n"
                f"Risk level: {player['risk_level']}\n"
                f"Top churn drivers: {', '.join(top_factors)}\n"
            )

    system_prompt = f"""You are a player retention analyst demonstrating a churn prediction platform.
You are running in DEMO MODE using synthetic data — always be transparent about this.

Demo dataset summary:
- Total players: {summary['total_players']}
- Overall churn rate: {summary['churn_rate']:.1%}
- High risk: {summary['high_risk_count']} players
- Medium risk: {summary['medium_risk_count']} players
- Low risk: {summary['low_risk_count']} players
- Platforms: {summary['platforms']}
{player_context}
Answer questions about churn risk, player behavior patterns, and retention strategies.
Always remind users this is synthetic demo data, not real player data.
Be concise, direct, and actionable."""

    async def stream():
        llm = get_llm(streaming=True)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in request.conversation_history[-6:]:  # last 3 turns
            messages.append(msg)
        messages.append({"role": "user", "content": request.message})

        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(stream(), media_type="text/plain")
