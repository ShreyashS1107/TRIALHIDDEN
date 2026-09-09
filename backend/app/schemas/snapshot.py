from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import Field

from app.schemas.common import BaseSchema


class MonthlySnapshotResponse(BaseSchema):
    """
    Single monthly longitudinal observation (Layer A Raw Fact).
    """
    snapshot_id: uuid.UUID = Field(..., description="Unique snapshot UUID")
    project_id: str = Field(..., description="Project identifier")
    report_month: str = Field(..., description="Reporting month epoch (YYYY-MM)")
    revised_completion_date: Optional[str] = Field(None, description="Anticipated DOC in YYYY-MM")
    revised_cost_crore: Optional[Decimal] = Field(None, description="Anticipated cost in ₹ Crore")
    cumulative_expenditure_crore: Optional[Decimal] = Field(None, description="Cumulative expenditure to date in ₹ Crore")
    physical_progress_percent: Optional[Decimal] = Field(None, description="Physical progress percentage [0.00, 100.00]")
    source_file: str = Field(..., description="Source Flash Report document name")
    source_table: str = Field(..., description="Source table in Flash Report")
    created_at: Optional[datetime] = Field(None, description="Ingestion timestamp")


class MonthlySnapshotSeriesResponse(BaseSchema):
    """
    Chronological series of monthly snapshots for a given project.
    """
    project_id: str = Field(..., description="Project identifier")
    total_snapshots: int = Field(..., description="Total count of snapshots in series")
    snapshots: List[MonthlySnapshotResponse] = Field(default_factory=list, description="Ordered list of monthly snapshots")
