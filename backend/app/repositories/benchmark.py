from typing import List, Optional, Tuple

from sqlalchemy import select, func

from app.database.session import Session
from app.models.benchmark import OCMSHistoricalBenchmark


class BenchmarkRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_benchmarks(
        self,
        page: int = 1,
        page_size: int = 20,
        benchmark_level: Optional[str] = None,
        entity_name: Optional[str] = None,
        year: Optional[str] = None,
    ) -> Tuple[List[OCMSHistoricalBenchmark], int]:
        """
        List historical benchmarks with optional filtering.
        """
        stmt = select(OCMSHistoricalBenchmark)
        count_stmt = select(func.count()).select_from(OCMSHistoricalBenchmark)

        if benchmark_level:
            stmt = stmt.where(OCMSHistoricalBenchmark.benchmark_level == benchmark_level)
            count_stmt = count_stmt.where(OCMSHistoricalBenchmark.benchmark_level == benchmark_level)
        
        if entity_name:
            stmt = stmt.where(OCMSHistoricalBenchmark.entity_name.ilike(f"%{entity_name}%"))
            count_stmt = count_stmt.where(OCMSHistoricalBenchmark.entity_name.ilike(f"%{entity_name}%"))
            
        if year:
            stmt = stmt.where(OCMSHistoricalBenchmark.year == year)
            count_stmt = count_stmt.where(OCMSHistoricalBenchmark.year == year)

        # Deterministic sorting
        stmt = stmt.order_by(
            OCMSHistoricalBenchmark.benchmark_level,
            OCMSHistoricalBenchmark.entity_name,
            OCMSHistoricalBenchmark.year.desc()
        )

        total = self.db.execute(count_stmt).scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        items = self.db.execute(stmt).scalars().all()
        return list(items), total

