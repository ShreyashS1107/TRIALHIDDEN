from typing import Optional

from app.models.enums import AlertSeverityEnum, AlertSourceEnum, AlertStatusEnum
from app.repositories.alert import AlertRepository
from app.schemas.alert import PaginatedAlertsResponse, SystemAlertResponse


class AlertService:
    """
    Business orchestration service for operational system alerts.
    Reads stored database records from system_alerts without dynamic generation.
    """

    def __init__(self, alert_repository: AlertRepository):
        self.alert_repository = alert_repository

    def get_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[AlertStatusEnum] = None,
        severity: Optional[AlertSeverityEnum] = None,
        alert_source: Optional[AlertSourceEnum] = None,
        project_id: Optional[str] = None,
        report_month: Optional[str] = None,
    ) -> PaginatedAlertsResponse:
        """Fetch paginated system alerts with optional filters."""
        items, total = self.alert_repository.list_alerts(
            page=page,
            page_size=page_size,
            status=status,
            severity=severity,
            alert_source=alert_source,
            project_id=project_id,
            report_month=report_month,
        )
        return PaginatedAlertsResponse(
            items=[SystemAlertResponse.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )
