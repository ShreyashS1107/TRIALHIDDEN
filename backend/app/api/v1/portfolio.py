from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database.session import get_db
from app.core.cache import cached
from app.schemas.analytics import PortfolioSummaryResponse
from app.schemas.portfolio import PortfolioBreakdownResponse, BreakdownItem
from app.services.analytics import AnalyticsService
from app.repositories.analytics import AnalyticsRepository
from app.repositories.risk import RiskRepository
from app.repositories.surveillance import SurveillanceRepository

router = APIRouter()

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    risk_repo = RiskRepository(db)
    surveillance_repo = SurveillanceRepository(db)
    analytics_repo = AnalyticsRepository(db)
    return AnalyticsService(risk_repo, surveillance_repo, analytics_repository=analytics_repo)

@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get Portfolio Intelligence Summary",
    description="Retrieve portfolio-level metrics."
)
@cached(prefix="portfolio:summary", ttl=3600)
def get_portfolio_summary(
    report_month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$", description="Report month (YYYY-MM)"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> PortfolioSummaryResponse:
    return service.get_portfolio_summary(report_month=report_month)

@router.get(
    "/breakdown/agency",
    response_model=PortfolioBreakdownResponse,
    summary="Agency Breakdown",
    description="Aggregated risk, execution stress, project counts grouped by agency."
)
@cached(prefix="portfolio:breakdown:agency", ttl=3600)
def get_agency_breakdown(
    report_month: str = Query("2026-03", description="Report month (YYYY-MM)"),
    limit: int = Query(20, description="Limit results"),
    db: Session = Depends(get_db)
) -> PortfolioBreakdownResponse:
    # Query logic inline for simplicity since we can't create complex repositories easily right now
    from sqlalchemy import text
    sql = text("""
        SELECT 
            r.agency as group_name,
            COUNT(r.project_id) as total_projects,
            COUNT(CASE WHEN r.revised_completion_date IS NOT NULL THEN 1 END) as active_projects,
            COALESCE(SUM(r.revised_cost_crore), 0) as total_cost_crore,
            COALESCE(SUM(r.revised_cost_crore - r.original_cost_crore), 0) as total_cost_escalation_crore,
            COALESCE(AVG(r.physical_progress_percent), 0) as mean_progress_percent,
            COALESCE(AVG(m.selected_integrated_risk), 0) as mean_integrated_risk,
            COALESCE(AVG(e.execution_stress_index), 0) as mean_execution_stress_index,
            COUNT(CASE WHEN m.risk_band IN ('HIGH', 'VERY_HIGH') THEN 1 END) as high_risk_count,
            COUNT(CASE WHEN e.esi_tier IN ('ATTENTION', 'HIGH_PRIORITY') THEN 1 END) as high_execution_stress_count
        FROM v_project_monthly_dossier r
        LEFT JOIN ml_risk_scores m ON r.project_id = m.project_id AND r.report_month = m.report_month
        LEFT JOIN execution_stress_scores e ON r.project_id = e.project_id AND r.report_month = e.report_month
        WHERE r.report_month = :report_month
        GROUP BY r.agency
        ORDER BY total_cost_escalation_crore DESC
        LIMIT :limit
    """)
    result = db.execute(sql, {"report_month": report_month, "limit": limit}).fetchall()
    
    breakdown = []
    for row in result:
        breakdown.append(BreakdownItem(
            group_name=row.group_name or "Unknown",
            total_projects=row.total_projects,
            active_projects=row.active_projects,
            total_cost_crore=Decimal(str(row.total_cost_crore)),
            total_cost_escalation_crore=Decimal(str(row.total_cost_escalation_crore)),
            mean_progress_percent=Decimal(str(row.mean_progress_percent)),
            mean_integrated_risk=Decimal(str(row.mean_integrated_risk)),
            mean_execution_stress_index=Decimal(str(row.mean_execution_stress_index)),
            high_risk_count=row.high_risk_count,
            high_execution_stress_count=row.high_execution_stress_count
        ))
        
    return PortfolioBreakdownResponse(report_month=report_month, breakdown=breakdown)

@router.get(
    "/breakdown/state",
    response_model=PortfolioBreakdownResponse,
    summary="State Breakdown",
    description="Aggregated risk, execution stress, project counts grouped by state."
)
@cached(prefix="portfolio:breakdown:state", ttl=3600)
def get_state_breakdown(
    report_month: str = Query("2026-03", description="Report month (YYYY-MM)"),
    limit: int = Query(20, description="Limit results"),
    db: Session = Depends(get_db)
) -> PortfolioBreakdownResponse:
    from sqlalchemy import text
    sql = text("""
        SELECT 
            r.state as group_name,
            COUNT(r.project_id) as total_projects,
            COUNT(CASE WHEN r.revised_completion_date IS NOT NULL THEN 1 END) as active_projects,
            COALESCE(SUM(r.revised_cost_crore), 0) as total_cost_crore,
            COALESCE(SUM(r.revised_cost_crore - r.original_cost_crore), 0) as total_cost_escalation_crore,
            COALESCE(AVG(r.physical_progress_percent), 0) as mean_progress_percent,
            COALESCE(AVG(m.selected_integrated_risk), 0) as mean_integrated_risk,
            COALESCE(AVG(e.execution_stress_index), 0) as mean_execution_stress_index,
            COUNT(CASE WHEN m.risk_band IN ('HIGH', 'VERY_HIGH') THEN 1 END) as high_risk_count,
            COUNT(CASE WHEN e.esi_tier IN ('ATTENTION', 'HIGH_PRIORITY') THEN 1 END) as high_execution_stress_count
        FROM v_project_monthly_dossier r
        LEFT JOIN ml_risk_scores m ON r.project_id = m.project_id AND r.report_month = m.report_month
        LEFT JOIN execution_stress_scores e ON r.project_id = e.project_id AND r.report_month = e.report_month
        WHERE r.report_month = :report_month
        GROUP BY r.state
        ORDER BY total_cost_escalation_crore DESC
        LIMIT :limit
    """)
    result = db.execute(sql, {"report_month": report_month, "limit": limit}).fetchall()
    
    breakdown = []
    for row in result:
        breakdown.append(BreakdownItem(
            group_name=row.group_name or "Unknown",
            total_projects=row.total_projects,
            active_projects=row.active_projects,
            total_cost_crore=Decimal(str(row.total_cost_crore)),
            total_cost_escalation_crore=Decimal(str(row.total_cost_escalation_crore)),
            mean_progress_percent=Decimal(str(row.mean_progress_percent)),
            mean_integrated_risk=Decimal(str(row.mean_integrated_risk)),
            mean_execution_stress_index=Decimal(str(row.mean_execution_stress_index)),
            high_risk_count=row.high_risk_count,
            high_execution_stress_count=row.high_execution_stress_count
        ))
        
    return PortfolioBreakdownResponse(report_month=report_month, breakdown=breakdown)
