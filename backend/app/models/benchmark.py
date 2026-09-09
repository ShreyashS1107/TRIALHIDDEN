from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OCMSHistoricalBenchmark(Base):
    __tablename__ = "ocms_historical_benchmarks"
    __table_args__ = (
        UniqueConstraint("benchmark_level", "entity_name", "year", name="uq_ocms_benchmark_grain"),
    )

    benchmark_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Legacy DB Spec fields
    project_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("projects.project_id", ondelete="SET NULL"), nullable=True)
    legacy_ocms_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    agency: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    historical_observation_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    historical_mean_cost_escalation_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    historical_mean_delay_months: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    historical_completion_rate_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Exact fields from historical_benchmarking.csv
    benchmark_level: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[str] = mapped_column(String(64), nullable=False)
    total_completed_projects: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    projects_with_schedule_outcome: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delay_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delay_rate_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    mean_delay_months: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    median_delay_months: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    projects_with_cost_outcome: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_overrun_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_overrun_rate_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    mean_cost_overrun_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    median_cost_overrun_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    total_original_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 2), nullable=True)
    total_cumulative_expenditure_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 2), nullable=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
