from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from app.schemas.common import BaseSchema


class ProjectSummary(BaseSchema):
    """
    High-level project summary for portfolio lists, search results, and rankings.
    """
    project_id: str = Field(..., description="Canonical 6-digit PAIMANA project identifier")
    project_name: Optional[str] = Field(None, description="Official project title")
    agency: str = Field(..., description="Implementing agency or CPSU (e.g. NHAI, NTPC)")
    state: str = Field(..., description="Location State or Multi-State")
    original_cost_crore: Optional[Decimal] = Field(None, description="Sanctioned capital cost in ₹ Crore")
    is_active: bool = Field(..., description="Active project status flag")


class ProjectDetail(ProjectSummary):
    """
    Full project detail including approval milestones, legacy cross-references, and timestamps.
    """
    legacy_ocms_code: Optional[str] = Field(None, description="Cross-referenced OCMS project code")
    approval_start_date: Optional[str] = Field(None, description="Sanction approval date (YYYY-MM)")
    original_completion_date: Optional[str] = Field(None, description="Original sanctioned DOC (YYYY-MM)")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record last update timestamp")


class PaginatedProjectsResponse(BaseSchema):
    """
    Standard paginated response wrapper for project listings.
    """
    items: List[ProjectSummary] = Field(..., description="List of projects on the current page")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total matching items across all pages")


from app.schemas.alert import SystemAlertResponse
from app.schemas.dossier import ProjectMonthlyDossierResponse
from app.schemas.execution import ExecutionStressScoreResponse
from app.schemas.risk import MLRiskScoreResponse
from app.schemas.snapshot import MonthlySnapshotResponse


class ProjectIntelligenceResponse(BaseSchema):
    """
    Unified project intelligence response.
    Aggregates the latest stored observations, ML risk predictions,
    operational surveillance metrics, alerts, and analytical dossier.
    """
    project: ProjectDetail = Field(..., description="Master project details")
    latest_snapshot: Optional[MonthlySnapshotResponse] = Field(None, description="Latest available monthly snapshot")
    latest_risk: Optional[MLRiskScoreResponse] = Field(None, description="Latest available ML risk prediction")
    latest_surveillance: Optional[ExecutionStressScoreResponse] = Field(None, description="Latest available ESI surveillance score")
    latest_alerts: List[SystemAlertResponse] = Field(default_factory=list, description="Latest operational alerts for this project")
    latest_dossier: Optional[ProjectMonthlyDossierResponse] = Field(None, description="Latest analytical monthly dossier record")

