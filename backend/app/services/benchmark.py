from typing import Optional

from app.repositories.benchmark import BenchmarkRepository
from app.schemas.benchmark import PaginatedHistoricalBenchmarksResponse, HistoricalBenchmarkResponse


class BenchmarkService:
    def __init__(self, repository: BenchmarkRepository):
        self.repository = repository

    def list_benchmarks(
        self,
        page: int = 1,
        page_size: int = 20,
        benchmark_level: Optional[str] = None,
        entity_name: Optional[str] = None,
        year: Optional[str] = None,
    ) -> PaginatedHistoricalBenchmarksResponse:
        """
        Fetch paginated list of historical benchmarks.
        """
        items, total = self.repository.list_benchmarks(
            page=page,
            page_size=page_size,
            benchmark_level=benchmark_level,
            entity_name=entity_name,
            year=year,
        )
        
        return PaginatedHistoricalBenchmarksResponse(
            items=[HistoricalBenchmarkResponse.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )
