from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.enums import DominantComponentEnum, RiskBandEnum
from app.models.risk import MLRiskScore


class RiskRepository:
    """
    Data access layer for machine learning risk score records.
    Provides deterministic ranking queries and supported filters.
    """

    def __init__(self, session: Session):
        self.session = session

    def list_ranked_scores(
        self,
        page: int = 1,
        page_size: int = 20,
        risk_band: Optional[RiskBandEnum] = None,
        dominant_component: Optional[DominantComponentEnum] = None,
        report_month: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[List[MLRiskScore], int]:
        """
        Fetch stored ML risk scores ranked by selected_integrated_risk DESC,
        with deterministic tie-breakers on project_id ASC and report_month DESC.
        """
        query = self.session.query(MLRiskScore)

        if risk_band is not None:
            query = query.filter(MLRiskScore.risk_band == risk_band)
        if dominant_component is not None:
            query = query.filter(MLRiskScore.dominant_component == dominant_component)
        if report_month is not None and report_month.strip():
            query = query.filter(MLRiskScore.report_month == report_month.strip())
        if project_id is not None and project_id.strip():
            query = query.filter(MLRiskScore.project_id == project_id.strip())

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(
                MLRiskScore.selected_integrated_risk.desc(),
                MLRiskScore.project_id.asc(),
                MLRiskScore.report_month.desc(),
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total
