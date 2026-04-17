"""Schema Agent — LLM-powered column mapping for studio file uploads.

Takes a sample of rows from a studio's uploaded file and infers
the mapping from their column names to PlayerPulse's feature schema.

TODO (Sprint 5):
  - infer_field_mapping(sample_rows, column_names) → FieldMap
  - Uses get_llm() to propose mappings with confidence scores
  - Studio reviews and confirms mapping before processing begins
"""

from api.config import get_llm

# Target schema columns the agent maps to
TARGET_SCHEMA = [
    "player_id", "platform",
    "games_7d", "games_14d", "games_30d",
    "playtime_7d_hours", "playtime_14d_hours", "playtime_30d_hours",
    "avg_daily_sessions_7d", "avg_daily_sessions_14d", "avg_daily_sessions_30d",
    "max_gap_days_30d", "games_trend_7d_vs_14d", "playtime_trend_7d_vs_14d",
    "win_rate_7d", "win_rate_30d", "rating_change_30d",
    "unique_peers_30d", "peer_games_30d", "engagement_score", "days_since_last_game",
    # Network features (optional)
    "avg_sinr_db", "p95_latency_ms", "packet_loss_rate", "jitter_ms",
    "disconnect_count", "peak_hour_latency_ms",
]


def infer_field_mapping(column_names: list[str], sample_rows: list[dict]) -> dict:
    """Use LLM to map studio column names to PlayerPulse schema.

    Args:
        column_names: List of column names from the studio's file
        sample_rows: First 5-10 rows for context

    Returns:
        Dict mapping studio column → PlayerPulse field (None if no match)

    TODO (Sprint 5): implement using get_llm() with a structured output prompt.
    """
    raise NotImplementedError(
        "TODO (Sprint 5): implement schema agent using get_llm(). "
        "Prompt the LLM with column_names + sample_rows + TARGET_SCHEMA, "
        "ask it to return a JSON mapping of studio_col → playerpulse_field."
    )
