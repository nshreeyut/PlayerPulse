"""Tests for feature engineering pipeline."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import polars as pl

from playerpulse.features.engineer import (
    build_features_for_player,
    compute_churn_label,
    compute_engagement_score,
    compute_time_window_features,
    compute_trend_features,
)


def _make_activity_df(
    player_id: str = "test_player",
    platform: str = "opendota",
    n_games: int = 20,
    start_days_ago: int = 25,
    end_days_ago: int = 1,
) -> pl.DataFrame:
    """Create a synthetic activity DataFrame for testing."""
    now = datetime.now(tz=UTC)
    interval = (start_days_ago - end_days_ago) / max(n_games - 1, 1)
    records = []
    for i in range(n_games):
        ts = now - timedelta(days=start_days_ago - i * interval)
        records.append(
            {
                "player_id": player_id,
                "platform": platform,
                "game_timestamp": ts,
                "duration_seconds": 1800,
                "result": "win" if i % 3 != 0 else "loss",
                "rating": 1500 + i * 5,
                "game_mode": "rapid",
            }
        )
    return pl.DataFrame(records)


def test_time_window_features() -> None:
    """Test time window feature computation."""
    df = _make_activity_df(n_games=20, start_days_ago=25, end_days_ago=1)
    ref = datetime.now(tz=UTC)
    features = compute_time_window_features(df, "test_player", "opendota", ref)

    assert features["player_id"] == "test_player"
    assert features["games_30d"] == 20
    assert features["games_7d"] <= features["games_14d"] <= features["games_30d"]
    assert features["playtime_30d_hours"] > 0
    assert features["avg_daily_sessions_30d"] > 0


def test_trend_features() -> None:
    """Test trend feature computation."""
    features = {
        "games_7d": 10,
        "games_14d": 15,
        "playtime_7d_hours": 5.0,
        "playtime_14d_hours": 8.0,
    }
    result = compute_trend_features(features)
    assert result["games_trend_7d_vs_14d"] == round(10 / 15, 3)
    assert result["playtime_trend_7d_vs_14d"] == round(5.0 / 8.0, 3)


def test_trend_features_zero_denominator() -> None:
    """Test trend features with zero activity."""
    features = {
        "games_7d": 0,
        "games_14d": 0,
        "playtime_7d_hours": 0.0,
        "playtime_14d_hours": 0.0,
    }
    result = compute_trend_features(features)
    assert result["games_trend_7d_vs_14d"] == 0.0
    assert result["playtime_trend_7d_vs_14d"] == 0.0


def test_churn_label_active() -> None:
    """Test churn label for active player."""
    df = _make_activity_df(end_days_ago=1)
    ref = datetime.now(tz=UTC)
    result = compute_churn_label(df, "test_player", "opendota", ref)
    assert result["churned"] is False
    assert result["days_since_last_game"] < 14


def test_churn_label_churned() -> None:
    """Test churn label for churned player."""
    df = _make_activity_df(start_days_ago=60, end_days_ago=20)
    ref = datetime.now(tz=UTC)
    result = compute_churn_label(df, "test_player", "opendota", ref)
    assert result["churned"] is True
    assert result["days_since_last_game"] >= 14


def test_engagement_score() -> None:
    """Test engagement score calculation."""
    features = {
        "games_30d": 30,
        "avg_daily_sessions_30d": 0.5,
        "games_trend_7d_vs_14d": 0.7,
        "win_rate_30d": 0.55,
        "unique_peers_30d": 10,
    }
    score = compute_engagement_score(features)
    assert 0 <= score <= 100


def test_build_features_complete() -> None:
    """Test full feature pipeline produces all expected keys."""
    df = _make_activity_df()
    ref = datetime.now(tz=UTC)
    features = build_features_for_player(df, "test_player", "opendota", ref)

    expected_keys = {
        "player_id",
        "platform",
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
        "rating_current",
        "rating_change_30d",
        "unique_peers_30d",
        "peer_games_30d",
        "engagement_score",
        "days_since_last_game",
        "churned",
    }
    assert expected_keys.issubset(set(features.keys()))
    assert features["games_30d"] > 0
    assert features["engagement_score"] > 0
