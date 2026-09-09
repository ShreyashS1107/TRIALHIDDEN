from typing import Any, Dict, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import SystemAlert
from app.models.execution import ExecutionStressScore
from app.models.project import MonthlySnapshot, Project
from app.models.risk import MLRiskScore


class AnalyticsRepository:
    """
    Data access layer for high-level portfolio intelligence metrics.
    Performs deterministic, read-only aggregation queries without full table loads.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_portfolio_summary(self, report_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute portfolio-level intelligence metrics.
        - total_projects: count of all registered projects
        - active_projects: count of currently active projects (is_active == True)
        - scored_projects: count of distinct projects scored in the target month
        - risk_band_distribution: distribution of projects by ML risk band
        - esi_tier_distribution: distribution of projects by Pillar 2 ESI tier
        - alert_counts_by_severity: breakdown of alerts by severity
        - alert_counts_by_status: breakdown of alerts by status
        - total_alerts: total system alerts
        - latest_report_month: target intelligence reporting month
        - latest_snapshot_month: latest available monthly snapshot epoch
        """
        total_projects = self.session.query(func.count(Project.project_id)).scalar() or 0
        active_projects = (
            self.session.query(func.count(Project.project_id))
            .filter(Project.is_active == True)
            .scalar()
            or 0
        )

        latest_snapshot_month = (
            self.session.query(func.max(MonthlySnapshot.report_month)).scalar()
        )

        # Determine target intelligence report month dynamically if not specified
        if report_month is not None and report_month.strip():
            target_month = report_month.strip()
        else:
            target_month = (
                self.session.query(func.max(MLRiskScore.report_month)).scalar()
            )

        # Scored projects count in the target epoch
        scored_projects = 0
        if target_month:
            scored_projects = (
                self.session.query(func.count(func.distinct(MLRiskScore.project_id)))
                .filter(MLRiskScore.report_month == target_month)
                .scalar()
                or 0
            )

        # Risk band distribution for target epoch
        risk_dist: Dict[str, int] = {
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "VERY_HIGH": 0,
        }
        if target_month:
            risk_rows = (
                self.session.query(MLRiskScore.risk_band, func.count(MLRiskScore.project_id))
                .filter(MLRiskScore.report_month == target_month)
                .group_by(MLRiskScore.risk_band)
                .all()
            )
            for row in risk_rows:
                key = row[0].value if hasattr(row[0], "value") else str(row[0])
                risk_dist[key] = row[1]

        # ESI tier distribution for target epoch
        esi_dist: Dict[str, int] = {
            "NOMINAL": 0,
            "WATCH": 0,
            "ATTENTION": 0,
            "HIGH_PRIORITY": 0,
        }
        if target_month:
            esi_rows = (
                self.session.query(ExecutionStressScore.esi_tier, func.count(ExecutionStressScore.project_id))
                .filter(ExecutionStressScore.report_month == target_month)
                .group_by(ExecutionStressScore.esi_tier)
                .all()
            )
            for row in esi_rows:
                key = row[0].value if hasattr(row[0], "value") else str(row[0])
                esi_dist[key] = row[1]

        # Alert statistics
        total_alerts = self.session.query(func.count(SystemAlert.alert_id)).scalar() or 0

        sev_dist: Dict[str, int] = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }
        sev_rows = (
            self.session.query(SystemAlert.severity, func.count(SystemAlert.alert_id))
            .group_by(SystemAlert.severity)
            .all()
        )
        for row in sev_rows:
            key = row[0].value if hasattr(row[0], "value") else str(row[0])
            sev_dist[key] = row[1]

        status_dist: Dict[str, int] = {
            "ACTIVE": 0,
            "ACKNOWLEDGED": 0,
            "RESOLVED": 0,
        }
        status_rows = (
            self.session.query(SystemAlert.status, func.count(SystemAlert.alert_id))
            .group_by(SystemAlert.status)
            .all()
        )
        for row in status_rows:
            key = row[0].value if hasattr(row[0], "value") else str(row[0])
            status_dist[key] = row[1]

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "scored_projects": scored_projects,
            "risk_band_distribution": risk_dist,
            "esi_tier_distribution": esi_dist,
            "alert_counts_by_severity": sev_dist,
            "alert_counts_by_status": status_dist,
            "total_alerts": total_alerts,
            "latest_report_month": target_month,
            "latest_snapshot_month": latest_snapshot_month,
        }
