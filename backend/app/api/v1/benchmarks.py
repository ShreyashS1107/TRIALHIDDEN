from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.benchmark import BenchmarkRepository
from app.schemas.benchmark import PaginatedHistoricalBenchmarksResponse
from app.services.benchmark import BenchmarkService

router = APIRouter()

def get_benchmark_service(db: Session = Depends(get_db)) -> BenchmarkService:
    repo = BenchmarkRepository(db)
    return BenchmarkService(repo)

@router.get(
    "/ocms",
    response_model=PaginatedHistoricalBenchmarksResponse,
    summary="Get OCMS Historical Benchmarks",
    description="Retrieve paginated historical performance benchmarks aggregated by sector or agency.",
)
def list_benchmarks(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    benchmark_level: Optional[str] = Query(None, description="Filter by level (e.g. 'Agency x Year')"),
    entity_name: Optional[str] = Query(None, description="Filter by agency or sector name"),
    year: Optional[str] = Query(None, description="Filter by specific year or 'All Years'"),
    service: BenchmarkService = Depends(get_benchmark_service),
) -> PaginatedHistoricalBenchmarksResponse:
    return service.list_benchmarks(
        page=page,
        page_size=page_size,
        benchmark_level=benchmark_level,
        entity_name=entity_name,
        year=year,
    )
