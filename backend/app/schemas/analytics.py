from typing import Dict, Optional
from pydantic import Field

from app.schemas.common import BaseSchema


class PortfolioSummaryResponse(BaseSchema):
    """
    High-level portfolio overview and operational intelligence summary.
    Aggregates project counts, latest risk distributions, surveillance stress tiers,
    alert statistics, and latest available reporting epochs.
    """
    total_projects: int = Field(..., description="Total infrastructure projects in portfolio")
    active_projects: int = Field(..., description="Currently active projects")
    scored_projects: int = Field(..., description="Projects with computed risk intelligence in the evaluated epoch")
    risk_band_distribution: Dict[str, int] = Field(..., description="Project count distribution by risk band (LOW, MODERATE, HIGH, VERY_HIGH)")
    esi_tier_distribution: Dict[str, int] = Field(..., description="Project count distribution by ESI tier (NOMINAL, WATCH, ATTENTION, HIGH_PRIORITY)")
    alert_counts_by_severity: Dict[str, int] = Field(..., description="Alert count by severity (LOW, MEDIUM, HIGH, CRITICAL)")
    alert_counts_by_status: Dict[str, int] = Field(..., description="Alert count by resolution status (ACTIVE, ACKNOWLEDGED, RESOLVED)")
    total_alerts: int = Field(..., description="Total system alerts recorded")
    latest_report_month: Optional[str] = Field(None, description="Latest available intelligence reporting month (YYYY-MM)")
    latest_snapshot_month: Optional[str] = Field(None, description="Latest available raw snapshot month (YYYY-MM)")
