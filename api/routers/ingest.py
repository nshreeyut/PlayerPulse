"""Ingest router — file upload and job status.

Accepts CSV/Excel uploads from studios, stores in Supabase Storage,
and kicks off a BackgroundTask to process the file.

TODO (Sprint 5):
  - POST /api/v1/ingest/upload      → accept CSV/Excel, queue processing
  - GET  /api/v1/ingest/jobs/{id}   → return job status
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Request

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

ALLOWED_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}


@router.post("/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # TODO (Sprint 5):
    #   studio_id = request.state.studio_id
    #   if file.content_type not in ALLOWED_TYPES:
    #       raise HTTPException(400, "Only CSV and Excel files accepted")
    #   job_id = await ingest_service.store_upload(file, studio_id)
    #   background_tasks.add_task(ingest_service.process_upload, job_id, studio_id)
    #   return {"job_id": job_id, "status": "pending"}
    raise HTTPException(status_code=501, detail="File upload not yet implemented")


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, request: Request):
    # TODO (Sprint 5):
    #   studio_id = request.state.studio_id
    #   return await ingest_service.get_job(job_id, studio_id)
    raise HTTPException(status_code=501, detail="Job status not yet implemented")
