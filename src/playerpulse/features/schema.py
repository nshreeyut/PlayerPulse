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


class NetworkFeatures(BaseModel):
    """Per-player network telemetry features from Sionna simulation.

    These features link 5G/6G network quality to player churn — the
    competitive moat. Generated via Sionna 3GPP channel models or
    statistical fallback when Sionna is not installed.
    """

    avg_sinr_db: float = Field(description="Average signal-to-interference-plus-noise ratio (dB)")
    p95_latency_ms: float = Field(description="95th percentile round-trip latency (ms)")
    packet_loss_rate: float = Field(description="Fraction of lost packets (0.0–1.0)")
    jitter_ms: float = Field(description="Latency variance / std dev (ms)")
    disconnect_count: int = Field(description="Number of connection drops in period")
    peak_hour_latency_ms: float = Field(description="Latency during peak gaming hours (ms)")


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

    # Network telemetry features (Sionna simulation — see network_features.py)
    avg_sinr_db: float = 0.0
    p95_latency_ms: float = 0.0
    packet_loss_rate: float = 0.0
    jitter_ms: float = 0.0
    disconnect_count: int = 0
    peak_hour_latency_ms: float = 0.0

    # Target
    churned: bool = False
