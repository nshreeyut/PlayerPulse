"""Generate synthetic player feature data for model development.

Players are modelled as five archetypes that mirror what a real game studio
would see in production data:

  Elite      (~14 %) — daily power users, high playtime, strong social graph
  Core       (~26 %) — consistent regulars, 4-5 sessions/week
  Casual     (~22 %) — weekend warriors, moderate engagement, low churn risk
  At-Risk    (~22 %) — activity sliding over the past 30 days, medium churn risk
  Churned    (~16 %) — last session was weeks ago, high churn risk

This produces a realistic three-way risk distribution (High / Medium / Low)
rather than a binary active/churned split.
"""

from __future__ import annotations

import numpy as np
import polars as pl


# ---------------------------------------------------------------------------
# Archetype definitions
# Each entry: (label, weight, param_dict)
# ---------------------------------------------------------------------------

def _elite(rng: np.random.Generator) -> dict:
    games_30d = int(rng.poisson(55))
    games_14d = min(int(rng.poisson(28)), games_30d)
    games_7d  = min(int(rng.poisson(14)), games_14d)
    pt30 = max(0, rng.normal(60, 12))
    pt14 = max(0, rng.normal(32, 7))
    pt7  = max(0, rng.normal(16, 4))
    return dict(
        games_30d=games_30d, games_14d=games_14d, games_7d=games_7d,
        playtime_30d=pt30, playtime_14d=pt14, playtime_7d=pt7,
        avg_sessions_30d=max(0, rng.normal(1.7, 0.2)),
        avg_sessions_14d=max(0, rng.normal(1.8, 0.15)),
        avg_sessions_7d =max(0, rng.normal(1.9, 0.15)),
        max_gap=rng.uniform(0.2, 2.5),
        win_rate_7d =max(0, min(1, rng.normal(0.58, 0.07))),
        win_rate_30d=max(0, min(1, rng.normal(0.56, 0.06))),
        rating_change=int(rng.normal(60, 35)),
        peers=int(max(0, rng.poisson(18))),
        peer_games=int(max(0, rng.poisson(30))),
        days_since=rng.uniform(0, 1.5),
        engagement=max(60, min(100, rng.normal(82, 8))),
        churned=False,
        # Network proxies: elite players rarely abandon or exit early
        abandon_rate=round(float(np.clip(rng.normal(0.01, 0.005), 0, 1)), 4),
        abnormal_duration_rate=round(float(np.clip(rng.normal(0.02, 0.01), 0, 1)), 4),
        short_session_rate=round(float(np.clip(rng.normal(0.03, 0.015), 0, 1)), 4),
        remake_rate=round(float(np.clip(rng.normal(0.01, 0.005), 0, 1)), 4),
        early_exit_rate=round(float(np.clip(rng.normal(0.02, 0.01), 0, 1)), 4),
        # Sionna: urban, good coverage — elite players have low-latency setups
        avg_sinr_db=round(max(0, rng.normal(18, 4)), 2),
        peak_hour_latency_ms=round(max(8, rng.normal(30, 8)), 2),
        archetype="elite",
    )


def _core(rng: np.random.Generator) -> dict:
    games_30d = int(rng.poisson(28))
    games_14d = min(int(rng.poisson(14)), games_30d)
    games_7d  = min(int(rng.poisson(7)), games_14d)
    pt30 = max(0, rng.normal(28, 8))
    pt14 = max(0, rng.normal(14, 5))
    pt7  = max(0, rng.normal(7, 3))
    return dict(
        games_30d=games_30d, games_14d=games_14d, games_7d=games_7d,
        playtime_30d=pt30, playtime_14d=pt14, playtime_7d=pt7,
        avg_sessions_30d=max(0, rng.normal(0.85, 0.18)),
        avg_sessions_14d=max(0, rng.normal(0.88, 0.16)),
        avg_sessions_7d =max(0, rng.normal(0.90, 0.15)),
        max_gap=rng.uniform(1, 5),
        win_rate_7d =max(0, min(1, rng.normal(0.52, 0.09))),
        win_rate_30d=max(0, min(1, rng.normal(0.51, 0.07))),
        rating_change=int(rng.normal(15, 30)),
        peers=int(max(0, rng.poisson(10))),
        peer_games=int(max(0, rng.poisson(18))),
        days_since=rng.uniform(0, 4),
        engagement=max(0, min(100, rng.normal(62, 10))),
        churned=False,
        # Network proxies: core players occasionally leave early
        abandon_rate=round(float(np.clip(rng.normal(0.02, 0.01), 0, 1)), 4),
        abnormal_duration_rate=round(float(np.clip(rng.normal(0.04, 0.02), 0, 1)), 4),
        short_session_rate=round(float(np.clip(rng.normal(0.07, 0.03), 0, 1)), 4),
        remake_rate=round(float(np.clip(rng.normal(0.02, 0.01), 0, 1)), 4),
        early_exit_rate=round(float(np.clip(rng.normal(0.05, 0.025), 0, 1)), 4),
        # Sionna: urban/suburban mix — decent connection
        avg_sinr_db=round(max(0, rng.normal(15, 5)), 2),
        peak_hour_latency_ms=round(max(12, rng.normal(40, 12)), 2),
        archetype="core",
    )


def _casual(rng: np.random.Generator) -> dict:
    games_30d = int(rng.poisson(10))
    games_14d = min(int(rng.poisson(5)), games_30d)
    games_7d  = min(int(rng.poisson(2)), games_14d)
    pt30 = max(0, rng.normal(10, 5))
    pt14 = max(0, rng.normal(5, 3))
    pt7  = max(0, rng.normal(2.5, 1.5))
    return dict(
        games_30d=games_30d, games_14d=games_14d, games_7d=games_7d,
        playtime_30d=pt30, playtime_14d=pt14, playtime_7d=pt7,
        avg_sessions_30d=max(0, rng.normal(0.32, 0.12)),
        avg_sessions_14d=max(0, rng.normal(0.30, 0.12)),
        avg_sessions_7d =max(0, rng.normal(0.28, 0.12)),
        max_gap=rng.uniform(3, 9),
        win_rate_7d =max(0, min(1, rng.normal(0.48, 0.12))),
        win_rate_30d=max(0, min(1, rng.normal(0.47, 0.10))),
        rating_change=int(rng.normal(0, 20)),
        peers=int(max(0, rng.poisson(4))),
        peer_games=int(max(0, rng.poisson(5))),
        days_since=rng.uniform(2, 9),
        engagement=max(0, min(100, rng.normal(38, 12))),
        churned=False,
        # Network proxies: casual players more likely to have short sessions
        abandon_rate=round(float(np.clip(rng.normal(0.04, 0.02), 0, 1)), 4),
        abnormal_duration_rate=round(float(np.clip(rng.normal(0.06, 0.03), 0, 1)), 4),
        short_session_rate=round(float(np.clip(rng.normal(0.12, 0.06), 0, 1)), 4),
        remake_rate=round(float(np.clip(rng.normal(0.03, 0.015), 0, 1)), 4),
        early_exit_rate=round(float(np.clip(rng.normal(0.08, 0.04), 0, 1)), 4),
        # Sionna: suburban — moderate coverage, occasional issues
        avg_sinr_db=round(max(0, rng.normal(14, 6)), 2),
        peak_hour_latency_ms=round(max(15, rng.normal(50, 16)), 2),
        archetype="casual",
    )


def _at_risk(rng: np.random.Generator) -> dict:
    """Player who was active but activity is sliding — medium churn risk."""
    games_30d = int(rng.poisson(8))
    games_14d = min(int(rng.poisson(3)), games_30d)
    games_7d  = min(int(rng.poisson(1)), games_14d)
    pt30 = max(0, rng.normal(7, 4))
    pt14 = max(0, rng.normal(2, 2))
    pt7  = max(0, rng.normal(0.5, 0.8))
    return dict(
        games_30d=games_30d, games_14d=games_14d, games_7d=games_7d,
        playtime_30d=pt30, playtime_14d=pt14, playtime_7d=pt7,
        avg_sessions_30d=max(0, rng.normal(0.22, 0.10)),
        avg_sessions_14d=max(0, rng.normal(0.14, 0.08)),
        avg_sessions_7d =max(0, rng.normal(0.08, 0.06)),
        max_gap=rng.uniform(8, 18),
        win_rate_7d =max(0, min(1, rng.normal(0.40, 0.14))),
        win_rate_30d=max(0, min(1, rng.normal(0.44, 0.11))),
        rating_change=int(rng.normal(-25, 30)),
        peers=int(max(0, rng.poisson(3))),
        peer_games=int(max(0, rng.poisson(4))),
        days_since=rng.uniform(9, 20),
        engagement=max(0, min(100, rng.normal(24, 10))),
        churned=False,  # model will score these as medium-high risk
        # Network proxies: at-risk players show frustration signals
        abandon_rate=round(float(np.clip(rng.normal(0.08, 0.04), 0, 1)), 4),
        abnormal_duration_rate=round(float(np.clip(rng.normal(0.10, 0.05), 0, 1)), 4),
        short_session_rate=round(float(np.clip(rng.normal(0.20, 0.08), 0, 1)), 4),
        remake_rate=round(float(np.clip(rng.normal(0.05, 0.025), 0, 1)), 4),
        early_exit_rate=round(float(np.clip(rng.normal(0.14, 0.07), 0, 1)), 4),
        # Sionna: poor coverage mix — frustrating network experience
        avg_sinr_db=round(max(-5, rng.normal(7, 6)), 2),
        peak_hour_latency_ms=round(max(25, rng.normal(75, 25)), 2),
        archetype="at_risk",
    )


