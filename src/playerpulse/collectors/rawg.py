"""RAWG.io game metadata API collector.

API docs: https://rawg.io/apidocs
Requires RAWG_API_KEY in environment / .env file.

Request budget: 20,000/month. Cache-first strategy — disk cache is checked
before every API call. Files older than CACHE_TTL_DAYS are considered stale.
Default max_review_pages=2 (40 reviews) instead of 5 — sufficient for NLP signal.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from playerpulse.collectors.base import BaseCollector
from playerpulse.utils.config import settings

BASE_URL = "https://api.rawg.io/api"
CACHE_TTL_DAYS = 30


class RawgCollector(BaseCollector):
    """Collect game metadata from RAWG.io API."""

    platform = "rawg"

    def _cache_valid(self, path: Path) -> bool:
        """Return True if file exists and is younger than CACHE_TTL_DAYS."""
        if not path.exists():
            return False
        age_days = (time.time() - path.stat().st_mtime) / 86400
        return age_days < CACHE_TTL_DAYS

    def _load_json(self, path: Path) -> object:
        return json.loads(path.read_text())

    def search_game(self, query: str, page_size: int = 5) -> dict:
        """Search for games by name."""
        return self._get(
            f"{BASE_URL}/games",
            params={"key": settings.rawg_api_key, "search": query, "page_size": page_size},
        )

    def get_game(self, game_id: int) -> dict:
        """Fetch detailed game metadata."""
        return self._get(
            f"{BASE_URL}/games/{game_id}",
            params={"key": settings.rawg_api_key},
        )

    def get_game_by_slug(self, slug: str) -> dict:
        """Fetch game by slug (e.g., 'dota-2', 'league-of-legends'). Cache-first."""
        cache_path = self.output_dir / f"{slug}_metadata.json"
        if self._cache_valid(cache_path):
            return self._load_json(cache_path)  # type: ignore[return-value]
        return self._get(
            f"{BASE_URL}/games/{slug}",
            params={"key": settings.rawg_api_key},
        )

    def get_game_reviews(self, game_id: int | str, page: int = 1, page_size: int = 20) -> dict:
        """Fetch one page of user reviews for a game.

        Args:
            game_id: RAWG game ID or slug
            page: Page number (1-indexed)
            page_size: Results per page (max 40)
        """
        return self._get(
            f"{BASE_URL}/games/{game_id}/reviews",
            params={"key": settings.rawg_api_key, "page": page, "page_size": page_size},
        )

    def get_all_reviews(self, game_id: int | str, max_pages: int = 2) -> list[dict]:
        """Fetch multiple pages of reviews and return a flat list.

        Args:
            game_id: RAWG game ID or slug
            max_pages: Maximum number of pages to fetch (each page = 20 reviews).
                       Default 2 (40 reviews) — sufficient for NLP signal, saves budget.

        Returns:
            Flat list of review objects
        """
        reviews: list[dict] = []
        for page in range(1, max_pages + 1):
            data = self.get_game_reviews(game_id, page=page)
            results = data.get("results", [])
            reviews.extend(results)
            if not data.get("next"):
                break
        return reviews

    def collect(self, player_id: str, max_review_pages: int = 2, force: bool = False) -> list[Path]:
        """Collect game metadata and reviews. player_id is treated as a game slug.

        Skips API calls entirely if cached files are fresh (< 30 days old).
        Pass force=True to bypass cache and re-fetch.

        Args:
            player_id: Game slug (e.g., 'dota-2', 'chess')
            max_review_pages: Review pages to fetch if cache miss (20 reviews each). Default 2.
            force: Ignore cache and always hit the API.

        Returns:
            List of saved file paths
        """
        saved: list[Path] = []
        slug = player_id.lower()

        metadata_path = self.output_dir / f"{slug}_metadata.json"
        reviews_path = self.output_dir / f"{slug}_reviews.json"

        if not force and self._cache_valid(metadata_path):
            saved.append(metadata_path)
        else:
            game = self.get_game_by_slug(slug)
            saved.append(self._save_json(game, f"{slug}_metadata.json"))

        if not force and self._cache_valid(reviews_path):
            saved.append(reviews_path)
        else:
            reviews = self.get_all_reviews(slug, max_pages=max_review_pages)
            saved.append(self._save_json(reviews, f"{slug}_reviews.json"))

        return saved
