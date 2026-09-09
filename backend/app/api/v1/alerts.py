from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.security import require_role
from app.models.enums import UserRoleEnum
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import AlertSeverityEnum, AlertSourceEnum, AlertStatusEnum
from app.repositories.alert import AlertRepository
from app.schemas.alert import PaginatedAlertsResponse
from app.services.alert import AlertService

router = APIRouter()


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    """Dependency provider for AlertService."""
    alert_repo = AlertRepository(db)
    return AlertService(alert_repo)


@router.get(
    "",
    response_model=PaginatedAlertsResponse,
    summary="List Operational Alerts",
    description=(
        "Retrieve a paginated list of operational alerts stored in system_alerts. "
        "Ordered deterministically by created_at DESC, report_month DESC. "
        "Returns stored alerts; does not generate alerts dynamically."
    ),
)
def list_alerts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[AlertStatusEnum] = Query(None, description="Filter by resolution status"),
    severity: Optional[AlertSeverityEnum] = Query(None, description="Filter by severity level"),
    alert_source: Optional[AlertSourceEnum] = Query(None, description="Filter by triggering alert source"),
    project_id: Optional[str] = Query(None, description="Filter by project identifier"),
    report_month: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="Filter by reporting month epoch (YYYY-MM)",
    ),
    service: AlertService = Depends(get_alert_service),
    current_user = Depends(require_role([UserRoleEnum.MOSPI_ADMIN, UserRoleEnum.NODAL_OFFICER])),
) -> PaginatedAlertsResponse:
    return service.get_alerts(
        page=page,
        page_size=page_size,
        status=status,
        severity=severity,
        alert_source=alert_source,
        project_id=project_id,
        report_month=report_month,
    )