def _churned(rng: np.random.Generator) -> dict:
    games_30d = int(rng.poisson(2))
    games_14d = min(int(rng.poisson(0.5)), games_30d)
    games_7d  = 0
    pt30 = max(0, rng.normal(1.5, 1.2))
    pt14 = max(0, rng.normal(0.3, 0.4))
    pt7  = 0.0
    return dict(
        games_30d=games_30d, games_14d=games_14d, games_7d=games_7d,
        playtime_30d=pt30, playtime_14d=pt14, playtime_7d=pt7,
        avg_sessions_30d=max(0, rng.normal(0.06, 0.05)),
        avg_sessions_14d=max(0, rng.normal(0.03, 0.03)),
        avg_sessions_7d =0.0,
        max_gap=rng.uniform(20, 45),
        win_rate_7d =0.0,
        win_rate_30d=max(0, min(1, rng.normal(0.38, 0.14))),
        rating_change=int(rng.normal(-70, 35)),
        peers=int(max(0, rng.poisson(1))),
        peer_games=int(max(0, rng.poisson(1))),
        days_since=rng.uniform(21, 90),
        engagement=max(0, rng.normal(8, 6)),
        churned=True,
        # Network proxies: churned players had highest frustration signals
        abandon_rate=round(float(np.clip(rng.normal(0.14, 0.07), 0, 1)), 4),
        abnormal_duration_rate=round(float(np.clip(rng.normal(0.16, 0.08), 0, 1)), 4),
        short_session_rate=round(float(np.clip(rng.normal(0.32, 0.12), 0, 1)), 4),
        remake_rate=round(float(np.clip(rng.normal(0.08, 0.04), 0, 1)), 4),
        early_exit_rate=round(float(np.clip(rng.normal(0.22, 0.10), 0, 1)), 4),
        # Sionna: cell-edge / poor coverage — high latency
        avg_sinr_db=round(max(-10, rng.normal(2, 5)), 2),
        peak_hour_latency_ms=round(max(40, rng.normal(120, 40)), 2),
        archetype="churned",
    )


_ARCHETYPES = [
    (_elite,   0.14),
    (_core,    0.26),
    (_casual,  0.22),
    (_at_risk, 0.22),
    (_churned, 0.16),
]


def generate_synthetic_data(n_players: int = 2000, seed: int = 42) -> pl.DataFrame:
    """Generate realistic synthetic player features with churn labels."""
    rng = np.random.default_rng(seed)

    # Sample archetype for each player according to weights
    weights = [w for _, w in _ARCHETYPES]
    fns     = [f for f, _ in _ARCHETYPES]
    choices  = rng.choice(len(fns), size=n_players, p=weights)

    _platforms = ["opendota", "steam", "riot_lol", "riot_valorant"]
    _platform_weights = [0.35, 0.30, 0.25, 0.10]  # Dota 2 + Steam + LoL + Valorant mix
    _platform_encoding = {p: i for i, p in enumerate(_platforms)}
    records: list[dict] = []

    for i, archetype_idx in enumerate(choices):
        p = fns[archetype_idx](rng)
        platform = str(rng.choice(_platforms, p=_platform_weights))

        games_trend   = p["games_7d"] / max(p["games_14d"], 1)
        playtime_trend = p["playtime_7d"] / max(p["playtime_14d"], 0.01)

        records.append({
            "player_id":               f"Player_{i + 1}",
            "platform":                platform,
            "games_7d":                p["games_7d"],
            "games_14d":               p["games_14d"],
            "games_30d":               p["games_30d"],
            "playtime_7d_hours":       round(p["playtime_7d"], 2),
            "playtime_14d_hours":      round(p["playtime_14d"], 2),
            "playtime_30d_hours":      round(p["playtime_30d"], 2),
            "avg_daily_sessions_7d":   round(p["avg_sessions_7d"], 3),
            "avg_daily_sessions_14d":  round(p["avg_sessions_14d"], 3),
            "avg_daily_sessions_30d":  round(p["avg_sessions_30d"], 3),
            "max_gap_days_30d":        round(p["max_gap"], 2),
            "games_trend_7d_vs_14d":   round(games_trend, 3),
            "playtime_trend_7d_vs_14d": round(playtime_trend, 3),
            "win_rate_7d":             round(p["win_rate_7d"], 3),
            "win_rate_30d":            round(p["win_rate_30d"], 3),
            "rating_current":          int(rng.normal(1500, 300)),
            "rating_change_30d":       p["rating_change"],
            "unique_peers_30d":        p["peers"],
            "peer_games_30d":          p["peer_games"],
            "engagement_score":        round(p["engagement"], 2),
            "days_since_last_game":    round(p["days_since"], 2),
            # Real network proxy features
            "abandon_rate":            p["abandon_rate"],
            "abnormal_duration_rate":  p["abnormal_duration_rate"],
            "short_session_rate":      p["short_session_rate"],
            "remake_rate":             p["remake_rate"],
            "early_exit_rate":         p["early_exit_rate"],
            # Sionna-grounded network features
            "avg_sinr_db":             p["avg_sinr_db"],
            "peak_hour_latency_ms":    p["peak_hour_latency_ms"],
            # Platform encoding: 0=opendota, 1=steam, 2=riot_lol, 3=riot_valorant
            "platform_encoded":        _platform_encoding[platform],
            "churned":                 p["churned"],
        })

    return pl.DataFrame(records)
