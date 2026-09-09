from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import Field

from app.models.enums import DominantComponentEnum, RiskBandEnum
from app.schemas.common import BaseSchema


class MLRiskScoreResponse(BaseSchema):
    """
    Machine learning multi-dimensional risk prediction score response (Layer C).
    """
    score_id: uuid.UUID = Field(..., description="Unique score UUID")
    project_id: str = Field(..., description="Project identifier")
    report_month: str = Field(..., description="Scored reporting month epoch (YYYY-MM)")
    schedule_delay_risk: Decimal = Field(..., description="Calibrated probability of schedule delay [0.0000, 1.0000]")
    cost_overrun_risk: Decimal = Field(..., description="Continuous model score for cost overrun [0.0000, 1.0000]")
    schedule_revision_risk: Decimal = Field(..., description="Score indicating likelihood of administrative schedule revision [0.0000, 1.0000]")
    selected_integrated_risk: Decimal = Field(..., description="Weighted composite risk index [0.0000, 1.0000]")
    risk_band: RiskBandEnum = Field(..., description="Risk tier classification: LOW, MODERATE, HIGH, VERY_HIGH")
    dominant_component: DominantComponentEnum = Field(..., description="Primary risk driver")
    schedule_contribution: Decimal = Field(..., description="Schedule delay component weighted contribution")
    cost_contribution: Decimal = Field(..., description="Cost overrun component weighted contribution")
    schedule_revision_contribution: Decimal = Field(..., description="Schedule revision component weighted contribution")
    model_version: str = Field(..., description="Predictive model version tag")
    scored_at: Optional[datetime] = Field(None, description="Timestamp when score was computed")


class PaginatedRiskRankingsResponse(BaseSchema):
    """
    Standard paginated response wrapper for risk ranking records.
    """
    items: List[MLRiskScoreResponse] = Field(..., description="List of risk score ranking records")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total count of matching risk records")
