"""Tests for active data collectors: OpenDota, RAWG, Steam."""

from __future__ import annotations

from unittest.mock import patch

from playerpulse.collectors.opendota import OpenDotaCollector
from playerpulse.collectors.rawg import RawgCollector
from playerpulse.collectors.steam import SteamCollector


def test_opendota_collect(tmp_path: object) -> None:
    """Test OpenDota collector produces expected files."""
    with patch.object(OpenDotaCollector, "_get") as mock_get:
        mock_get.side_effect = [
            {"profile": {"account_id": 12345}},                         # player
            {"win": 100, "lose": 50},                                    # wl
            [{"match_id": 1, "player_slot": 0}],                        # matches
            [{"account_id": 99, "games": 10}],                          # peers
            [{"account_id": 12345, "solo_competitive_rank": 3000}],     # ratings
        ]
        collector = OpenDotaCollector()
        collector.output_dir = tmp_path  # type: ignore[assignment]
        paths = collector.collect("12345")
        assert len(paths) == 5
        assert all(p.exists() for p in paths)


def test_steam_collect(tmp_path: object) -> None:
    """Test Steam collector produces expected files."""
    steam_id = "76561198012345678"
    with (
        patch.object(SteamCollector, "_get") as mock_get,
        patch("playerpulse.collectors.steam.settings") as mock_settings,
    ):
        mock_settings.steam_api_key = "fake_key"
        mock_settings.request_timeout = 30
        mock_settings.max_retries = 3
        mock_get.side_effect = [
            {"response": {"players": [{"steamid": steam_id, "personaname": "TestUser", "lastlogoff": 1700000000}]}},  # summary
            {"response": {"game_count": 2, "games": [
                {"appid": 570, "name": "Dota 2", "playtime_forever": 5000, "playtime_2weeks": 120},
                {"appid": 730, "name": "CS2", "playtime_forever": 3000},
            ]}},  # owned games
            {"response": {"total_count": 1, "games": [
                {"appid": 570, "name": "Dota 2", "playtime_2weeks": 120, "playtime_forever": 5000},
            ]}},  # recently played
            {"friendslist": {"friends": [
                {"steamid": "76561198000000001", "relationship": "friend"},
                {"steamid": "76561198000000002", "relationship": "friend"},
            ]}},  # friends
        ]
        collector = SteamCollector()
        collector.output_dir = tmp_path  # type: ignore[assignment]
        paths = collector.collect(steam_id)
        assert len(paths) == 4
        assert all(p.exists() for p in paths)


def test_steam_collect_private_friends(tmp_path: object) -> None:
    """Test Steam collector handles private friend list gracefully."""
    steam_id = "76561198012345678"
    with (
        patch.object(SteamCollector, "_get") as mock_get,
        patch("playerpulse.collectors.steam.settings") as mock_settings,
    ):
        mock_settings.steam_api_key = "fake_key"
        mock_settings.request_timeout = 30
        mock_settings.max_retries = 3

        def side_effect(url: str, params: dict | None = None):
            if "GetPlayerSummaries" in url:
                return {"response": {"players": [{"steamid": steam_id, "personaname": "Private"}]}}
            if "GetOwnedGames" in url:
                return {"response": {"game_count": 1, "games": [{"appid": 570, "name": "Dota 2", "playtime_forever": 100}]}}
            if "GetRecentlyPlayedGames" in url:
                return {"response": {"total_count": 0, "games": []}}
            if "GetFriendList" in url:
                raise Exception("403 Forbidden")
            return {}

        mock_get.side_effect = side_effect
        collector = SteamCollector()
        collector.output_dir = tmp_path  # type: ignore[assignment]
        paths = collector.collect(steam_id)
        # Should still save 4 files — friends file contains empty list
        assert len(paths) == 4


def test_rawg_collect(tmp_path: object) -> None:
    """Test RAWG collector produces expected files."""
    with patch.object(RawgCollector, "_get") as mock_get:
        mock_get.side_effect = [
            {"count": 1, "results": [{"id": 1, "slug": "dota-2", "name": "Dota 2"}]},  # search
            {"id": 1, "slug": "dota-2", "name": "Dota 2", "rating": 4.5},              # game detail
            {"count": 2, "results": [                                                    # reviews page 1
                {"id": 10, "text": "Great game!", "rating": 5},
                {"id": 11, "text": "Fun but complex", "rating": 4},
            ]},
            {"count": 2, "results": []},                                                 # reviews page 2 (empty → stop)
        ]
        collector = RawgCollector()
        collector.output_dir = tmp_path  # type: ignore[assignment]
        paths = collector.collect("dota-2")
        assert len(paths) >= 1
        assert all(p.exists() for p in paths)
