"""Studios router — registration, API key generation, account management.

TODO (Sprint 3):
  - POST /api/v1/studios     → register studio, return API key (shown once)
  - GET  /api/v1/studios/me  → return studio profile (key masked)
"""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/v1/studios", tags=["studios"])


@router.post("")
async def register_studio(request: Request):
    # TODO (Sprint 3):
    #   body = StudioCreate(**await request.json())
    #   result = await studio_service.create_studio(body)
    #   return APIKeyResponse(studio_id=result.id, api_key=result.raw_key)
    raise HTTPException(status_code=501, detail="Studio registration not yet implemented")


@router.get("/me")
async def get_studio(request: Request):
    # TODO (Sprint 3):
    #   studio_id = request.state.studio_id  (set by AuthMiddleware)
    #   return await studio_service.get_studio(studio_id)
    raise HTTPException(status_code=501, detail="Studio profile not yet implemented")
