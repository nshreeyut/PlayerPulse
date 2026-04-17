"""Pydantic schemas for studio accounts and API keys.

TODO (Sprint 3): implement fully once Supabase schema is created.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Literal


class StudioCreate(BaseModel):
    name: str
    email: EmailStr


class Studio(BaseModel):
    id: str
    name: str
    email: str
    api_key_masked: str        # e.g. "pp_live_a8f3...xxxx"
    plan: Literal["free", "pro"] = "free"
    created_at: datetime


class APIKeyResponse(BaseModel):
    """Returned once on studio creation — key is never shown again."""
    studio_id: str
    api_key: str               # full key, shown only at creation
    message: str = "Store this API key securely — it will not be shown again."
