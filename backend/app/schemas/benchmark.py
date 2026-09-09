from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema


class HistoricalBenchmarkResponse(BaseSchema):
    """
    Response schema for an OCMS historical benchmark record.
    """
    benchmark_id: UUID = Field(..., description="Unique benchmark identifier")
    
    # Legacy fields
    project_id: Optional[str] = Field(None, description="Linked project ID (if applicable)")
    legacy_ocms_code: Optional[str] = Field(None, description="Legacy OCMS code")
    agency: Optional[str] = Field(None, description="Agency name (legacy)")
    sector: Optional[str] = Field(None, description="Sector name (legacy)")
    historical_observation_months: Optional[int] = Field(None, description="Months observed")
    historical_mean_cost_escalation_pct: Optional[Decimal] = Field(None, description="Historical cost escalation %")
    historical_mean_delay_months: Optional[Decimal] = Field(None, description="Historical delay months")
    historical_completion_rate_pct: Optional[Decimal] = Field(None, description="Historical completion rate")
    
    # Core CSV fields
    benchmark_level: str = Field(..., description="Level of aggregation (e.g. Agency x Year)")
    entity_name: str = Field(..., description="Name of the aggregated entity")
    year: str = Field(..., description="Year or period string")
    total_completed_projects: Optional[int] = Field(None, description="Total projects completed")
    projects_with_schedule_outcome: Optional[int] = Field(None, description="Projects with known schedule outcome")
    delay_count: Optional[int] = Field(None, description="Number of delayed projects")
    delay_rate_pct: Optional[Decimal] = Field(None, description="Percentage of delayed projects")
    mean_delay_months: Optional[Decimal] = Field(None, description="Mean delay in months")
    median_delay_months: Optional[Decimal] = Field(None, description="Median delay in months")
    projects_with_cost_outcome: Optional[int] = Field(None, description="Projects with known cost outcome")
    cost_overrun_count: Optional[int] = Field(None, description="Number of projects with cost overrun")
    cost_overrun_rate_pct: Optional[Decimal] = Field(None, description="Percentage of projects with cost overrun")
    mean_cost_overrun_pct: Optional[Decimal] = Field(None, description="Mean cost overrun percentage")
    median_cost_overrun_pct: Optional[Decimal] = Field(None, description="Median cost overrun percentage")
    total_original_cost_crore: Optional[Decimal] = Field(None, description="Total original cost in crore")
    total_cumulative_expenditure_crore: Optional[Decimal] = Field(None, description="Total cumulative expenditure in crore")
    
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")


class PaginatedHistoricalBenchmarksResponse(BaseSchema):
    """
    Paginated response for historical benchmarks.
    """
    items: List[HistoricalBenchmarkResponse] = Field(..., description="List of benchmarks on the current page")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total matching items across all pages")
