from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import (
    DominantComponentEnum,
    DominantStressorEnum,
    EsiTierEnum,
    RiskBandEnum,
)
from app.repositories.analytics import AnalyticsRepository
from app.repositories.risk import RiskRepository
from app.repositories.surveillance import SurveillanceRepository
from app.schemas.analytics import PortfolioSummaryResponse
from app.schemas.execution import PaginatedSurveillanceResponse
from app.schemas.risk import PaginatedRiskRankingsResponse
from app.services.analytics import AnalyticsService

router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency provider for AnalyticsService."""
    risk_repo = RiskRepository(db)
    surveillance_repo = SurveillanceRepository(db)
    analytics_repo = AnalyticsRepository(db)
    return AnalyticsService(risk_repo, surveillance_repo, analytics_repository=analytics_repo)


@router.get(
    "/risk-rankings",
    response_model=PaginatedRiskRankingsResponse,
    summary="Get Risk Rankings",
    description=(
        "Retrieve a paginated, ranked list of predictive ML risk scores. "
        "Ranked deterministically by selected_integrated_risk descending. "
        "Reads stored database records without triggering dynamic ML inference."
    ),
)
def get_risk_rankings(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    risk_band: Optional[RiskBandEnum] = Query(None, description="Filter by ML predicted risk band"),
    dominant_component: Optional[DominantComponentEnum] = Query(
        None, description="Filter by dominant risk component"
    ),
    report_month: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="Filter by reporting month epoch (YYYY-MM)",
    ),
    project_id: Optional[str] = Query(None, description="Filter by project identifier"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> PaginatedRiskRankingsResponse:
    return service.get_risk_rankings(
        page=page,
        page_size=page_size,
        risk_band=risk_band,
        dominant_component=dominant_component,
        report_month=report_month,
        project_id=project_id,
    )


@router.get(
    "/surveillance",
    response_model=PaginatedSurveillanceResponse,
    summary="Get Operational Surveillance Scores",
    description=(
        "Retrieve a paginated list of Pillar 2 execution stress surveillance scores. "
        "Ranked deterministically by execution_stress_index descending."
    ),
)
def get_surveillance(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    esi_tier: Optional[EsiTierEnum] = Query(None, description="Filter by Pillar 2 ESI tier"),
    dominant_stressor: Optional[DominantStressorEnum] = Query(
        None, description="Filter by dominant stressor"
    ),
    report_month: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="Filter by reporting month epoch (YYYY-MM)",
    ),
    project_id: Optional[str] = Query(None, description="Filter by project identifier"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> PaginatedSurveillanceResponse:
    return service.get_surveillance_scores(
        page=page,
        page_size=page_size,
        esi_tier=esi_tier,
        dominant_stressor=dominant_stressor,
        report_month=report_month,
        project_id=project_id,
    )


