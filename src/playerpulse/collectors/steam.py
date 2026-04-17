"""Steam Web API collector.

API docs: https://developer.steampowered.com/doc/webapi
Requires: STEAM_API_KEY (get one at https://steamcommunity.com/dev/apikey)

Player IDs are 64-bit Steam IDs (e.g. 76561198012345678).
Find yours at: https://www.steamidfinder.com

What we collect per player:
  - Summary      → persona name, last logoff (recency signal)
  - Owned games  → playtime_forever per game (total engagement)
  - Recent games → playtime_2weeks per game (current activity)
  - Friend list  → friend count (social signal)

Reviews are collected per game (app_id), not per player.
Call get_game_reviews(app_id) separately — used by the NLP agent.
"""

from __future__ import annotations

import logging
from pathlib import Path

from playerpulse.collectors.base import BaseCollector
from playerpulse.utils.config import settings

log = logging.getLogger(__name__)

BASE_URL = "https://api.steampowered.com"
STORE_URL = "https://store.steampowered.com"


class SteamCollector(BaseCollector):
    """Collect player behavioral data from the Steam Web API."""

    platform = "steam"

    def get_player_summary(self, steam_id: str) -> dict:
        """Fetch public profile: persona name, avatar, last logoff timestamp.

        last_logoff is the strongest recency signal — unix timestamp of last
        time the player was online. Missing if profile is private.
        """
        data = self._get(
            f"{BASE_URL}/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": settings.steam_api_key, "steamids": steam_id},
        )
        players = data.get("response", {}).get("players", [])
        return players[0] if players else {}

    def get_owned_games(self, steam_id: str) -> dict:
        """Fetch all owned games with playtime_forever (minutes).

        playtime_forever = total minutes played across all time.
        playtime_2weeks  = minutes played in the last 2 weeks (may be absent if 0).
        """
        return self._get(
            f"{BASE_URL}/IPlayerService/GetOwnedGames/v1/",
            params={
                "key": settings.steam_api_key,
                "steamid": steam_id,
                "include_appinfo": 1,
                "include_played_free_games": 1,
            },
        )

    def get_recently_played(self, steam_id: str, count: int = 10) -> dict:
        """Fetch games played in the last 2 weeks.

        This is our primary frequency + duration signal:
        - game count = how many distinct games played recently
        - sum of playtime_2weeks = total recent session time (minutes)
        """
        return self._get(
            f"{BASE_URL}/IPlayerService/GetRecentlyPlayedGames/v1/",
            params={
                "key": settings.steam_api_key,
                "steamid": steam_id,
                "count": count,
            },
        )

    def get_friend_list(self, steam_id: str) -> list[dict]:
        """Fetch friend list (requires public profile).

        Friend count is our social signal — players with more friends churn less.
        Returns empty list if profile is private (not an error).
        """
        try:
            data = self._get(
                f"{BASE_URL}/ISteamUser/GetFriendList/v1/",
                params={
                    "key": settings.steam_api_key,
                    "steamid": steam_id,
                    "relationship": "friend",
                },
            )
            return data.get("friendslist", {}).get("friends", [])
        except Exception:
            log.warning("Friend list unavailable for %s (private profile)", steam_id)
            return []

    def get_game_reviews(
        self,
        app_id: str | int,
        language: str = "english",
        num_per_page: int = 100,
        max_pages: int = 3,
    ) -> list[dict]:
        """Fetch recent user reviews for a game (used by NLP agent).

        Uses the Steam Store reviews endpoint (separate from the Web API).
        Paginates using cursor-based pagination until max_pages reached or
        no more reviews are returned.

        Args:
            app_id:       Steam app ID (e.g. 570 for Dota 2)
            language:     Review language filter
            num_per_page: Reviews per page (max 100)
            max_pages:    Maximum pages to fetch

        Returns:
            Flat list of review dicts
        """
        reviews: list[dict] = []
        cursor = "*"

        for page in range(max_pages):
            data = self._get(
                f"{STORE_URL}/appreviews/{app_id}",
                params={
                    "json": 1,
                    "filter": "recent",
                    "language": language,
                    "num_per_page": num_per_page,
                    "cursor": cursor,
                    "purchase_type": "all",
                },
            )
            batch = data.get("reviews", [])
            if not batch:
                break

            reviews.extend(batch)
            cursor = data.get("cursor", "")
            log.info("Fetched page %d — %d reviews (app_id=%s)", page + 1, len(batch), app_id)

            if not cursor:
                break

        return reviews

    def collect(self, player_id: str) -> list[Path]:
        """Collect all behavioral data for a Steam player.

        Args:
            player_id: 64-bit Steam ID (e.g. "76561198012345678")

        Returns:
            List of saved file paths
        """
        if not settings.steam_api_key:
            raise RuntimeError("STEAM_API_KEY is not set — cannot collect Steam data")

        saved: list[Path] = []
        sid = player_id

        summary = self.get_player_summary(sid)
        saved.append(self._save_json(summary, f"{sid}_summary.json"))
        log.info("Saved summary for %s (persona: %s)", sid, summary.get("personaname", "?"))

        owned = self.get_owned_games(sid)
        saved.append(self._save_json(owned, f"{sid}_owned_games.json"))
        game_count = owned.get("response", {}).get("game_count", 0)
        log.info("Saved %d owned games for %s", game_count, sid)

        recent = self.get_recently_played(sid)
        saved.append(self._save_json(recent, f"{sid}_recently_played.json"))
        recent_count = len(recent.get("response", {}).get("games", []))
        log.info("Saved %d recently played games for %s", recent_count, sid)

        friends = self.get_friend_list(sid)
        saved.append(self._save_json(friends, f"{sid}_friends.json"))
        log.info("Saved %d friends for %s", len(friends), sid)

        return saved
