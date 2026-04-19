"""
Model startup loader
=====================
On startup, checks whether the production model files exist in MODELS_DIR.
If any are missing and MODEL_RELEASE_URL is configured, downloads them.

This lets Render (or any host) bootstrap the persistent disk automatically
on first cold-start without manual file uploads.

Setup:
  1. Train models locally: make features && make train
  2. Create a GitHub Release and attach all *.joblib files
  3. Set MODEL_RELEASE_URL=https://github.com/USER/REPO/releases/download/TAG
     in your Render environment variables
  4. Set MODELS_DIR=/var/data/models (persistent disk mount path)
  5. Deploy — models download automatically on first start

After the disk is populated, subsequent starts skip the download entirely.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Files required for live player lookup (production models).
# Demo mode loads from models/demo/ and never needs these.
_REQUIRED_MODELS = [
    "scaler.joblib",
    "lightgbm.joblib",
    "xgboost.joblib",
    "catboost.joblib",
    "ensemble.joblib",
    "logistic_regression.joblib",
]


def ensure_models(models_dir: Path, release_url: str) -> None:
    """Download any missing model files from a GitHub Release.

    Args:
        models_dir:   Path where models should live (e.g. /var/data/models).
        release_url:  Base URL of the GitHub Release, e.g.
                      https://github.com/USER/REPO/releases/download/v1.0-models
                      Each filename is appended: {release_url}/{filename}
    """
    missing = [f for f in _REQUIRED_MODELS if not (models_dir / f).exists()]
    if not missing:
        log.info("All model files present in %s — skipping download", models_dir)
        return

    log.info(
        "%d model file(s) missing in %s — downloading from release ...",
        len(missing),
        models_dir,
    )
    models_dir.mkdir(parents=True, exist_ok=True)

    import httpx

    for filename in missing:
        url = f"{release_url.rstrip('/')}/{filename}"
        dest = models_dir / filename
        log.info("Downloading %s ...", filename)
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=120) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=1024 * 256):
                        f.write(chunk)
            size_kb = dest.stat().st_size // 1024
            log.info("Saved %s (%d KB)", filename, size_kb)
        except Exception:
            log.exception("Failed to download %s from %s", filename, url)
            if dest.exists():
                dest.unlink()  # remove partial file

    still_missing = [f for f in _REQUIRED_MODELS if not (models_dir / f).exists()]
    if still_missing:
        log.warning(
            "Some models still missing after download: %s. "
            "Live player lookup will be unavailable until they are present.",
            still_missing,
        )
    else:
        log.info("All model files ready in %s", models_dir)
