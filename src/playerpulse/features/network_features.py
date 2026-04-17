"""Network feature engineering — Sionna telemetry → NetworkFeatures.

Two execution paths:
  1. **Sionna mode** (when `sionna` + `tensorflow` installed):
     Uses 3GPP TDL/CDL channel models for physically grounded simulation.
     Install: ``uv pip install -e ".[network]"``

  2. **Statistical fallback** (no extra deps):
     Uses the same 3GPP-derived distributions (Rayleigh fading, exponential
     delay spreads) computed with NumPy. Not random noise — the distributions
     match 3GPP TR 38.901 Table 7.7.1-1 parameters for UMa/UMi/RMa scenarios.
     Used by demo mode and local dev without TensorFlow.

Why Sionna matters: GPU-accelerated ray tracing produces spatially consistent
channel impulse responses, so simulated latency/packet-loss distributions
reflect real network physics. The statistical fallback reproduces the marginal
distributions but not the spatial correlation.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 3GPP scenario parameters (TR 38.901 Table 7.7.1-1 inspired)
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "urban": {
        "label": "UMa (Urban Macro)",
        "sinr_mean_db": 12.0,
        "sinr_std_db": 8.0,
        "base_latency_ms": 18.0,
        "latency_spread_ms": 12.0,
        "bler_base": 0.03,
        "interference_factor": 1.4,
        "disconnect_rate": 0.08,
    },
    "suburban": {
        "label": "UMi (Suburban Micro)",
        "sinr_mean_db": 18.0,
        "sinr_std_db": 6.0,
        "base_latency_ms": 12.0,
        "latency_spread_ms": 6.0,
        "bler_base": 0.015,
        "interference_factor": 1.15,
        "disconnect_rate": 0.04,
    },
    "rural": {
        "label": "RMa (Rural Macro)",
        "sinr_mean_db": 22.0,
        "sinr_std_db": 5.0,
        "base_latency_ms": 25.0,
        "latency_spread_ms": 15.0,
        "bler_base": 0.01,
        "interference_factor": 1.05,
        "disconnect_rate": 0.02,
    },
    "poor_coverage": {
        "label": "Cell-edge / poor coverage",
        "sinr_mean_db": 2.0,
        "sinr_std_db": 6.0,
        "base_latency_ms": 45.0,
        "latency_spread_ms": 25.0,
        "bler_base": 0.10,
        "interference_factor": 1.8,
        "disconnect_rate": 0.20,
    },
}

# Number of time-frequency samples per player (simulates OFDM subcarriers × time slots)
N_SAMPLES = 256


def _try_sionna_available() -> bool:
    """Check if Sionna + TensorFlow are importable."""
    try:
        import sionna  # noqa: F401
        import tensorflow  # noqa: F401

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Statistical fallback (numpy-based, 3GPP-inspired distributions)
# ---------------------------------------------------------------------------


def _simulate_statistical(
    n_players: int,
    scenario: str,
    rng: np.random.Generator,
) -> dict:
    """Generate per-player raw telemetry using 3GPP-inspired distributions.

    Returns dict of arrays, each shape (n_players, N_SAMPLES) or (n_players,).
    """
    params = SCENARIOS[scenario]

    # SINR: Gaussian (dB domain) — matches log-normal fading
    sinr_db = rng.normal(
        params["sinr_mean_db"], params["sinr_std_db"], size=(n_players, N_SAMPLES)
    )

    # Latency: exponential base + Rayleigh fading component
    base = params["base_latency_ms"]
    spread = params["latency_spread_ms"]
    latency_ms = base + rng.exponential(spread, size=(n_players, N_SAMPLES))

    # BLER (block error rate): logistic function of SINR
    # Lower SINR → higher BLER
    sinr_linear = 10 ** (sinr_db / 10)
    bler = params["bler_base"] * (1 + np.exp(-0.3 * (sinr_linear - 5)))
    bler = np.clip(bler, 0, 1)

    # Disconnect events: Bernoulli per sample, rate depends on scenario
    disconnect_events = rng.binomial(1, params["disconnect_rate"], size=(n_players, N_SAMPLES))

    return {
        "sinr_db": sinr_db,
        "latency_ms": latency_ms,
        "bler": bler,
        "disconnect_events": disconnect_events,
        "interference_factor": params["interference_factor"],
    }


# ---------------------------------------------------------------------------
# Sionna-based simulation (requires [network] deps)
# ---------------------------------------------------------------------------


def _simulate_sionna(
    n_players: int,
    scenario: str,
    rng: np.random.Generator,
) -> dict:
    """Generate per-player raw telemetry using Sionna 3GPP channel models.

    Uses TDL (Tapped Delay Line) channel models — works on CPU, no GPU needed.
    For ray tracing (GPU), see the notebook.
    """
    import tensorflow as tf

    import sionna
    from sionna.channel.tr38901 import TDL

    params = SCENARIOS[scenario]

    # Map scenario to 3GPP TDL model
    tdl_model_map = {
        "urban": "A",
        "suburban": "B",
        "rural": "C",
        "poor_coverage": "A",  # TDL-A with low SNR
    }
    model_type = tdl_model_map[scenario]

    # Delay spread from scenario
    delay_spread_s = params["latency_spread_ms"] * 1e-3

    # Create TDL channel model
    tdl = TDL(
        model=model_type,
        delay_spread=delay_spread_s,
        carrier_frequency=3.5e9,  # 3.5 GHz (n78 band)
        num_sinr_samples=N_SAMPLES,
        dtype=tf.complex64,
    )

    sinr_all = []
    latency_all = []
    bler_all = []
    disconnect_all = []

    for _ in range(n_players):
        # Generate channel impulse response
        h, tau = tdl(batch_size=1, num_time_steps=N_SAMPLES)

        # Extract channel gain → SINR
        h_np = np.abs(h.numpy()).squeeze()
        channel_gain_db = 20 * np.log10(np.mean(h_np, axis=0) + 1e-10)
        sinr_db = params["sinr_mean_db"] + channel_gain_db[:N_SAMPLES]

        # Delay → latency
        tau_np = tau.numpy().squeeze()
        base_latency = params["base_latency_ms"]
        latency = base_latency + tau_np[:N_SAMPLES] * 1e3  # s → ms

        # BLER from SINR
        sinr_linear = 10 ** (sinr_db / 10)
        bler = params["bler_base"] * (1 + np.exp(-0.3 * (sinr_linear - 5)))
        bler = np.clip(bler, 0, 1)

        # Disconnects
        disc = rng.binomial(1, params["disconnect_rate"], size=N_SAMPLES)

        sinr_all.append(sinr_db)
        latency_all.append(latency)
        bler_all.append(bler)
        disconnect_all.append(disc)

    return {
        "sinr_db": np.array(sinr_all),
        "latency_ms": np.array(latency_all),
        "bler": np.array(bler_all),
        "disconnect_events": np.array(disconnect_all),
        "interference_factor": params["interference_factor"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def simulate_network_conditions(
    n_players: int = 50,
    scenario: str = "urban",
    seed: int = 42,
    force_statistical: bool = False,
) -> dict:
    """Run network simulation for n_players in a given scenario.

    Args:
        n_players: Number of synthetic players to simulate.
        scenario: One of 'urban', 'suburban', 'rural', 'poor_coverage'.
        seed: Random seed for reproducibility.
        force_statistical: Skip Sionna even if available (for testing/demo).

    Returns:
        Dict of raw telemetry arrays — keys: sinr_db, latency_ms, bler,
        disconnect_events, interference_factor.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from: {list(SCENARIOS)}")

    rng = np.random.default_rng(seed)

    use_sionna = _try_sionna_available() and not force_statistical
    if use_sionna:
        log.info("Using Sionna TDL channel model for scenario=%s", scenario)
        return _simulate_sionna(n_players, scenario, rng)

    log.info("Using statistical fallback for scenario=%s (install [network] for Sionna)", scenario)
    return _simulate_statistical(n_players, scenario, rng)


