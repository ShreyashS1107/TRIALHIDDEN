import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.alert import SystemAlert
from app.models.enums import AlertSeverityEnum, AlertSourceEnum

class AlertGenerationService:
    def __init__(self, db: Session):
        self.db = db

    def generate_alerts_from_inference(self, risk_df: pd.DataFrame, esi_df: pd.DataFrame) -> int:
        """
        Consumes already-produced Risk and ESI DataFrames and maps thresholds to system_alerts.
        Rules:
        - ESI Tier [WATCH, ATTENTION, HIGH_PRIORITY] -> Alerts
        - Risk Band [HIGH, VERY_HIGH] -> Alerts
        """
        alerts_to_insert = []
        
        # 1. Process ESI Alerts
        if not esi_df.empty:
            for _, row in esi_df.iterrows():
                tier = row.get("esi_tier")
                if tier in ["WATCH", "ATTENTION", "HIGH_PRIORITY"]:
                    severity = AlertSeverityEnum.MEDIUM
                    if tier == "ATTENTION":
                        severity = AlertSeverityEnum.HIGH
                    elif tier == "HIGH_PRIORITY":
                        severity = AlertSeverityEnum.CRITICAL
                        
                    alerts_to_insert.append({
                        "project_id": row["project_id"],
                        "report_month": row["report_month"],
                        "alert_code": f"ESI_{tier}",
                        "severity": severity.name,
                        "alert_source": AlertSourceEnum.EXECUTION_SURVEILLANCE.name,
                        "message": f"Project shows {tier} execution stress. Dominant stressor: {row.get('dominant_stressor')}."
                    })
                    
        # 2. Process ML Risk Alerts
        if not risk_df.empty:
            for _, row in risk_df.iterrows():
                band = row.get("risk_band")
                if band in ["HIGH", "VERY_HIGH"]:
                    severity = AlertSeverityEnum.HIGH
                    if band == "VERY_HIGH":
                        severity = AlertSeverityEnum.CRITICAL
                        
                    alerts_to_insert.append({
                        "project_id": row["project_id"],
                        "report_month": row["report_month"],
                        "alert_code": f"ML_RISK_{band}",
                        "severity": severity.name,
                        "alert_source": AlertSourceEnum.ML_ENGINE.name,
                        "message": f"Model predicts {band} risk. Dominant component: {row.get('dominant_component')}."
                    })

        if not alerts_to_insert:
            return 0
            
        # Bulk Insert with ON CONFLICT DO NOTHING (if alert already exists for same month/code)
        stmt = insert(SystemAlert).values(alerts_to_insert)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['project_id', 'report_month', 'alert_code']
        )
        
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
