from app.worker.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_flash_report_task")
def process_flash_report_task(self, file_path: str, report_month: str):
    """
    Background worker for PDF ingestion, 75-feature extraction, ML scoring, ESI, and Alerts.
    """
    logger.info(f"Starting Flash Report Processing for month {report_month}")
    
    # BOUNDARY: PDF -> FEATURE EXTRACTION
    # The project lacks a production-ready pipeline to convert a raw PDF into the 
    # strictly required 75-feature DataFrame for BatchScorer and 12-feature for ESI.
    error_msg = "PDF feature extraction pipeline is an external/ML-side dependency and is not implemented."
    logger.error(error_msg)
    
    # We deliberately fail here cleanly instead of fabricating data.
    raise NotImplementedError(error_msg)
