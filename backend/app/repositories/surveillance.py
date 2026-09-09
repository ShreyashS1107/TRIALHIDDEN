from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.enums import DominantStressorEnum, EsiTierEnum
from app.models.execution import ExecutionStressScore


class SurveillanceRepository:
    """
    Data access layer for Pillar 2 Execution Stress Index surveillance records.
    Provides deterministic queries ranked by execution_stress_index DESC.
    """

    def __init__(self, session: Session):
        self.session = session

    def list_surveillance_scores(
        self,
        page: int = 1,
        page_size: int = 20,
        esi_tier: Optional[EsiTierEnum] = None,
        dominant_stressor: Optional[DominantStressorEnum] = None,
        report_month: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[List[ExecutionStressScore], int]:
        """
        Fetch stored execution stress surveillance records ranked by execution_stress_index DESC,
        with deterministic tie-breakers on project_id ASC and report_month DESC.
        """
        query = self.session.query(ExecutionStressScore)

        if esi_tier is not None:
            query = query.filter(ExecutionStressScore.esi_tier == esi_tier)
        if dominant_stressor is not None:
            query = query.filter(ExecutionStressScore.dominant_stressor == dominant_stressor)
        if report_month is not None and report_month.strip():
            query = query.filter(ExecutionStressScore.report_month == report_month.strip())
        if project_id is not None and project_id.strip():
            query = query.filter(ExecutionStressScore.project_id == project_id.strip())

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(
                ExecutionStressScore.execution_stress_index.desc(),
                ExecutionStressScore.project_id.asc(),
                ExecutionStressScore.report_month.desc(),
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total
