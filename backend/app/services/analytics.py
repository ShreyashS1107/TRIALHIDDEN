from typing import Optional

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
from app.schemas.execution import (
    ExecutionStressScoreResponse,
    PaginatedSurveillanceResponse,
)
from app.schemas.risk import (
    MLRiskScoreResponse,
    PaginatedRiskRankingsResponse,
)


class AnalyticsService:
    """
    Business orchestration service for predictive ML risk rankings,
    Pillar 2 operational surveillance analytics, and portfolio summary intelligence.
    Reads stored database records without triggering on-the-fly ML inference.
    """

    def __init__(
        self,
        risk_repository: RiskRepository,
        surveillance_repository: SurveillanceRepository,
        analytics_repository: Optional[AnalyticsRepository] = None,
    ):
        self.risk_repository = risk_repository
        self.surveillance_repository = surveillance_repository
        self.analytics_repository = analytics_repository or AnalyticsRepository(risk_repository.session)

    def get_risk_rankings(
        self,
        page: int = 1,
        page_size: int = 20,
        risk_band: Optional[RiskBandEnum] = None,
        dominant_component: Optional[DominantComponentEnum] = None,
        report_month: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> PaginatedRiskRankingsResponse:
        """Fetch ranked ML risk scores."""
        items, total = self.risk_repository.list_ranked_scores(
            page=page,
            page_size=page_size,
            risk_band=risk_band,
            dominant_component=dominant_component,
            report_month=report_month,
            project_id=project_id,
        )
        return PaginatedRiskRankingsResponse(
            items=[MLRiskScoreResponse.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_surveillance_scores(
        self,
        page: int = 1,
        page_size: int = 20,
        esi_tier: Optional[EsiTierEnum] = None,
        dominant_stressor: Optional[DominantStressorEnum] = None,
        report_month: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> PaginatedSurveillanceResponse:
        """Fetch ranked Pillar 2 execution stress surveillance records."""
        items, total = self.surveillance_repository.list_surveillance_scores(
            page=page,
            page_size=page_size,
            esi_tier=esi_tier,
            dominant_stressor=dominant_stressor,
            report_month=report_month,
            project_id=project_id,
        )
        return PaginatedSurveillanceResponse(
            items=[ExecutionStressScoreResponse.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_portfolio_summary(
        self,
        report_month: Optional[str] = None,
    ) -> PortfolioSummaryResponse:
        """
        Fetch portfolio-level overview and risk/surveillance intelligence summary.
        Reads precomputed stored aggregates.
        """
        summary_data = self.analytics_repository.get_portfolio_summary(report_month=report_month)
        return PortfolioSummaryResponse.model_validate(summary_data)
