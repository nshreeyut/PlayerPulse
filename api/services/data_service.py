"""
Data Service
=============
Handles loading and querying the player features dataset, plus live player lookup.

The feature table lives at:
  data/03_features/player_features.parquet

get_player_live() does a fresh API collect + feature engineering for any player.
If you ever migrate from Parquet to PostgreSQL, you change load_features() only.
"""

import polars as pl
from functools import lru_cache

from api.config import settings


@lru_cache(maxsize=1)
def load_features() -> pl.DataFrame:
    """Load the player features parquet file into memory (cached after first load)."""
    if not settings.features_path.exists():
        raise FileNotFoundError(
            f"Feature file not found at {settings.features_path}.\n"
            "Run `make train` to generate it."
        )
    return pl.read_parquet(settings.features_path)


def get_player(player_id: str, platform: str) -> dict | None:
    """Look up a single player's features by ID and platform. Returns None if not found."""
    df = load_features()
    filtered = df.filter(
        (pl.col("player_id") == player_id) & (pl.col("platform") == platform)
    )
    if filtered.height == 0:
        return None
    return filtered.to_dicts()[0]


def list_players(platform: str | None = None, limit: int = 100) -> list[dict]:
    """Return a list of players, optionally filtered by platform."""
    df = load_features()
    if platform:
        df = df.filter(pl.col("platform") == platform)
    cols = [c for c in ["player_id", "platform", "engagement_score", "churned", "days_since_last_game"] if c in df.columns]
    return df.select(cols).head(limit).to_dicts()


def get_dataset_summary() -> dict:
    """Return high-level statistics about the dataset."""
    df = load_features()
    total = df.height
    churned_count = int(df["churned"].sum()) if "churned" in df.columns else 0
    return {
        "total_players": total,
        "churned_count": churned_count,
        "churn_rate": round(churned_count / max(total, 1), 3),
        "platforms": df["platform"].unique().to_list() if "platform" in df.columns else [],
        "avg_engagement_score": round(float(df["engagement_score"].mean()), 1) if "engagement_score" in df.columns else 0.0,
        "avg_days_since_last_game": round(float(df["days_since_last_game"].mean()), 1) if "days_since_last_game" in df.columns else 0.0,
    }


_PLATFORM_ENCODING = {"opendota": 0, "steam": 1, "riot_lol": 2, "riot_valorant": 3}

# Archetype-inferred avg_sinr_db and peak_hour_latency_ms defaults
# Used when no live ping is available (Step 2 grounds these with real ping)
_ARCHETYPE_NETWORK = {
    "elite":   {"avg_sinr_db": 18.0, "peak_hour_latency_ms": 30.0},
    "core":    {"avg_sinr_db": 15.0, "peak_hour_latency_ms": 40.0},
    "casual":  {"avg_sinr_db": 14.0, "peak_hour_latency_ms": 50.0},
    "at_risk": {"avg_sinr_db": 7.0,  "peak_hour_latency_ms": 75.0},
    "churned": {"avg_sinr_db": 2.0,  "peak_hour_latency_ms": 120.0},
}


def _infer_archetype_from_features(features: dict) -> str:
    """Map behavioral features to a network archetype for Sionna scenario selection."""
    if features.get("churned", False) or features.get("days_since_last_game", 0) >= 14:
        return "churned"
    days_since = features.get("days_since_last_game", 0)
    if days_since >= 7:
        return "at_risk"
    engagement = features.get("engagement_score", 0)
    if engagement >= 70:
        return "elite"
    if engagement >= 40:
        return "core"
    return "casual"


def _get_collector(platform: str):
    """Instantiate the correct collector for the given platform."""
    if platform == "opendota":
        from playerpulse.collectors.opendota import OpenDotaCollector
        return OpenDotaCollector()
    if platform == "steam":
        from playerpulse.collectors.steam import SteamCollector
        return SteamCollector()
    if platform == "riot_lol":
        from playerpulse.collectors.riot import RiotLoLCollector
        return RiotLoLCollector()
    if platform == "riot_valorant":
        from playerpulse.collectors.riot import RiotValorantCollector
        return RiotValorantCollector()
    raise ValueError(f"Unknown platform: {platform}")


def get_player_live(player_id: str, platform: str) -> dict:
    """
    Live player lookup: collect → standardize → engineer features → return feature dict.

    Steps:
      1. Collect raw data from the game API (saves JSON to data/01_raw/{platform}/)
      2. Standardize raw JSON → list[PlayerActivity]
      3. Build behavioral + proxy features via engineer.py
      4. Add avg_sinr_db + peak_hour_latency_ms (archetype-inferred defaults)
      5. Add platform_encoded integer
      6. Return complete 27-feature dict ready for predict_churn()
    """
    import polars as pl
    from playerpulse.features.standardize import (
        standardize_opendota,
        standardize_steam,
        standardize_riot_lol,
        standardize_riot_valorant,
    )
    from playerpulse.features.engineer import build_features_for_player

    # 1. Collect
    with _get_collector(platform) as collector:
        collector.collect(player_id)

    # 2. Standardize
    if platform == "opendota":
        activities = standardize_opendota(player_id)
    elif platform == "steam":
        activities = standardize_steam(player_id)
    elif platform == "riot_lol":
        activities = standardize_riot_lol(player_id)
    elif platform == "riot_valorant":
        activities = standardize_riot_valorant(player_id)
    else:
        raise ValueError(f"Unknown platform: {platform}")

    if not activities:
        raise ValueError(f"No activity data found for player {player_id} on {platform}")

    # 3. Build features
    records = [a.model_dump() for a in activities]
    df = pl.DataFrame(records)
    features = build_features_for_player(df, player_id, platform)

    # 4. Add Sionna-grounded network features (archetype-inferred defaults)
    archetype = _infer_archetype_from_features(features)
    network_defaults = _ARCHETYPE_NETWORK[archetype]
    features["avg_sinr_db"] = network_defaults["avg_sinr_db"]
    features["peak_hour_latency_ms"] = network_defaults["peak_hour_latency_ms"]

    # 5. Add platform encoding
    features["platform_encoded"] = _PLATFORM_ENCODING.get(platform, 0)

    return features
