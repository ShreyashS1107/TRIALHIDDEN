from typing import Optional
from fastapi import HTTPException, status

from app.repositories.project import ProjectRepository
from app.schemas.alert import SystemAlertResponse
from app.schemas.dossier import ProjectMonthlyDossierResponse
from app.schemas.execution import ExecutionStressScoreResponse
from app.schemas.project import (
    PaginatedProjectsResponse,
    ProjectDetail,
    ProjectIntelligenceResponse,
    ProjectSummary,
)
from app.schemas.risk import MLRiskScoreResponse
from app.schemas.snapshot import MonthlySnapshotResponse, MonthlySnapshotSeriesResponse


class ProjectService:
    """
    Business logic and orchestration service for projects.
    Handles entity validation, HTTP exception mapping, and response schema transformations.
    """

    def __init__(self, repository: ProjectRepository):
        self.repository = repository

    def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        agency: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedProjectsResponse:
        """Fetch a paginated, filtered list of projects."""
        items, total = self.repository.list_projects(
            page=page,
            page_size=page_size,
            agency=agency,
            state=state,
            is_active=is_active,
        )
        return PaginatedProjectsResponse(
            items=[ProjectSummary.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_project_detail(self, project_id: str) -> ProjectDetail:
        """Fetch comprehensive details for a single project by ID."""
        project = self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found.",
            )
        return ProjectDetail.model_validate(project)

    def get_project_snapshots(self, project_id: str) -> MonthlySnapshotSeriesResponse:
        """
        Fetch chronological monthly snapshots for a project.
        Raises 404 if the project does not exist; returns empty series if project has no snapshots.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found.",
            )

        snapshots = self.repository.get_snapshots_for_project(project_id)
        return MonthlySnapshotSeriesResponse(
            project_id=project_id,
            total_snapshots=len(snapshots),
            snapshots=[MonthlySnapshotResponse.model_validate(s) for s in snapshots],
        )

    def get_project_dossier(
        self,
        project_id: str,
        report_month: Optional[str] = None,
    ) -> ProjectMonthlyDossierResponse:
        """
        Fetch analytical dossier record from v_project_monthly_dossier.
        Returns the latest month if report_month is omitted.
        Raises 404 if the project or the specific dossier record does not exist.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found.",
            )

        dossier = self.repository.get_dossier_for_project(
            project_id=project_id,
            report_month=report_month,
        )
        if not dossier:
            if report_month:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dossier record for project '{project_id}' in month '{report_month}' not found.",
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No dossier records found for project '{project_id}'.",
            )

        return ProjectMonthlyDossierResponse.model_validate(dossier)

    def get_project_intelligence(self, project_id: str) -> ProjectIntelligenceResponse:
        """
        Aggregate stored intelligence for a single project across all domains:
        master details, latest snapshot, latest ML risk, latest surveillance score,
        latest alerts, and latest analytical dossier.
        Raises HTTP 404 if project does not exist.
        Returns null/empty collections for any component without stored records.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found.",
            )

        snapshot = self.repository.get_latest_snapshot(project_id)
        risk = self.repository.get_latest_risk(project_id)
        surveillance = self.repository.get_latest_surveillance(project_id)
        alerts = self.repository.get_latest_alerts(project_id)
        dossier = self.repository.get_dossier_for_project(project_id)

        return ProjectIntelligenceResponse(
            project=ProjectDetail.model_validate(project),
            latest_snapshot=MonthlySnapshotResponse.model_validate(snapshot) if snapshot else None,
            latest_risk=MLRiskScoreResponse.model_validate(risk) if risk else None,
            latest_surveillance=ExecutionStressScoreResponse.model_validate(surveillance) if surveillance else None,
            latest_alerts=[SystemAlertResponse.model_validate(a) for a in alerts],
            latest_dossier=ProjectMonthlyDossierResponse.model_validate(dossier) if dossier else None,
        )
