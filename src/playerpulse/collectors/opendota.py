"""OpenDota public API collector.

API docs: https://docs.opendota.com/
Free tier: 60 calls/min, no key required.
"""

from __future__ import annotations

from pathlib import Path

from playerpulse.collectors.base import BaseCollector

BASE_URL = "https://api.opendota.com/api"


class OpenDotaCollector(BaseCollector):
    """Collect player data from OpenDota API."""

    platform = "opendota"

    def get_player(self, account_id: str) -> dict:
        """Fetch player profile."""
        return self._get(f"{BASE_URL}/players/{account_id}")

    def get_win_loss(self, account_id: str) -> dict:
        """Fetch win/loss record."""
        return self._get(f"{BASE_URL}/players/{account_id}/wl")

    def get_recent_matches(self, account_id: str, limit: int = 100) -> list[dict]:
        """Fetch recent matches."""
        return self._get(
            f"{BASE_URL}/players/{account_id}/recentMatches",
        )

    def get_matches(self, account_id: str, limit: int = 200) -> list[dict]:
        """Fetch match history with details."""
        return self._get(
            f"{BASE_URL}/players/{account_id}/matches",
            params={"limit": limit},
        )

    def get_peers(self, account_id: str) -> list[dict]:
        """Fetch social graph (players frequently played with)."""
        return self._get(f"{BASE_URL}/players/{account_id}/peers")

    def get_ratings(self, account_id: str) -> list[dict]:
        """Fetch MMR rating history."""
        return self._get(f"{BASE_URL}/players/{account_id}/ratings")

    def collect(self, player_id: str) -> list[Path]:
        """Collect all available data for a Dota 2 player.

        Args:
            player_id: Steam account ID (32-bit)

        Returns:
            List of saved file paths
        """
        saved: list[Path] = []
        aid = player_id

        player = self.get_player(aid)
        saved.append(self._save_json(player, f"{aid}_player.json"))

        wl = self.get_win_loss(aid)
        saved.append(self._save_json(wl, f"{aid}_winloss.json"))

        matches = self.get_matches(aid)
        saved.append(self._save_json(matches, f"{aid}_matches.json"))

        peers = self.get_peers(aid)
        # Keep top 50 peers by games played together
        peers_sorted = sorted(peers, key=lambda p: p.get("games", 0), reverse=True)[:50]
        saved.append(self._save_json(peers_sorted, f"{aid}_peers.json"))

        ratings = self.get_ratings(aid)
        saved.append(self._save_json(ratings, f"{aid}_ratings.json"))

        return saved
