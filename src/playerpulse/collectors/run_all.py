"""Run active data collectors.

Active platforms: OpenDota (Dota 2), Steam, Riot (LoL + Valorant), RAWG.io (reviews)

Usage: python -m playerpulse.collectors.run_all
"""

from __future__ import annotations

import logging

from playerpulse.collectors.opendota import OpenDotaCollector
from playerpulse.collectors.rawg import RawgCollector
from playerpulse.collectors.riot import RiotLoLCollector, RiotValorantCollector
from playerpulse.collectors.steam import SteamCollector
from playerpulse.utils.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Dota 2 pro players — public profiles, diverse activity levels for churn signal variety.
# OpenDota IDs (32-bit) and matching Steam IDs (64-bit = OpenDota + 76561197960265728).
# Active pros = Elite/Core archetype. Retired/inactive = At-Risk/Churned archetype.
_OPENDOTA_SEED_PLAYERS = [
    # Active pros (Elite/Core — low churn risk)
    "105248644",   # Miracle-
    "86745912",    # Arteezy
    "94054712",    # Topson
    "111620041",   # SumaiL
    "311360822",   # ana
    "103735745",   # Jerax
    "86700461",    # w33
    # Veteran/moderately active (Core/Casual)
    "87278757",    # Puppey
    "70388657",    # Dendi
    "41231571",    # s4
    "86698277",    # Resolution
    "120269134",
    # Retired/inactive (At-Risk/Churned — critical for churn signal)
    "19672354",    # N0tail
    "25907144",    # Ceb
]

_STEAM_PLAYERS = [
    # Matching Steam IDs for the same Dota 2 players above
    "76561198065514372",   # Miracle-
    "76561198047011640",   # Arteezy
    "76561198054320440",   # Topson
    "76561198071885769",   # SumaiL
    "76561198271626550",   # ana
    "76561198056439818",   # MidOne
    "76561198046966189",   # w33
    "76561198047544485",   # Puppey
    "76561198030654385",   # Dendi
    "76561198001497299",   # s4
    "76561197979938082",   # N0tail
    "76561197985939093",   # Ceb
]

# LoL pros — public ranked accounts, diverse MMR and activity levels.
# Format: "GameName#TAG" — resolved to PUUID at collection time.
_LOL_PLAYERS = [
    # NA — active pros
    "Doublelift#NA1",
    "CoreJJ#NA1",
    "Bjergsen#NA1",
    "Faker#KR1",        # Global icon, very high activity
    "Chovy#KR1",
    "Ruler#KR1",
    # EU
    "Caps#EUW",
    "Jankos#EUW",
    # Retired / lower activity (churn signal)
    "Sneaky#NA1",
    "Yellowstar#EUW",
]

# Valorant pros — public ranked accounts.
_VALORANT_PLAYERS = [
    "TenZ#NA1",
    "Yay#NA1",
    "ShahZaM#NA1",
    "cNed#EUW",
    "Chronicle#EUW",
]

_RAWG_GAMES = ["dota-2", "counter-strike-2", "pubg-battlegrounds"]


def _expand_opendota_players(target: int = 200) -> list[str]:
    """Use the OpenDota /explorer SQL endpoint to fetch random ranked player IDs.

    Supplements seed pros with diverse real players (various skill levels,
    activity levels) to improve churn signal variety.

    Args:
        target: Number of random player IDs to fetch (max 1000 per query).

    Returns:
        List of account_id strings. May be fewer than target if query returns less.
    """
    import httpx

    log.info("Fetching %d random ranked players from OpenDota /explorer...", target)
    sql = (
        f"SELECT account_id FROM players "
        f"WHERE win + lose > 50 "
        f"ORDER BY RANDOM() "
        f"LIMIT {target}"
    )
    try:
        resp = httpx.get(
            "https://api.opendota.com/api/explorer",
            params={"sql": sql},
            timeout=30,
        )
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
        ids = [str(row["account_id"]) for row in rows if row.get("account_id")]
        log.info("Got %d random player IDs from OpenDota explorer", len(ids))
        return ids
    except Exception:
        log.exception("OpenDota explorer query failed — using seed players only")
        return []


def main() -> None:
    """Run all active collectors."""
    # -------------------------------------------------------------------
    # OpenDota — no auth needed
    # -------------------------------------------------------------------
    log.info("=== OpenDota Collector ===")

    # Expand beyond seed pros with random ranked players
    expanded_ids = _expand_opendota_players(target=200)
    # Merge: seed players first (guaranteed diverse activity), then random
    opendota_ids = _OPENDOTA_SEED_PLAYERS + [
        pid for pid in expanded_ids if pid not in _OPENDOTA_SEED_PLAYERS
    ]
    log.info("Collecting %d OpenDota players total", len(opendota_ids))

    with OpenDotaCollector() as collector:
        for account_id in opendota_ids:
            try:
                paths = collector.collect(account_id)
                log.info("Collected %d files for OpenDota/%s", len(paths), account_id)
            except Exception:
                log.exception("Failed to collect OpenDota/%s", account_id)

    # -------------------------------------------------------------------
    # Steam — requires STEAM_API_KEY
    # -------------------------------------------------------------------
    if settings.steam_api_key:
        log.info("=== Steam Collector ===")
        with SteamCollector() as collector:
            for steam_id in _STEAM_PLAYERS:
                try:
                    paths = collector.collect(steam_id)
                    log.info("Collected %d files for Steam/%s", len(paths), steam_id)
                except Exception:
                    log.exception("Failed to collect Steam/%s", steam_id)
    else:
        log.warning("Skipping Steam collector: STEAM_API_KEY not set")

    # -------------------------------------------------------------------
    # Riot LoL — requires RIOT_API_KEY
    # -------------------------------------------------------------------
    if settings.riot_api_key:
        log.info("=== Riot LoL Collector ===")
        with RiotLoLCollector(region="na1") as collector:
            for riot_id in _LOL_PLAYERS:
                try:
                    paths = collector.collect(riot_id)
                    log.info("Collected %d files for LoL/%s", len(paths), riot_id)
                except Exception:
                    log.exception("Failed to collect LoL/%s", riot_id)

        log.info("=== Riot Valorant Collector ===")
        with RiotValorantCollector(region="na1") as collector:
            for riot_id in _VALORANT_PLAYERS:
                try:
                    paths = collector.collect(riot_id)
                    log.info("Collected %d files for Valorant/%s", len(paths), riot_id)
                except Exception:
                    log.exception("Failed to collect Valorant/%s", riot_id)
    else:
        log.warning("Skipping Riot collectors: RIOT_API_KEY not set")

    # -------------------------------------------------------------------
    # RAWG — game metadata + reviews (NLP agent input only)
    # -------------------------------------------------------------------
    if settings.rawg_api_key:
        log.info("=== RAWG Metadata + Reviews Collector ===")
        with RawgCollector() as collector:
            for slug in _RAWG_GAMES:
                try:
                    paths = collector.collect(slug)
                    log.info("Collected %d files for RAWG/%s", len(paths), slug)
                except Exception:
                    log.exception("Failed to collect RAWG/%s", slug)
    else:
        log.warning("Skipping RAWG collector: RAWG_API_KEY not set")

    log.info("Collection complete.")


if __name__ == "__main__":
    main()
