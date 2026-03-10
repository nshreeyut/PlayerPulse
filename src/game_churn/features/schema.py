"""Unified player-activity schema definitions."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlayerActivity(BaseModel):
    """A single game/match activity record, standardized across platforms."""

    player_id: str = Field(description="Unique player identifier")
    platform: str = Field(description="Source platform (opendota, steam)")
    game_timestamp: datetime = Field(description="When the game was played")
    duration_seconds: int = Field(default=0, description="Game duration in seconds")
    result: str = Field(default="unknown", description="Game result (win/loss/draw)")
    rating: int | None = Field(default=None, description="Player rating at time of game")
    game_mode: str = Field(default="unknown", description="Game mode / time control")


class PlayerFeatures(BaseModel):
    """Engineered features for a single player snapshot."""

    player_id: str
    platform: str

    # Activity counts
    games_7d: int = 0
    games_14d: int = 0
    games_30d: int = 0

    # Playtime
    playtime_7d_hours: float = 0.0
    playtime_14d_hours: float = 0.0
    playtime_30d_hours: float = 0.0

    # Session patterns
    avg_daily_sessions_7d: float = 0.0
    avg_daily_sessions_14d: float = 0.0
    avg_daily_sessions_30d: float = 0.0
    max_gap_days_30d: float = 0.0

    # Trend features
    games_trend_7d_vs_14d: float = 0.0  # ratio of 7d / 14d activity
    playtime_trend_7d_vs_14d: float = 0.0

    # Performance
    win_rate_7d: float = 0.0
    win_rate_30d: float = 0.0
    rating_current: int | None = None
    rating_change_30d: int = 0

    # Social (OpenDota-specific, defaults for others)
    unique_peers_30d: int = 0
    peer_games_30d: int = 0

    # Engagement score (composite)
    engagement_score: float = 0.0

    # Days since last game
    days_since_last_game: float = 0.0

    # Target
    churned: bool = False
