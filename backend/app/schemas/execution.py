from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from app.models.enums import DominantStressorEnum, EsiTierEnum, PrescriptiveActionEnum
from app.schemas.common import BaseSchema


class ExecutionStressScoreResponse(BaseSchema):
    """
    Pillar 2 operational execution surveillance and Execution Stress Index (ESI) response.
    """
    project_id: str = Field(..., description="Project identifier")
    report_month: str = Field(..., description="Evaluation month epoch (YYYY-MM)")
    s_stag: Decimal = Field(..., description="Stagnation stress score [0.0000, 1.0000]")
    s_vel: Decimal = Field(..., description="Progress velocity stress score [0.0000, 1.0000]")
    s_div: Decimal = Field(..., description="Expenditure divergence stress score [0.0000, 1.0000]")
    s_sched: Decimal = Field(..., description="Schedule slippage debt stress score [0.0000, 1.0000]")
    s_rep: Decimal = Field(..., description="Reporting friction stress score [0.0000, 1.0000]")
    flag_stag: int = Field(..., description="Stagnation indicator flag (0 or 1)")
    flag_vel: int = Field(..., description="Velocity collapse indicator flag (0 or 1)")
    flag_div: int = Field(..., description="Expenditure divergence indicator flag (0 or 1)")
    flag_sched: int = Field(..., description="Schedule slippage debt indicator flag (0 or 1)")
    flag_rep: int = Field(..., description="Reporting friction indicator flag (0 or 1)")
    total_stress_flags: int = Field(..., description="Count of triggered stress flags [0 to 5]")
    execution_stress_index: Decimal = Field(..., description="Composite Execution Stress Index [0.0000, 1.0000]")
    esi_tier: EsiTierEnum = Field(..., description="Execution stress tier: NOMINAL, WATCH, ATTENTION, HIGH_PRIORITY")
    dominant_stressor: DominantStressorEnum = Field(..., description="Leading operational stress dimension")
    suggested_action: PrescriptiveActionEnum = Field(..., description="Prescriptive governance action directive")
    execution_index_version: str = Field(..., description="Surveillance index version tag")
    evaluated_at: Optional[datetime] = Field(None, description="Surveillance evaluation timestamp")


class PaginatedSurveillanceResponse(BaseSchema):
    """
    Standard paginated response wrapper for execution stress surveillance records.
    """
    items: List[ExecutionStressScoreResponse] = Field(..., description="List of surveillance records")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total count of matching surveillance records")
