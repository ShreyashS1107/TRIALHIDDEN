from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import SystemAlert
from app.models.dossier import ProjectMonthlyDossier
from app.models.execution import ExecutionStressScore
from app.models.project import MonthlySnapshot, Project
from app.models.risk import MLRiskScore


class ProjectRepository:
    """
    Data access layer for projects, monthly snapshots, and dossier view.
    Handles pure database queries, filtering, sorting, and pagination.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Fetch a single project by its primary key."""
        return (
            self.session.query(Project)
            .filter(Project.project_id == project_id)
            .first()
        )

    def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        agency: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Project], int]:
        """
        List projects with optional filtering on agency, state, and active status.
        Uses deterministic ordering by project_id ASC for stable pagination.
        """
        query = self.session.query(Project)

        if agency is not None and agency.strip():
            query = query.filter(func.lower(Project.agency) == agency.strip().lower())
        if state is not None and state.strip():
            query = query.filter(func.lower(Project.state) == state.strip().lower())
        if is_active is not None:
            query = query.filter(Project.is_active == is_active)

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(Project.project_id.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_snapshots_for_project(self, project_id: str) -> List[MonthlySnapshot]:
        """
        Fetch all longitudinal monthly snapshots for a given project,
        strictly ordered chronologically by report_month ASC.
        """
        return (
            self.session.query(MonthlySnapshot)
            .filter(MonthlySnapshot.project_id == project_id)
            .order_by(MonthlySnapshot.report_month.asc())
            .all()
        )

    def get_dossier_for_project(
        self,
        project_id: str,
        report_month: Optional[str] = None,
    ) -> Optional[ProjectMonthlyDossier]:
        """
        Fetch a project's monthly dossier row from the read-only v_project_monthly_dossier view.
        If report_month is specified, retrieves that specific month.
        Otherwise, returns the latest available month (report_month DESC).
        """
        query = self.session.query(ProjectMonthlyDossier).filter(
            ProjectMonthlyDossier.project_id == project_id
        )
        if report_month is not None and report_month.strip():
            query = query.filter(ProjectMonthlyDossier.report_month == report_month.strip())

        return query.order_by(ProjectMonthlyDossier.report_month.desc()).first()

    def get_latest_snapshot(self, project_id: str) -> Optional[MonthlySnapshot]:
        """Fetch the latest available monthly snapshot for a project."""
        return (
            self.session.query(MonthlySnapshot)
            .filter(MonthlySnapshot.project_id == project_id)
            .order_by(MonthlySnapshot.report_month.desc())
            .first()
        )

    def get_latest_risk(self, project_id: str) -> Optional[MLRiskScore]:
        """Fetch the latest available ML risk score for a project."""
        return (
            self.session.query(MLRiskScore)
            .filter(MLRiskScore.project_id == project_id)
            .order_by(MLRiskScore.report_month.desc())
            .first()
        )

    def get_latest_surveillance(self, project_id: str) -> Optional[ExecutionStressScore]:
        """Fetch the latest available execution stress surveillance score for a project."""
        return (
            self.session.query(ExecutionStressScore)
            .filter(ExecutionStressScore.project_id == project_id)
            .order_by(ExecutionStressScore.report_month.desc())
            .first()
        )

    def get_latest_alerts(self, project_id: str, limit: int = 20) -> List[SystemAlert]:
        """
        Fetch the most recent system alerts stored for a project.
        Ordered deterministically by created_at DESC, report_month DESC, alert_id ASC.
        """
        return (
            self.session.query(SystemAlert)
            .filter(SystemAlert.project_id == project_id)
            .order_by(
                SystemAlert.created_at.desc(),
                SystemAlert.report_month.desc(),
                SystemAlert.alert_id.asc(),
            )
            .limit(limit)
            .all()
        )
