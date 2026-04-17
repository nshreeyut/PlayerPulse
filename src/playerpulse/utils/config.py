"""Project configuration and settings."""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "01_raw"
PROCESSED_DIR = DATA_DIR / "02_processed"
FEATURES_DIR = DATA_DIR / "03_features"
PREDICTIONS_DIR = DATA_DIR / "04_predictions"
MODELS_DIR = PROJECT_ROOT / "models"
MLFLOW_DIR = PROJECT_ROOT / ".mlflow"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {"env_prefix": "PLAYERPULSE_", "env_file": ".env", "extra": "ignore"}

    steam_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("STEAM_API_KEY", "PLAYERPULSE_STEAM_API_KEY"),
        description="Steam Web API key",
    )
    rawg_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("RAWG_API_KEY", "PLAYERPULSE_RAWG_API_KEY"),
        description="RAWG.io API key",
    )
    riot_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("RIOT_API_KEY", "PLAYERPULSE_RIOT_API_KEY"),
        description="Riot Games API key — covers LoL + Valorant + TFT",
    )
    # OpenDota needs no key

    churn_threshold_days: int = Field(default=14, description="Days inactive to label as churned")
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    max_retries: int = Field(default=3, description="Max API request retries")


settings = Settings()
