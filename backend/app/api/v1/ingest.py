import os
import shutil
import uuid
import re
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from app.core.security import require_role
from app.models.enums import UserRoleEnum
from app.schemas.ingest import IngestionResponse
from app.worker.tasks import process_flash_report_task

router = APIRouter()

@router.post(
    "/flash-report",
    response_model=IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and Process Flash Report PDF",
    description="Asynchronous batch intake of monthly MoSPI Flash Report."
)
def ingest_flash_report(
    report_month: str = Form(..., description="Target reporting month (YYYY-MM)"),
    file: UploadFile = File(..., description="PDF Flash Report file"),
    current_user = Depends(require_role([UserRoleEnum.MOSPI_ADMIN]))
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
        
    if not re.match(r"^\d{4}-\d{2}$", report_month):
        raise HTTPException(status_code=400, detail="report_month must be in YYYY-MM format.")

    # Save file temporarily to pass to Celery
    temp_dir = "/tmp/mospi_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
        
    # Queue task
    task = process_flash_report_task.delay(temp_file_path, report_month)
    
    return IngestionResponse(
        task_id=task.id,
        status="QUEUED",
        report_month=report_month,
        message="Flash Report ingestion, 75-feature extraction, ML scoring, and ESI calculation queued for execution."
    )
