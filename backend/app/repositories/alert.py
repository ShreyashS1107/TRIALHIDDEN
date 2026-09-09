from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.alert import SystemAlert
from app.models.enums import AlertSeverityEnum, AlertSourceEnum, AlertStatusEnum


class AlertRepository:
    """
    Data access layer for operational system alerts stored in system_alerts.
    Provides read-only queries, status/severity/source filtering, and pagination.
    """

    def __init__(self, session: Session):
        self.session = session

    def list_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[AlertStatusEnum] = None,
        severity: Optional[AlertSeverityEnum] = None,
        alert_source: Optional[AlertSourceEnum] = None,
        project_id: Optional[str] = None,
        report_month: Optional[str] = None,
    ) -> Tuple[List[SystemAlert], int]:
        """
        Fetch stored operational system alerts ordered by created_at DESC, report_month DESC, alert_id ASC.
        """
        query = self.session.query(SystemAlert)

        if status is not None:
            query = query.filter(SystemAlert.status == status)
        if severity is not None:
            query = query.filter(SystemAlert.severity == severity)
        if alert_source is not None:
            query = query.filter(SystemAlert.alert_source == alert_source)
        if project_id is not None and project_id.strip():
            query = query.filter(SystemAlert.project_id == project_id.strip())
        if report_month is not None and report_month.strip():
            query = query.filter(SystemAlert.report_month == report_month.strip())

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(
                SystemAlert.created_at.desc(),
                SystemAlert.report_month.desc(),
                SystemAlert.alert_id.asc(),
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total
