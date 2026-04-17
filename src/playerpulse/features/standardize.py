"""Standardize raw API data into unified PlayerActivity records.

Active platforms: OpenDota, Steam
RAWG is review-only — its output feeds the NLP agent, not this module.

Each standardize_*() function reads the raw JSON saved by its collector
and returns a list of PlayerActivity records in the shared schema.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from playerpulse.features.schema import PlayerActivity
from playerpulse.utils.config import RAW_DIR


def _load_json(path: Path) -> list | dict:
    return json.loads(path.read_text())


def standardize_opendota(account_id: str, raw_dir: Path | None = None) -> list[PlayerActivity]:
    """Convert OpenDota raw match data to PlayerActivity records."""
    base = (raw_dir or RAW_DIR) / "opendota"
    matches_path = base / f"{account_id}_matches.json"
    if not matches_path.exists():
        return []

    matches = _load_json(matches_path)
    activities: list[PlayerActivity] = []

    for match in matches:
        start_time = match.get("start_time", 0)
        game_dt = (
            datetime.fromtimestamp(start_time, tz=UTC) if start_time else datetime.now(tz=UTC)
        )
        duration = match.get("duration", 0)

        player_slot = match.get("player_slot", 0)
        radiant_win = match.get("radiant_win", False)
        is_radiant = player_slot < 128
        won = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)

        activities.append(
            PlayerActivity(
                player_id=account_id,
                platform="opendota",
                game_timestamp=game_dt,
                duration_seconds=duration,
                result="win" if won else "loss",
                rating=None,
                game_mode=str(match.get("game_mode", "unknown")),
            )
        )

    return activities


def standardize_steam(steam_id: str, raw_dir: Path | None = None) -> list[PlayerActivity]:
    """Convert Steam raw data to PlayerActivity records.

    Reads: {steam_id}_recently_played.json and {steam_id}_summary.json
    Produces one activity record per recently played game (proxy for session).
    """
    base = (raw_dir or RAW_DIR) / "steam"
    recently_played_path = base / f"{steam_id}_recently_played.json"
    summary_path = base / f"{steam_id}_summary.json"

    if not recently_played_path.exists():
        return []

    recently_played = _load_json(recently_played_path)
    summary = _load_json(summary_path) if summary_path.exists() else {}

    last_logoff = summary.get("lastlogoff", 0)
    last_seen = datetime.fromtimestamp(last_logoff, tz=UTC) if last_logoff else datetime.now(tz=UTC)

    activities: list[PlayerActivity] = []

    games = recently_played.get("response", {}).get("games", [])
    for game in games:
        playtime_2weeks = game.get("playtime_2weeks", 0)  # minutes
        playtime_forever = game.get("playtime_forever", 0)  # minutes

        # Use playtime_2weeks as a session duration proxy
        # Use last_seen as timestamp (most recent signal we have)
        activities.append(
            PlayerActivity(
                player_id=steam_id,
                platform="steam",
                game_timestamp=last_seen,
                duration_seconds=playtime_2weeks * 60,
                result="unknown",  # Steam doesn't have win/loss
                rating=None,
                game_mode=game.get("name", "unknown"),
            )
        )

    return activities


def standardize_riot_lol(puuid: str, raw_dir: Path | None = None) -> list[PlayerActivity]:
    """Convert Riot LoL raw match data to PlayerActivity records.

    Args:
        puuid: Player PUUID (used as file key and player_id)
    """
    base = (raw_dir or RAW_DIR) / "riot_lol"
    matches_path = base / f"{puuid}_matches.json"
    if not matches_path.exists():
        return []

    matches = _load_json(matches_path)
    activities: list[PlayerActivity] = []

    for match in matches:
        start_ms = match.get("gameStartTimestamp", 0)
        game_dt = (
            datetime.fromtimestamp(start_ms / 1000, tz=UTC) if start_ms else datetime.now(tz=UTC)
        )
        duration = match.get("gameDuration", 0)
        won = match.get("win", False)

        activities.append(
            PlayerActivity(
                player_id=puuid,
                platform="riot_lol",
                game_timestamp=game_dt,
                duration_seconds=duration,
                result="win" if won else "loss",
                rating=None,
                game_mode=str(match.get("gameMode", "unknown")),
            )
        )

    return activities


def standardize_riot_valorant(puuid: str, raw_dir: Path | None = None) -> list[PlayerActivity]:
    """Convert Riot Valorant raw match data to PlayerActivity records.

    Args:
        puuid: Player PUUID (used as file key and player_id)
    """
    base = (raw_dir or RAW_DIR) / "riot_valorant"
    matches_path = base / f"{puuid}_matches.json"
    if not matches_path.exists():
        return []

    matches = _load_json(matches_path)
    activities: list[PlayerActivity] = []

    for match in matches:
        start_ms = match.get("gameStartMillis", 0)
        game_dt = (
            datetime.fromtimestamp(start_ms / 1000, tz=UTC) if start_ms else datetime.now(tz=UTC)
        )
        duration_ms = match.get("gameLengthMillis", 0)
        won = match.get("win", False)

        activities.append(
            PlayerActivity(
                player_id=puuid,
                platform="riot_valorant",
                game_timestamp=game_dt,
                duration_seconds=duration_ms // 1000,
                result="win" if won else "loss",
                rating=None,
                game_mode=str(match.get("queueId", "unknown")),
            )
        )

    return activities


def load_all_activities(raw_dir: Path | None = None) -> pl.DataFrame:
    """Load and standardize all raw data into a single Polars DataFrame."""
    base = raw_dir or RAW_DIR
    all_activities: list[PlayerActivity] = []

    # OpenDota
    dota_dir = base / "opendota"
    if dota_dir.exists():
        for f in dota_dir.glob("*_matches.json"):
            account_id = f.stem.replace("_matches", "")
            all_activities.extend(standardize_opendota(account_id, raw_dir))

    # Steam
    steam_dir = base / "steam"
    if steam_dir.exists():
        for f in steam_dir.glob("*_recently_played.json"):
            steam_id = f.stem.replace("_recently_played", "")
            all_activities.extend(standardize_steam(steam_id, raw_dir))

    # Riot LoL
    riot_lol_dir = base / "riot_lol"
    if riot_lol_dir.exists():
        for f in riot_lol_dir.glob("*_matches.json"):
            puuid = f.stem.replace("_matches", "")
            all_activities.extend(standardize_riot_lol(puuid, raw_dir))

    # Riot Valorant
    riot_val_dir = base / "riot_valorant"
    if riot_val_dir.exists():
        for f in riot_val_dir.glob("*_matches.json"):
            puuid = f.stem.replace("_matches", "")
            all_activities.extend(standardize_riot_valorant(puuid, raw_dir))

    if not all_activities:
        return pl.DataFrame(
            schema={
                "player_id": pl.Utf8,
                "platform": pl.Utf8,
                "game_timestamp": pl.Datetime("us", "UTC"),
                "duration_seconds": pl.Int64,
                "result": pl.Utf8,
                "rating": pl.Int64,
                "game_mode": pl.Utf8,
            }
        )

    records = [a.model_dump() for a in all_activities]
    return pl.DataFrame(records).sort("game_timestamp")
