import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.risk import MLRiskScore
from app.models.execution import ExecutionStressScore

class IngestionPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def persist_ml_risk_scores(self, df: pd.DataFrame) -> int:
        """
        Takes a valid BatchScorer output DataFrame and bulk upserts into ml_risk_scores.
        Does not fabricate data or modify ML logic.
        """
        if df.empty:
            return 0
            
        records = df.to_dict(orient="records")
        
        stmt = insert(MLRiskScore).values(records)
        
        # Upsert: ON CONFLICT UPDATE
        update_dict = {
            c.name: c
            for c in stmt.excluded
            if not c.primary_key
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['project_id', 'report_month'],
            set_=update_dict
        )
        
        self.db.execute(upsert_stmt)
        self.db.commit()
        return len(records)

    def persist_execution_stress_scores(self, df: pd.DataFrame) -> int:
        """
        Takes a valid ExecutionSurveillanceEngine output DataFrame and bulk upserts into execution_stress_scores.
        """
        if df.empty:
            return 0
            
        records = df.to_dict(orient="records")
        
        stmt = insert(ExecutionStressScore).values(records)
        
        update_dict = {
            c.name: c
            for c in stmt.excluded
            if not c.primary_key
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['project_id', 'report_month'],
            set_=update_dict
        )
        
        self.db.execute(upsert_stmt)
        self.db.commit()
        return len(records)
