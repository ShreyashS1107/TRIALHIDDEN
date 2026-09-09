from typing import Dict, List, Optional
from pydantic import Field
from decimal import Decimal

from app.schemas.common import BaseSchema

class BreakdownItem(BaseSchema):
    group_name: str = Field(..., description="Agency or State name")
    total_projects: int = Field(..., description="Total projects")
    total_cost_crore: Decimal = Field(..., description="Total cost crore")
    total_cost_escalation_crore: Decimal = Field(..., description="Total cost escalation")
    mean_progress_percent: Decimal = Field(..., description="Average physical progress %")
    mean_integrated_risk: Decimal = Field(..., description="Mean integrated risk")
    mean_execution_stress_index: Decimal = Field(..., description="Mean execution stress index")
    high_risk_count: int = Field(..., description="Number of VERY_HIGH or HIGH risk projects")
    high_execution_stress_count: int = Field(..., description="Number of HIGH_PRIORITY or ATTENTION stress projects")

class PortfolioBreakdownResponse(BaseSchema):
    report_month: str = Field(..., description="Report month (YYYY-MM)")
    breakdown: List[BreakdownItem] = Field(..., description="Breakdown list")

class EpochsResponse(BaseSchema):
    total_epochs: int = Field(..., description="Total epochs available")
    available_epochs: List[str] = Field(..., description="List of epochs in YYYY-MM format")
