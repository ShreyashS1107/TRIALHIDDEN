from app.worker.celery_app import celery_app
import logging
from app.services.ml_integration import MLIntegrationAdapter
from app.database.session import SessionLocal
from app.services.ingestion import IngestionPersistenceService
from app.services.alert_generation import AlertGenerationService
import os

# Initialize inference bridge
import inference
from inference.adapter import extract_features_for_inference
from ml.inference.batch_scorer import BatchScorer
from ml.surveillance.surveillance_engine import ExecutionSurveillanceEngine

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_flash_report_task")
def process_flash_report_task(self, file_path: str, report_month: str):
    """
    Background worker for PDF ingestion, 75-feature extraction, ML scoring, ESI, and Alerts.
    
    Final Worker Flow:
    1. receive PDF path + report_month
    2. invoke ML-owned feature extraction interface
    3. validate returned feature DataFrames
    4. call existing BatchScorer
    5. call existing ExecutionSurveillanceEngine
    6. persist returned outputs using existing IngestionPersistenceService
    7. generate alerts using existing AlertGenerationService
    8. clean up temporary PDF
    """
    logger.info(f"Starting Flash Report Processing for month {report_month}")
    db_session = SessionLocal()
    
    try:
        # 2. Invoke ML-Owned Extraction Interface
        logger.info("Extracting features using inference adapter...")
        risk_df, esi_df = extract_features_for_inference(file_path, report_month, db_session)
        
        # 3. Validate Features against Backend Adapter constraints
        MLIntegrationAdapter.validate_risk_features(risk_df)
        MLIntegrationAdapter.validate_esi_features(esi_df)
        
        # 4. Call Existing BatchScorer
        logger.info("Running Predictive ML Risk Scoring...")
        scorer = BatchScorer()
        risk_output_df = scorer.score_batch(risk_df)
        
        # 5. Call Existing ExecutionSurveillanceEngine
        logger.info("Running ESI Surveillance Engine...")
        esi_engine = ExecutionSurveillanceEngine()
        esi_output_df = esi_engine.compute_scores(esi_df)
        
        # 6. Persistence
        logger.info("Persisting outputs...")
        persistence_svc = IngestionPersistenceService(db_session)
        persistence_svc.persist_ml_risk_scores(risk_output_df)
        persistence_svc.persist_execution_stress_scores(esi_output_df)
        
        # 7. Generate alerts
        logger.info("Generating operational alerts...")
        alert_svc = AlertGenerationService(db_session)
        alert_svc.generate_alerts_from_inference(risk_output_df, esi_output_df)
        
        db_session.commit()
        return "SUCCESS"
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Inference pipeline failed: {e}")
        raise e
        
    finally:
        db_session.close()
        # 8. Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
