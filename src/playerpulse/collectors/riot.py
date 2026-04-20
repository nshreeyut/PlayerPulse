"""Riot Games API collector — League of Legends and Valorant.

API docs: https://developer.riotgames.com/apis
Requires a Riot API key from developer.riotgames.com (development key = 24h validity).
One key covers LoL, Valorant, and TFT.

Development key rate limits: 20 req/second, 100 req/2 minutes.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from playerpulse.collectors.base import BaseCollector
from playerpulse.utils.config import settings

log = logging.getLogger(__name__)

# Regional routing hosts (per-player data)
# Cluster routing hosts (match history, cross-region endpoints)
_REGION_TO_CLUSTER = {
    "na1": "americas",
    "la1": "americas",
    "la2": "americas",
    "br1": "americas",
    "euw1": "europe",
    "eune1": "europe",
    "ru": "europe",
    "tr1": "europe",
    "kr": "asia",
    "jp1": "asia",
    "oc1": "sea",
    "ph2": "sea",
    "sg2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}


class RiotBaseCollector(BaseCollector):
    """Base collector for Riot Games APIs. Sets auth header and routing."""

    def __init__(self, region: str = "na1", output_dir: Path | None = None) -> None:
        super().__init__(output_dir)
        if not settings.riot_api_key:
            raise ValueError(
                "RIOT_API_KEY not set. Get a development key at developer.riotgames.com"
            )
        self.region = region
        self.cluster = _REGION_TO_CLUSTER.get(region, "americas")
        self.client.headers.update({"X-Riot-Token": settings.riot_api_key})

    @property
    def region_url(self) -> str:
        return f"https://{self.region}.api.riotgames.com"

    @property
    def cluster_url(self) -> str:
        return f"https://{self.cluster}.api.riotgames.com"

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict:
        """Resolve a Riot ID (gameName#tagLine) to an account record containing PUUID."""
        return self._get(
            f"{self.cluster_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )


class RiotLoLCollector(RiotBaseCollector):
    """Collect League of Legends match history and ranked stats via Riot Match v5 API."""

    platform = "riot_lol"
    # Keep under development key budget: 1 account + 1 match-ids + N match details
    # 20 matches × 1.3s = ~26s for live lookups (matches Valorant budget)
    MAX_MATCHES = 20

    def get_match_ids(self, puuid: str, count: int = 100) -> list[str]:
        """Fetch ranked solo/duo match IDs (queue=420)."""
        return self._get(
            f"{self.cluster_url}/lol/match/v5/matches/by-puuid/{puuid}/ids",
            params={"count": count, "queue": 420},
        )

    def get_match(self, match_id: str) -> dict:
        return self._get(f"{self.cluster_url}/lol/match/v5/matches/{match_id}")

    def get_summoner(self, puuid: str) -> dict:
        return self._get(f"{self.region_url}/lol/summoner/v4/summoners/by-puuid/{puuid}")

    def get_ranked(self, summoner_id: str) -> list[dict]:
        return self._get(f"{self.region_url}/lol/league/v4/entries/by-summoner/{summoner_id}")

    def collect(self, player_id: str) -> list[Path]:
        """Collect LoL data for a player.

        Args:
            player_id: Riot ID in "GameName#TAG" format, e.g. "Doublelift#NA1"

        Returns:
            List of saved file paths. PUUID is used as the stable file key.
        """
        if "#" not in player_id:
            raise ValueError(f"player_id must be 'GameName#TAG', got: {player_id!r}")

        game_name, tag_line = player_id.split("#", 1)
        saved: list[Path] = []

        # Resolve Riot ID → PUUID (stable, globally unique)
        account = self.get_account_by_riot_id(game_name, tag_line)
        puuid = account["puuid"]
        log.info("Resolved %s → PUUID %s", player_id, puuid[:12] + "...")
        saved.append(self._save_json(account, f"{puuid}_account.json"))
        # Lookup file: GameName#TAG → PUUID, used by data_service.get_player_live()
        safe_id = player_id.replace("#", "_")
        saved.append(self._save_json({"puuid": puuid, "riot_id": player_id}, f"{safe_id}_lookup.json"))

        # Match IDs
        try:
            match_ids = self.get_match_ids(puuid, count=self.MAX_MATCHES)
        except Exception:
            log.exception("Failed to fetch match IDs for %s", player_id)
            return saved

        # Fetch match details — extract only what we need per player to keep files small
        matches: list[dict] = []
        for mid in match_ids[: self.MAX_MATCHES]:
            try:
                raw = self.get_match(mid)
                info = raw.get("info", {})
                participant = next(
                    (p for p in info.get("participants", []) if p.get("puuid") == puuid),
                    {},
                )
                matches.append(
                    {
                        "matchId": mid,
                        "gameStartTimestamp": info.get("gameStartTimestamp"),
                        "gameDuration": info.get("gameDuration"),
                        "gameMode": info.get("gameMode"),
                        "win": participant.get("win"),
                        "kills": participant.get("kills"),
                        "deaths": participant.get("deaths"),
                        "assists": participant.get("assists"),
                    }
                )
                # 100 req/2 min = 0.83 req/sec sustained limit — 1.3s gives ~92 req/2 min
                time.sleep(1.3)
            except Exception:
                log.warning("Failed to fetch LoL match %s", mid)

        saved.append(self._save_json(matches, f"{puuid}_matches.json"))

        # Ranked stats
        try:
            summoner = self.get_summoner(puuid)
            saved.append(self._save_json(summoner, f"{puuid}_summoner.json"))
            ranked = self.get_ranked(summoner["id"])
            saved.append(self._save_json(ranked, f"{puuid}_ranked.json"))
        except Exception:
            log.warning("Failed to fetch ranked data for %s", player_id)

        log.info("Collected %d LoL matches for %s (PUUID: %s...)", len(matches), player_id, puuid[:12])
        return saved


class RiotValorantCollector(RiotBaseCollector):
    """Collect Valorant match history via Riot Val Match v1 API."""

    platform = "riot_valorant"
    MAX_MATCHES = 20  # Valorant match detail endpoint is heavier

    def get_match_list(self, puuid: str) -> dict:
        return self._get(f"{self.region_url}/val/match/v1/matchlists/by-puuid/{puuid}")

    def get_match(self, match_id: str) -> dict:
        return self._get(f"{self.region_url}/val/match/v1/matches/{match_id}")

    def collect(self, player_id: str) -> list[Path]:
        """Collect Valorant data for a player.

        Args:
            player_id: Riot ID in "GameName#TAG" format, e.g. "TenZ#NA1"

        Returns:
            List of saved file paths. PUUID is used as the stable file key.
        """
        if "#" not in player_id:
            raise ValueError(f"player_id must be 'GameName#TAG', got: {player_id!r}")

        game_name, tag_line = player_id.split("#", 1)
        saved: list[Path] = []

        account = self.get_account_by_riot_id(game_name, tag_line)
        puuid = account["puuid"]
        log.info("Resolved %s → PUUID %s", player_id, puuid[:12] + "...")
        saved.append(self._save_json(account, f"{puuid}_account.json"))
        # Lookup file: GameName#TAG → PUUID, used by data_service.get_player_live()
        safe_id = player_id.replace("#", "_")
        saved.append(self._save_json({"puuid": puuid, "riot_id": player_id}, f"{safe_id}_lookup.json"))

        # Match list
        try:
            match_list_data = self.get_match_list(puuid)
        except Exception:
            log.exception("Failed to fetch Valorant match list for %s", player_id)
            return saved

        history = match_list_data.get("history", [])
        matches: list[dict] = []

        for entry in history[: self.MAX_MATCHES]:
            mid = entry.get("matchId")
            if not mid:
                continue
            try:
                raw = self.get_match(mid)
                match_info = raw.get("matchInfo", {})
                player_data = next(
                    (p for p in raw.get("players", []) if p.get("puuid") == puuid),
                    {},
                )
                team_id = player_data.get("teamId")
                won = any(
                    t.get("won", False)
                    for t in raw.get("teams", [])
                    if t.get("teamId") == team_id
                )
                stats = player_data.get("stats", {})
                matches.append(
                    {
                        "matchId": mid,
                        "gameStartMillis": match_info.get("gameStartMillis"),
                        "gameLengthMillis": match_info.get("gameLengthMillis"),
                        "queueId": match_info.get("queueId"),
                        "win": won,
                        "kills": stats.get("kills"),
                        "deaths": stats.get("deaths"),
                        "assists": stats.get("assists"),
                    }
                )
                # 100 req/2 min = 0.83 req/sec sustained limit — 1.3s gives ~92 req/2 min
                time.sleep(1.3)
            except Exception:
                log.warning("Failed to fetch Valorant match %s", mid)

        saved.append(self._save_json(matches, f"{puuid}_matches.json"))
        log.info(
            "Collected %d Valorant matches for %s (PUUID: %s...)",
            len(matches),
            player_id,
            puuid[:12],
        )
        return saved
