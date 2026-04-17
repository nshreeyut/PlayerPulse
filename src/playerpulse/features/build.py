"""Build features from raw data and save to disk.

Usage: python -m playerpulse.features.build

Pipeline:
  1. Standardize raw API data → activity records
  2. Engineer 19 behavioral features per player
  3. Simulate network telemetry (Sionna / statistical fallback) → 6 network features
     Network scenario is inferred from each player's behavioral profile so the
     simulated telemetry is grounded in their real play patterns.
  4. Join behavioral + network features → save player_features.parquet
"""

from __future__ import annotations

import logging

import polars as pl

from playerpulse.features.engineer import build_features_for_player
from playerpulse.features.standardize import load_all_activities
from playerpulse.utils.config import FEATURES_DIR, RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _infer_archetype(row: dict) -> str:
    """Infer network scenario archetype from behavioral features.

    Maps real player behavior to a Sionna scenario so simulated network
    telemetry reflects their actual play patterns:
      - churned / inactive → poor_coverage (cell-edge conditions)
      - at-risk            → at_risk (mixed suburban/poor)
      - high engagement    → elite/core (urban, good coverage)
      - moderate           → casual (suburban)
    """
    if row.get("churned", False) or row.get("days_since_last_game", 0) >= 14:
        return "churned"
    engagement = row.get("engagement_score", 0)
    days_since = row.get("days_since_last_game", 0)
    if days_since >= 7:
        return "at_risk"
    if engagement >= 70:
        return "elite"
    if engagement >= 40:
        return "core"
    return "casual"


def _add_network_features(features_df: pl.DataFrame) -> pl.DataFrame:
    """Generate Sionna network telemetry and join avg_sinr_db + peak_hour_latency_ms.

    Only these two Sionna features are retained; the four synthetic-only columns
    (p95_latency_ms, packet_loss_rate, jitter_ms, disconnect_count) are replaced
    by real API proxy features computed in engineer.py.
    """
    from api.services.network_sim_service import generate_synthetic_telemetry

    rows = features_df.to_dicts()
    player_ids = [r["player_id"] for r in rows]
    archetypes = [_infer_archetype(r) for r in rows]

    log.info("Simulating network telemetry for %d players...", len(player_ids))
    network_df = generate_synthetic_telemetry(
        n_players=len(player_ids),
        player_ids=player_ids,
        archetype_labels=archetypes,
    )

    # Only keep the two Sionna features that remain in FEATURE_COLS
    network_slim = network_df.select(["player_id", "avg_sinr_db", "peak_hour_latency_ms"])

    # Join on player_id — left join keeps all behavioral rows
    return features_df.join(network_slim, on="player_id", how="left")


def build_all_features() -> pl.DataFrame:
    """Load raw data, standardize, engineer behavioral + network features, save parquet."""
    log.info("Loading and standardizing raw activity data...")
    activities = load_all_activities()

    if activities.is_empty():
        log.warning("No activity data found. Run collectors first.")
        return pl.DataFrame()

    log.info("Loaded %d activity records", len(activities))

    # Get unique player-platform combos
    player_platforms = activities.select("player_id", "platform").unique().to_dicts()
    log.info("Building behavioral features for %d players...", len(player_platforms))

    all_features: list[dict] = []
    for pp in player_platforms:
        features = build_features_for_player(
            activities,
            pp["player_id"],
            pp["platform"],
            raw_dir=RAW_DIR,
        )
        all_features.append(features)

    features_df = pl.DataFrame(all_features)

    # Encode platform as integer feature (game-aware model)
    _PLATFORM_ENCODING = ["opendota", "steam", "riot_lol", "riot_valorant"]
    features_df = features_df.with_columns(
        pl.col("platform")
        .replace(_PLATFORM_ENCODING, list(range(len(_PLATFORM_ENCODING))))
        .cast(pl.Int32)
        .alias("platform_encoded")
    )

    # Add network features via Sionna simulation
    features_df = _add_network_features(features_df)

    # Save
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FEATURES_DIR / "player_features.parquet"
    features_df.write_parquet(output_path)
    log.info(
        "Saved features to %s (%d rows, %d cols)",
        output_path,
        len(features_df),
        len(features_df.columns),
    )

    return features_df


if __name__ == "__main__":
    build_all_features()
