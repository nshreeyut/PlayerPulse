"""
Data Service
=============
Handles loading and querying the player features dataset.

The feature table lives at:
  data/03_features/player_features.parquet

This service is the single point of contact for that file.
If you ever migrate from Parquet to PostgreSQL, you change this file only —
routers, agents, and other services never know the difference.

POLARS QUICK REFERENCE (you'll need these):
--------------------------------------------
Load a file:     pl.read_parquet(path)
Filter rows:     df.filter(pl.col("platform") == "opendota")
Select columns:  df.select(["player_id", "engagement_score"])
Convert to dict: df.to_dicts()          → list of dicts
First row dict:  df.to_dicts()[0]       → single dict
Count rows:      df.height
Unique values:   df["platform"].unique()

LEARN MORE: https://docs.pola.rs/user-guide/getting-started/
"""

import polars as pl
from functools import lru_cache

from api.config import settings


@lru_cache(maxsize=1)
def load_features() -> pl.DataFrame:
    """
    Load the player features parquet file into memory (cached after first load).

    @lru_cache(maxsize=1) means the file is only read from disk once.
    The DataFrame stays in memory for the lifetime of the API process.
    This is fine for moderate dataset sizes (< 1GB). For larger data,
    you'd switch to a database with proper indexing.

    TODO: Implement this function.
    Steps:
      1. Check if settings.features_path exists
      2. If not, raise FileNotFoundError with a helpful message like:
         "Feature file not found. Run `make train` to generate it."
      3. Return pl.read_parquet(settings.features_path)
    """
    raise NotImplementedError("TODO: implement load_features()")


def get_player(player_id: str, platform: str) -> dict | None:
    """
    Look up a single player's features by their ID and platform.

    Args:
        player_id: the player's ID (e.g., "hikaru" for Chess.com)
        platform:  registry key (e.g., "opendota")

    Returns:
        A dict of all feature values, or None if the player isn't in the dataset.

    TODO: Implement this.
    Steps:
      1. df = load_features()
      2. filtered = df.filter(
             (pl.col("player_id") == player_id) &
             (pl.col("platform") == platform)
         )
      3. If filtered.height == 0: return None
      4. Return filtered.to_dicts()[0]
    """
    raise NotImplementedError("TODO: implement get_player()")


def list_players(platform: str | None = None, limit: int = 100) -> list[dict]:
    """
    Return a list of players from the dataset, optionally filtered by platform.
    Powers the browse/search functionality in the frontend.

    TODO: Implement this.
    Steps:
      1. df = load_features()
      2. If platform is provided: df = df.filter(pl.col("platform") == platform)
      3. Select only the columns useful for listing:
         ["player_id", "platform", "engagement_score", "churned", "days_since_last_game"]
      4. Limit: df = df.head(limit)
      5. Return df.to_dicts()
    """
    raise NotImplementedError("TODO: implement list_players()")


def get_dataset_summary() -> dict:
    """
    Return high-level statistics about the dataset.
    The LangChain agent calls this so the chatbot can answer general questions
    like "what's the overall churn rate?" without querying individual players.

    TODO: Implement this to return something like:
    {
        "total_players": 2000,
        "churned_count": 600,
        "churn_rate": 0.30,
        "platforms": ["opendota", "opendota"],
        "avg_engagement_score": 52.3,
        "avg_days_since_last_game": 8.1,
    }

    Hints:
      df.height                          → total row count
      df["churned"].sum()                → count of True values
      df["platform"].unique().to_list()  → list of unique platforms
      df["engagement_score"].mean()      → average
    """
    raise NotImplementedError("TODO: implement get_dataset_summary()")
