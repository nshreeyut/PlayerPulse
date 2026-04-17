"""
Game Registry
==============
Single source of truth for all active data sources.

To add a new platform:
  1. Build collector in src/playerpulse/collectors/your_platform.py
  2. Add standardize_*() in src/playerpulse/features/standardize.py
  3. Add entry here

The frontend dropdown and agent tools both read from this registry —
no other files need to change when you add a platform.
"""

GAME_REGISTRY: dict[str, dict] = {
    "opendota": {
        "display_name": "Dota 2 (OpenDota)",
        "collector_class": "playerpulse.collectors.opendota.OpenDotaCollector",
        "requires_api_key": False,
        "player_id_label": "Account ID",
        "player_id_example": "87278757",
        "description": "Dota 2 match history, MMR progression, and social graph via OpenDota API",
    },
    "steam": {
        "display_name": "Steam",
        "collector_class": "playerpulse.collectors.steam.SteamCollector",
        "requires_api_key": True,
        "player_id_label": "Steam 64-bit ID",
        "player_id_example": "76561198012345678",
        "description": "Steam playtime, recently played games, and friend list",
    },
    "riot_lol": {
        "display_name": "League of Legends",
        "collector_class": "playerpulse.collectors.riot.RiotLoLCollector",
        "requires_api_key": True,
        "player_id_label": "Riot ID (Name#TAG)",
        "player_id_example": "Faker#KR1",
        "description": "League of Legends match history and performance via Riot Games API",
    },
    "riot_valorant": {
        "display_name": "Valorant",
        "collector_class": "playerpulse.collectors.riot.RiotValorantCollector",
        "requires_api_key": True,
        "player_id_label": "Riot ID (Name#TAG)",
        "player_id_example": "TenZ#NA1",
        "description": "Valorant match history and performance via Riot Games API",
    },
    # RAWG is a review source — feeds the NLP agent, not the player lookup flow
    # It does not appear in the player search dropdown
}


def get_supported_games() -> list[dict]:
    """Returns all registered platforms as a list for the frontend dropdown."""
    return [{"id": game_id, **metadata} for game_id, metadata in GAME_REGISTRY.items()]


def get_game(game_id: str) -> dict:
    """Look up a platform by registry ID. Raises KeyError if not found."""
    if game_id not in GAME_REGISTRY:
        raise KeyError(
            f"Unknown platform: '{game_id}'. Supported: {list(GAME_REGISTRY.keys())}"
        )
    return GAME_REGISTRY[game_id]
