"""Studio service — create studios, generate and validate API keys.

All API keys are hashed before storage (SHA-256). The raw key is
returned once at creation and never stored in plaintext.

TODO (Sprint 3):
  - create_studio(studio_create) → (Studio, raw_api_key)
  - validate_api_key(raw_key) → studio_id | None
  - get_studio(studio_id) → Studio
"""

import hashlib
import secrets
from api.models.studio import Studio, StudioCreate


API_KEY_PREFIX = "pp_live_"


def _generate_api_key() -> tuple[str, str]:
    """Generate a raw API key and its SHA-256 hash.

    Returns:
        (raw_key, hashed_key) — store only the hash
    """
    raw = API_KEY_PREFIX + secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def _mask_key(raw_key: str) -> str:
    """Return masked version for display: pp_live_a8f3...xxxx"""
    return raw_key[:16] + "..." + raw_key[-4:]


async def create_studio(studio_create: StudioCreate) -> tuple[dict, str]:
    """Create a new studio account and generate its API key.

    TODO (Sprint 3):
      - Insert row into Supabase studios table
      - Store api_key_hash, NOT the raw key
      - Return Studio object + raw key (shown once to user)
    """
    raise NotImplementedError("TODO (Sprint 3): insert studio into Supabase and return API key")


async def validate_api_key(raw_key: str) -> str | None:
    """Hash the incoming key and look it up in Supabase.

    Returns:
        studio_id if valid, None if not found
    """
    # TODO (Sprint 3): hash key, query Supabase studios table
    raise NotImplementedError("TODO (Sprint 3): validate API key against Supabase")


async def get_studio(studio_id: str) -> Studio:
    """Fetch studio profile from Supabase by studio_id."""
    # TODO (Sprint 3): query Supabase studios table
    raise NotImplementedError("TODO (Sprint 3): fetch studio from Supabase")