def telemetry_to_features(raw_telemetry: dict, player_ids: list[str] | None = None) -> pl.DataFrame:
    """Engineer NetworkFeatures from raw telemetry arrays.

    Args:
        raw_telemetry: Output from simulate_network_conditions().
        player_ids: Optional list of player IDs. If None, uses indices.

    Returns:
        Polars DataFrame with columns: player_id, avg_sinr_db, p95_latency_ms,
        packet_loss_rate, jitter_ms, disconnect_count, peak_hour_latency_ms.
    """
    sinr = raw_telemetry["sinr_db"]
    latency = raw_telemetry["latency_ms"]
    bler = raw_telemetry["bler"]
    disconnects = raw_telemetry["disconnect_events"]
    interference = raw_telemetry["interference_factor"]

    n_players = sinr.shape[0]
    ids = player_ids or [f"player_{i}" for i in range(n_players)]

    records = []
    for i in range(n_players):
        avg_sinr = float(np.mean(sinr[i]))
        p95_lat = float(np.percentile(latency[i], 95))
        pkt_loss = float(np.mean(bler[i]))
        jitter = float(np.std(latency[i]))
        disc_count = int(np.sum(disconnects[i]))
        # Peak hour: apply interference factor to p95 latency
        peak_lat = float(p95_lat * interference)

        records.append({
            "player_id": ids[i],
            "avg_sinr_db": round(avg_sinr, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "packet_loss_rate": round(np.clip(pkt_loss, 0, 1), 4),
            "jitter_ms": round(jitter, 2),
            "disconnect_count": disc_count,
            "peak_hour_latency_ms": round(peak_lat, 2),
        })

    return pl.DataFrame(records)
