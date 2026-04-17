"""Authentication middleware — API key validation and studio scoping.

Validates the X-API-Key header on every request and attaches studio_id
to request.state so all downstream services can scope data correctly.

Excludes /api/v1/demo/* — demo requires no API key.

TODO (Sprint 3):
  - Connect to Supabase studios table
  - Hash incoming key and compare to stored api_key_hash
  - Attach studio_id to request.state
  - Return 401 if key missing or invalid on protected routes
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

DEMO_PREFIX = "/api/v1/demo"
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Demo and public paths bypass auth
        if path.startswith(DEMO_PREFIX) or path in PUBLIC_PATHS:
            return await call_next(request)

        # TODO (Sprint 3): implement API key validation
        # api_key = request.headers.get("X-API-Key")
        # if not api_key:
        #     raise HTTPException(status_code=401, detail="Missing X-API-Key header")
        # studio_id = await studio_service.validate_api_key(api_key)
        # if not studio_id:
        #     raise HTTPException(status_code=401, detail="Invalid API key")
        # request.state.studio_id = studio_id

        return await call_next(request)
