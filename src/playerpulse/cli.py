"""PlayerPulse CLI — SDK entry point for technical studios.

Commands:
  playerpulse connect --api-key pp_live_xxx
  playerpulse sync --file players.csv
  playerpulse sync --file players.xlsx
  playerpulse sync --file players.parquet
  playerpulse sync --file players.json
  playerpulse sync --db postgres://...

Config stored at ~/.playerpulse/config.json

TODO (Sprint 7):
  - connect command: save API key to config
  - sync --file: parse file, engineer features, POST to API
  - sync --db: pull from DB, engineer features, POST to API
  - status command: show last sync result

Installation:
    uv pip install -e .
    # then use: playerpulse <command>
"""

import typer
from pathlib import Path

app = typer.Typer(
    name="playerpulse",
    help="PlayerPulse SDK — sync your player data to the PlayerPulse platform.",
)

CONFIG_PATH = Path.home() / ".playerpulse" / "config.json"


@app.command()
def connect(
    api_key: str = typer.Option(..., "--api-key", help="Your PlayerPulse API key (pp_live_xxx)"),
):
    """Save your API key to ~/.playerpulse/config.json."""
    # TODO (Sprint 7):
    #   - Validate key format (must start with pp_live_)
    #   - Test key against GET /api/v1/studios/me
    #   - Save to CONFIG_PATH
    raise NotImplementedError("TODO (Sprint 7): implement connect command")


@app.command()
def sync(
    file: Path = typer.Option(None, "--file", help="Path to CSV, Excel, Parquet, or JSON file"),
    db: str = typer.Option(None, "--db", help="Database connection string (postgres://, bigquery://)"),
):
    """Sync player data to PlayerPulse. Provide --file or --db."""
    # TODO (Sprint 7):
    #   - Load API key from CONFIG_PATH
    #   - If --file: detect format by extension, parse with polars/pandas
    #   - If --db: connect and pull player data
    #   - Engineer features locally
    #   - POST feature vectors to /api/v1/ingest/upload
    #   - Poll /api/v1/ingest/jobs/{id} until done
    #   - Print summary
    raise NotImplementedError("TODO (Sprint 7): implement sync command")


if __name__ == "__main__":
    app()
