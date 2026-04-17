"""Ingest service — file processing pipeline as a BackgroundTask.

Flow: uploaded file → parse CSV/Excel → schema agent maps columns
      → standardize → engineer features → score + SHAP → store in Supabase

TODO (Sprint 5):
  - store_upload(file, studio_id) → job_id
  - process_upload(job_id, studio_id) → runs as BackgroundTask
  - get_job(job_id, studio_id) → upload job status
"""

from fastapi import UploadFile


async def store_upload(file: UploadFile, studio_id: str) -> str:
    """Store uploaded file in Supabase Storage and create an upload_jobs row.

    Returns:
        job_id for status polling
    """
    # TODO (Sprint 5):
    #   - Upload file bytes to Supabase Storage bucket
    #   - Insert row into upload_jobs table with status='pending'
    #   - Return job_id
    raise NotImplementedError("TODO (Sprint 5): store file in Supabase Storage")


async def process_upload(job_id: str, studio_id: str) -> None:
    """BackgroundTask: parse file → map schema → engineer → score → store.

    Steps:
      1. Download file from Supabase Storage
      2. Parse CSV or Excel into rows
      3. schema_agent.infer_field_mapping() → FieldMap
      4. mapping_service.apply_field_map() → standardized rows
      5. standardize.py → PlayerActivity objects
      6. engineer.py → feature vectors
      7. model_service.predict_churn() → churn probability + risk level
      8. shap_service.get_player_shap() → SHAP values
      9. Store players, features, predictions, shap_values in Supabase
      10. Update upload_jobs status to 'done'
    """
    # TODO (Sprint 5): implement full pipeline
    raise NotImplementedError("TODO (Sprint 5): implement upload processing pipeline")


async def get_job(job_id: str, studio_id: str) -> dict:
    """Return upload job status from Supabase upload_jobs table."""
    # TODO (Sprint 5): query Supabase upload_jobs table
    raise NotImplementedError("TODO (Sprint 5): fetch job status from Supabase")
