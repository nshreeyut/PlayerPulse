"""Feature engineering: time-window, trend, social, and engagement features."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from playerpulse.utils.config import RAW_DIR, settings


def compute_time_window_features(
    df: pl.DataFrame,
    player_id: str,
    platform: str,
    reference_date: datetime | None = None,
) -> dict:
    """Compute activity features over 7d, 14d, 30d windows."""
    ref = reference_date or datetime.now(tz=UTC)

    player_df = df.filter((pl.col("player_id") == player_id) & (pl.col("platform") == platform))

    if player_df.is_empty():
        return _empty_features(player_id, platform)

    features: dict = {"player_id": player_id, "platform": platform}

    for window_days, suffix in [(7, "7d"), (14, "14d"), (30, "30d")]:
        cutoff = ref - timedelta(days=window_days)
        window_df = player_df.filter(pl.col("game_timestamp") >= cutoff)

        game_count = len(window_df)
        features[f"games_{suffix}"] = game_count

        playtime_hours = window_df["duration_seconds"].sum() / 3600.0
        features[f"playtime_{suffix}_hours"] = round(playtime_hours, 2)

        # Avg daily sessions (unique days with games / window days)
        if game_count > 0:
            unique_days = window_df.select(
                pl.col("game_timestamp").dt.date().alias("day")
            ).n_unique()
            features[f"avg_daily_sessions_{suffix}"] = round(unique_days / window_days, 3)
        else:
            features[f"avg_daily_sessions_{suffix}"] = 0.0

    # Max gap in last 30 days
    cutoff_30 = ref - timedelta(days=30)
    recent = player_df.filter(pl.col("game_timestamp") >= cutoff_30).sort("game_timestamp")
    if len(recent) >= 2:
        timestamps = recent["game_timestamp"].to_list()
        gaps = [
            (timestamps[i + 1] - timestamps[i]).total_seconds() / 86400
            for i in range(len(timestamps) - 1)
        ]
        features["max_gap_days_30d"] = round(max(gaps), 2)
    else:
        features["max_gap_days_30d"] = 30.0

    return features


def compute_trend_features(features: dict) -> dict:
    """Compute engagement trajectory features."""
    games_7d = features.get("games_7d", 0)
    games_14d = features.get("games_14d", 0)

    # Ratio of recent (7d) vs broader (14d) - values > 0.5 = increasing
    if games_14d > 0:
        features["games_trend_7d_vs_14d"] = round(games_7d / games_14d, 3)
    else:
        features["games_trend_7d_vs_14d"] = 0.0

    pt_7d = features.get("playtime_7d_hours", 0.0)
    pt_14d = features.get("playtime_14d_hours", 0.0)
    if pt_14d > 0:
        features["playtime_trend_7d_vs_14d"] = round(pt_7d / pt_14d, 3)
    else:
        features["playtime_trend_7d_vs_14d"] = 0.0

    return features


def compute_performance_features(
    df: pl.DataFrame,
    player_id: str,
    platform: str,
    reference_date: datetime | None = None,
) -> dict:
    """Compute win rate and rating features."""
    ref = reference_date or datetime.now(tz=UTC)
    player_df = df.filter((pl.col("player_id") == player_id) & (pl.col("platform") == platform))

    features: dict = {}

    for window_days, suffix in [(7, "7d"), (30, "30d")]:
        cutoff = ref - timedelta(days=window_days)
        window_df = player_df.filter(pl.col("game_timestamp") >= cutoff)
        total = len(window_df)
        if total > 0:
            wins = len(window_df.filter(pl.col("result") == "win"))
            features[f"win_rate_{suffix}"] = round(wins / total, 3)
        else:
            features[f"win_rate_{suffix}"] = 0.0

    # Rating
    rated = player_df.filter(pl.col("rating").is_not_null()).sort("game_timestamp")
    if len(rated) > 0:
        features["rating_current"] = rated["rating"][-1]
        cutoff_30 = ref - timedelta(days=30)
        old_rated = rated.filter(pl.col("game_timestamp") <= cutoff_30)
        if len(old_rated) > 0:
            features["rating_change_30d"] = features["rating_current"] - old_rated["rating"][-1]
        else:
            features["rating_change_30d"] = 0
    else:
        features["rating_current"] = None
        features["rating_change_30d"] = 0

    return features


def compute_social_features(player_id: str, raw_dir: Path | None = None) -> dict:
    """Compute social features from OpenDota peer data."""
    base = (raw_dir or RAW_DIR) / "opendota"
    peers_path = base / f"{player_id}_peers.json"

    features: dict = {"unique_peers_30d": 0, "peer_games_30d": 0}

    if not peers_path.exists():
        return features

    peers = json.loads(peers_path.read_text())
    features["unique_peers_30d"] = len(peers)
    features["peer_games_30d"] = sum(p.get("games", 0) for p in peers)

    return features


def compute_engagement_score(features: dict) -> float:
    """Composite engagement score (0-100) from multiple signals."""
    score = 0.0

    # Activity volume (max 30 points)
    games_30d = features.get("games_30d", 0)
    score += min(games_30d / 2.0, 30.0)

    # Session frequency (max 20 points)
    avg_sessions = features.get("avg_daily_sessions_30d", 0)
    score += min(avg_sessions * 30, 20.0)

    # Trend (max 20 points) — increasing engagement gets more points
    trend = features.get("games_trend_7d_vs_14d", 0.0)
    score += min(trend * 20, 20.0)

    # Win rate boost (max 15 points)
    wr = features.get("win_rate_30d", 0.0)
    score += wr * 15

    # Social (max 15 points)
    peers = features.get("unique_peers_30d", 0)
    score += min(peers / 3.0, 15.0)

    return round(min(score, 100.0), 2)


def compute_churn_label(
    df: pl.DataFrame,
    player_id: str,
    platform: str,
    reference_date: datetime | None = None,
) -> dict:
    """Determine if player has churned (14+ days since last game)."""
    ref = reference_date or datetime.now(tz=UTC)
    player_df = df.filter((pl.col("player_id") == player_id) & (pl.col("platform") == platform))

    if player_df.is_empty():
        return {"days_since_last_game": 999.0, "churned": True}

    last_game = player_df["game_timestamp"].max()
    days_since = (ref - last_game).total_seconds() / 86400  # type: ignore[union-attr]
    churned = days_since >= settings.churn_threshold_days

    return {"days_since_last_game": round(days_since, 2), "churned": churned}


def compute_network_proxy_features(
    df: pl.DataFrame,
    player_id: str,
    platform: str,
    raw_dir: Path | None = None,
) -> dict:
    """Compute real network proxy features from activity data.

    These are behavioral signals extracted from API data that correlate with
    network quality — avoiding the circular dependency of archetype → Sionna.

    All features default to 0.0 for platforms where they are not applicable.
    """
    player_df = df.filter((pl.col("player_id") == player_id) & (pl.col("platform") == platform))

    proxies: dict = {
        "abandon_rate": 0.0,
        "abnormal_duration_rate": 0.0,
        "short_session_rate": 0.0,
        "remake_rate": 0.0,
        "early_exit_rate": 0.0,
    }

    if player_df.is_empty():
        return proxies

    total = len(player_df)
    durations = player_df["duration_seconds"].to_list()

    if platform == "opendota":
        # abandon_rate: leaver_status != 0 from raw match JSON
        base = (raw_dir or RAW_DIR) / "opendota"
        matches_path = base / f"{player_id}_matches.json"
        if matches_path.exists():
            import json as _json
            matches = _json.loads(matches_path.read_text())
            abandoned = sum(1 for m in matches if m.get("leaver_status", 0) != 0)
            proxies["abandon_rate"] = round(abandoned / max(len(matches), 1), 4)
        # abnormal_duration_rate: Dota 2 games normally 20–60 min; < 300s or > 7200s is abnormal
        abnormal = sum(1 for d in durations if d < 300 or d > 7200)
        proxies["abnormal_duration_rate"] = round(abnormal / max(total, 1), 4)

    elif platform == "steam":
        # short_session_rate: sessions < 10 min (600 sec) as fraction of total
        short = sum(1 for d in durations if 0 < d < 600)
        proxies["short_session_rate"] = round(short / max(total, 1), 4)

    elif platform == "riot_lol":
        # remake_rate: games < 5 min (300 sec) — game ended abnormally early
        remakes = sum(1 for d in durations if d < 300)
        proxies["remake_rate"] = round(remakes / max(total, 1), 4)
        # early_exit_rate: games 5–20 min (300–1200 sec) — surrendered very early
        early_exits = sum(1 for d in durations if 300 <= d < 1200)
        proxies["early_exit_rate"] = round(early_exits / max(total, 1), 4)

    elif platform == "riot_valorant":
        # early_exit_rate: match length < 10 min (600 sec)
        early_exits = sum(1 for d in durations if d < 600)
        proxies["early_exit_rate"] = round(early_exits / max(total, 1), 4)

    return proxies


def build_features_for_player(
    df: pl.DataFrame,
    player_id: str,
    platform: str,
    reference_date: datetime | None = None,
    raw_dir: Path | None = None,
) -> dict:
    """Build complete feature set for a single player."""
    features = compute_time_window_features(df, player_id, platform, reference_date)
    features = compute_trend_features(features)
    features.update(compute_performance_features(df, player_id, platform, reference_date))

    if platform == "opendota":
        features.update(compute_social_features(player_id, raw_dir))
    else:
        features["unique_peers_30d"] = 0
        features["peer_games_30d"] = 0

    features["engagement_score"] = compute_engagement_score(features)
    features.update(compute_churn_label(df, player_id, platform, reference_date))
    features.update(compute_network_proxy_features(df, player_id, platform, raw_dir))

    return features


def _empty_features(player_id: str, platform: str) -> dict:
    """Return zeroed-out feature dict for player with no data."""
    return {
        "player_id": player_id,
        "platform": platform,
        "games_7d": 0,
        "games_14d": 0,
        "games_30d": 0,
        "playtime_7d_hours": 0.0,
        "playtime_14d_hours": 0.0,
        "playtime_30d_hours": 0.0,
        "avg_daily_sessions_7d": 0.0,
        "avg_daily_sessions_14d": 0.0,
        "avg_daily_sessions_30d": 0.0,
        "max_gap_days_30d": 30.0,
    }
