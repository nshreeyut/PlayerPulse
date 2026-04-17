"""Network simulation service — NVIDIA Sionna telemetry generation.

Generates physically grounded synthetic network telemetry using
NVIDIA Sionna (3GPP channel models) or statistical fallback.

Distributes players across network scenarios based on archetype:
  - Elite/Core  → urban (good coverage, some congestion)
  - Casual      → suburban (moderate coverage)
  - At-Risk     → mixed (suburban + poor_coverage)
  - Churned     → poor_coverage (cell-edge, high latency)

Output parquets saved to data/network_sim/
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from playerpulse.features.network_features import (
    simulate_network_conditions,
    telemetry_to_features,
)

log = logging.getLogger(__name__)

NETWORK_SIM_DIR = Path("data/network_sim")

# Archetype → scenario mapping
# Maps archetype labels to (scenario, weight) pairs for mixed assignment
ARCHETYPE_SCENARIOS: dict[str, list[tuple[str, float]]] = {
    "elite": [("urban", 0.8), ("suburban", 0.2)],
    "core": [("urban", 0.5), ("suburban", 0.5)],
    "casual": [("suburban", 0.6), ("rural", 0.3), ("poor_coverage", 0.1)],
    "at_risk": [("suburban", 0.3), ("rural", 0.3), ("poor_coverage", 0.4)],
    "churned": [("poor_coverage", 0.6), ("rural", 0.3), ("suburban", 0.1)],
}


def generate_synthetic_telemetry(
    n_players: int = 50,
    seed: int = 42,
    archetype_labels: list[str] | None = None,
    player_ids: list[str] | None = None,
    force_statistical: bool = False,
) -> pl.DataFrame:
    """Run Sionna simulation and return per-player network features.

    Args:
        n_players: Number of synthetic players to simulate.
        seed: Random seed for reproducibility.
        archetype_labels: Per-player archetype (elite/core/casual/at_risk/churned).
            If None, assigns uniform random archetypes.
        player_ids: Per-player IDs. If None, uses Player_1..Player_N.
        force_statistical: Skip Sionna even if installed.

    Returns:
        Polars DataFrame with columns: player_id, avg_sinr_db, p95_latency_ms,
        packet_loss_rate, jitter_ms, disconnect_count, peak_hour_latency_ms.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    ids = player_ids or [f"Player_{i + 1}" for i in range(n_players)]
    archetypes = archetype_labels or rng.choice(
        list(ARCHETYPE_SCENARIOS.keys()), size=n_players
    ).tolist()

    # Assign each player to a scenario based on their archetype
    player_scenarios: list[str] = []
    for arch in archetypes:
        mapping = ARCHETYPE_SCENARIOS.get(arch, [("suburban", 1.0)])
        scenarios = [s for s, _ in mapping]
        weights = [w for _, w in mapping]
        chosen = rng.choice(scenarios, p=weights)
        player_scenarios.append(chosen)

    # Group players by scenario for batch simulation
    scenario_groups: dict[str, list[int]] = {}
    for idx, scenario in enumerate(player_scenarios):
        scenario_groups.setdefault(scenario, []).append(idx)

    # Simulate each scenario group and merge
    all_records: list[dict] = [{}] * n_players
    for scenario, indices in scenario_groups.items():
        n = len(indices)
        group_ids = [ids[i] for i in indices]

        raw = simulate_network_conditions(
            n_players=n,
            scenario=scenario,
            seed=seed + hash(scenario) % 10000,
            force_statistical=force_statistical,
        )
        features_df = telemetry_to_features(raw, player_ids=group_ids)

        for row_idx, player_idx in enumerate(indices):
            all_records[player_idx] = features_df.row(row_idx, named=True)

    df = pl.DataFrame(all_records)

    # Save parquet
    NETWORK_SIM_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    out_path = NETWORK_SIM_DIR / f"telemetry_{ts}.parquet"
    df.write_parquet(out_path)
    log.info("Saved network telemetry to %s (%d players)", out_path, n_players)

    return df


def load_latest_telemetry() -> pl.DataFrame | None:
    """Load the most recently generated telemetry parquet, if it exists."""
    parquets = sorted(NETWORK_SIM_DIR.glob("telemetry_*.parquet"))
    if not parquets:
        return None
    return pl.read_parquet(parquets[-1])
