"""
Churn Analyst Agent
====================
Provides tools and the LLM call wrapper for the live chat endpoint.

Tools are defined here for future agent-framework integration. The current
`get_agent()` returns a direct LLM wrapper that injects player context and
dataset context into a rich system prompt — the same pattern as demo chat,
proven to work across all 7 LLM providers.

Tools remain available for standalone use (e.g., from scripts or tests).
"""

from langchain_core.tools import tool

from api.services.data_service import get_player, get_dataset_summary
from api.services.model_service import predict_churn
from api.services.shap_service import get_player_shap, FEATURE_LABELS
from api.config import get_llm

SYSTEM_PROMPT_TEMPLATE = """You are a game analytics expert specializing in player churn prediction.

You have access to a machine learning system that:
  - Predicts whether players are about to stop playing their games (churn probability 0–1)
  - Explains WHY using SHAP feature importance values
  - Covers multiple platforms: OpenDota (Dota 2), Steam, League of Legends, Valorant

Your audience includes game designers, business stakeholders, and data science students.

Dataset context:
{dataset_context}

{player_context}

Guidelines:
- Be specific — reference actual numbers from the player data when available
- Suggest concrete, actionable retention strategies when asked
- Explain SHAP values in plain English if asked
- Keep responses clear and concise
"""


@tool
def get_player_data(player_id: str, platform: str) -> dict:
    """
    Fetch a player's features and churn prediction from the ML system.
    Use this when the user asks about a specific player's risk level or statistics.

    Args:
        player_id: The player's ID (e.g., "12345" for OpenDota)
        platform:  The gaming platform key (opendota, steam, riot_lol, riot_valorant)
    """
    features = get_player(player_id, platform)
    if features is None:
        return {"error": f"Player {player_id} not found on {platform}"}
    prediction = predict_churn(features)
    return {"player_id": player_id, "platform": platform, "features": features, "prediction": prediction}


@tool
def explain_prediction(player_id: str, platform: str) -> str:
    """
    Get a plain-English explanation of WHY the model predicts churn for this player.
    Use this when the user asks why a player is at risk or what factors are driving their score.
    """
    shap_values = get_player_shap(player_id, platform)
    if shap_values is None:
        return "No SHAP explanation available for this player."

    top5 = shap_values[:5]
    lines = []
    for sv in top5:
        direction = "strongly" if abs(sv["shap_value"]) > 0.2 else "slightly"
        impact = "increases" if sv["direction"] == "increases_churn" else "reduces"
        lines.append(f"• {sv['label']} ({sv['shap_value']:+.3f}): {direction} {impact} churn risk")
    return "\n".join(lines)


@tool
def get_dataset_context() -> dict:
    """
    Get overall statistics about the game churn dataset.
    Use this when the user asks general questions about churn rates or platforms.
    """
    return get_dataset_summary()


_RETENTION_MAP = {
    "days_since_last_game":    "Send a re-engagement notification or email with a personalized hook",
    "games_7d":                "Offer a time-limited reward for logging in this week",
    "games_trend_7d_vs_14d":   "Offer a time-limited reward for logging in this week",
    "win_rate_7d":             "Adjust matchmaking — the player may be frustrated by losses",
    "win_rate_30d":            "Adjust matchmaking — the player may be frustrated by losses",
    "unique_peers_30d":        "Promote social/team features; suggest finding regular teammates",
    "peer_games_30d":          "Promote social/team features; suggest finding regular teammates",
    "max_gap_days_30d":        "The player takes long breaks — consider a streak reward system",
    "abandon_rate":            "Investigate connectivity issues; offer network quality support",
    "short_session_rate":      "Review onboarding/tutorial — player may be hitting friction early",
    "early_exit_rate":         "Review matchmaking or difficulty balance — player exits frequently",
}


@tool
def suggest_retention_strategy(player_id: str, platform: str) -> str:
    """
    Generate personalized retention recommendations for a specific at-risk player.
    Use this when the user asks how to retain a player or what actions to take.
    """
    shap_values = get_player_shap(player_id, platform)
    if shap_values is None:
        return (
            "• Send a personalized re-engagement email highlighting recent game updates\n"
            "• Offer a limited-time in-game reward for returning this week\n"
            "• Review matchmaking quality for this player's skill tier"
        )

    top_risk = [sv for sv in shap_values if sv["direction"] == "increases_churn"][:3]
    recommendations = []
    seen: set = set()
    for sv in top_risk:
        rec = _RETENTION_MAP.get(sv["feature"])
        if rec and rec not in seen:
            recommendations.append(f"• {rec}")
            seen.add(rec)

    return "\n".join(recommendations[:3]) if recommendations else "• Consider a personalized re-engagement campaign"


def build_system_prompt(player_context: dict | None = None) -> str:
    """Build a rich system prompt with dataset stats and optional player context."""
    try:
        summary = get_dataset_summary()
        dataset_ctx = (
            f"- Total players: {summary['total_players']}\n"
            f"- Overall churn rate: {summary['churn_rate']:.1%}\n"
            f"- Platforms: {summary['platforms']}"
        )
    except Exception:
        dataset_ctx = "(dataset stats unavailable)"

    player_ctx = ""
    if player_context:
        p = player_context
        pred = p.get("prediction", {})
        shap = p.get("shap_values", [])
        top_factors = [
            f"{s['label']} (impact: {s['shap_value']:+.3f})"
            for s in shap[:3]
        ]
        player_ctx = (
            f"\nCurrently viewing player: {p.get('player_id')} on {p.get('platform')}\n"
            f"Churn probability: {pred.get('churn_probability', 'N/A')}\n"
            f"Risk level: {pred.get('risk_level', 'N/A')}\n"
            f"Top churn drivers: {', '.join(top_factors) if top_factors else 'N/A'}\n"
        )

    return SYSTEM_PROMPT_TEMPLATE.format(
        dataset_context=dataset_ctx,
        player_context=player_ctx,
    )


def get_agent():
    """
    Return the LLM configured for streaming.

    Returns the raw LLM (not a LangGraph agent) so that callers can use
    the same direct-streaming pattern that works reliably across all 7 providers.
    The system prompt (built by build_system_prompt) carries all the player
    context the LLM needs to answer questions without tool calls.
    """
    return get_llm(streaming=True)
