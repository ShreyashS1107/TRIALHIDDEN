from typing import Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.project import ProjectRepository
from app.schemas.dossier import ProjectMonthlyDossierResponse
from app.schemas.project import (
    PaginatedProjectsResponse,
    ProjectDetail,
    ProjectIntelligenceResponse,
)
from app.schemas.snapshot import MonthlySnapshotSeriesResponse
from app.services.project import ProjectService

router = APIRouter()


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """Dependency provider for ProjectService."""
    repository = ProjectRepository(db)
    return ProjectService(repository)


@router.get(
    "",
    response_model=PaginatedProjectsResponse,
    summary="List Projects",
    description="Retrieve a paginated, filterable list of infrastructure projects.",
)
def list_projects(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    agency: Optional[str] = Query(None, description="Filter by implementing agency (e.g. NHAI, NTPC)"),
    state: Optional[str] = Query(None, description="Filter by location state"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: ProjectService = Depends(get_project_service),
) -> PaginatedProjectsResponse:
    return service.list_projects(
        page=page,
        page_size=page_size,
        agency=agency,
        state=state,
        is_active=is_active,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetail,
    summary="Get Project Detail",
    description="Retrieve detailed information for a single project by its primary key identifier.",
)
def get_project_detail(
    project_id: str = Path(..., description="Canonical project ID (e.g. '105236')"),
    service: ProjectService = Depends(get_project_service),
) -> ProjectDetail:
    return service.get_project_detail(project_id)


@router.get(
    "/{project_id}/snapshots",
    response_model=MonthlySnapshotSeriesResponse,
    summary="Get Project Snapshots",
    description="Retrieve the chronological monthly snapshot time-series for a project.",
)
def get_project_snapshots(
    project_id: str = Path(..., description="Canonical project ID"),
    service: ProjectService = Depends(get_project_service),
) -> MonthlySnapshotSeriesResponse:
    return service.get_project_snapshots(project_id)


@router.get(
    "/{project_id}/dossier",
    response_model=ProjectMonthlyDossierResponse,
    summary="Get Project Dossier",
    description=(
        "Retrieve the analytical monthly dossier from v_project_monthly_dossier. "
        "Returns the latest month's dossier by default, or a specific month if report_month is supplied."
    ),
)
def get_project_dossier(
    project_id: str = Path(..., description="Canonical project ID"),
    report_month: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="Specific reporting month epoch (YYYY-MM). If omitted, returns latest available.",
    ),
    service: ProjectService = Depends(get_project_service),
) -> ProjectMonthlyDossierResponse:
    return service.get_project_dossier(project_id, report_month=report_month)


@router.get(
    "/{project_id}/intelligence",
    response_model=ProjectIntelligenceResponse,
    summary="Get Project Intelligence Dossier",
    description=(
        "Retrieve aggregated multi-domain intelligence for a single project. "
        "Returns the latest stored observation snapshot, latest ML risk prediction, "
        "latest ESI operational surveillance score, recent alerts, and latest analytical dossier. "
        "Missing components return null or empty list without failing the request."
    ),
)
def get_project_intelligence(
    project_id: str = Path(..., description="Canonical project ID"),
    service: ProjectService = Depends(get_project_service),
) -> ProjectIntelligenceResponse:
    return service.get_project_intelligence(project_id)
