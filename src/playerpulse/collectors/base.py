"""Base collector with shared HTTP client logic."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from playerpulse.utils.config import RAW_DIR, settings


class BaseCollector(ABC):
    """Abstract base class for API data collectors."""

    platform: str = ""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or RAW_DIR / self.platform
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=settings.request_timeout)

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> BaseCollector:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        resp = self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _save_json(self, data: Any, filename: str) -> Path:
        path = self.output_dir / filename
        path.write_text(json.dumps(data, indent=2, default=str))
        return path

    @abstractmethod
    def collect(self, player_id: str) -> list[Path]:
        """Collect data for a player, return list of saved file paths."""
        ...
