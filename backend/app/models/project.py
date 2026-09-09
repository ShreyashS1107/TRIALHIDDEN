from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.alert import SystemAlert
    from app.models.anomaly import DataAnomalyLog
    from app.models.execution import ExecutionStressScore
    from app.models.risk import MLRiskScore


class Project(Base):
    """
    Canonical Projects Master Table.
    Holds immutable or slowly-changing project identity attributes across all reporting months.
    """
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agency: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    legacy_ocms_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    approval_start_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    original_completion_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    original_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships to child entities with cascade deletion
    monthly_snapshots: Mapped[List["MonthlySnapshot"]] = relationship(
        "MonthlySnapshot", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    ml_risk_scores: Mapped[List["MLRiskScore"]] = relationship(
        "MLRiskScore", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    execution_stress_scores: Mapped[List["ExecutionStressScore"]] = relationship(
        "ExecutionStressScore", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    system_alerts: Mapped[List["SystemAlert"]] = relationship(
        "SystemAlert", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    anomalies: Mapped[List["DataAnomalyLog"]] = relationship(
        "DataAnomalyLog", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )


class MonthlySnapshot(Base):
    """
    Monthly Longitudinal Snapshots Table (Layer A Raw Facts).
    Stores monthly time-series records. Exactly one row per project per report_month.
    """
    __tablename__ = "monthly_snapshots"
    __table_args__ = (
        UniqueConstraint("project_id", "report_month", name="uq_project_month"),
        CheckConstraint("physical_progress_percent >= 0.0 AND physical_progress_percent <= 100.0", name="chk_progress_bounds"),
        CheckConstraint("revised_cost_crore >= 0.0 AND cumulative_expenditure_crore >= 0.0", name="chk_costs_positive"),
    )

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()")
    )
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    revised_completion_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    revised_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    cumulative_expenditure_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    physical_progress_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    source_file: Mapped[str] = mapped_column(String(128), nullable=False)
    source_table: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    # Inverse relationship to Project
    project: Mapped["Project"] = relationship("Project", back_populates="monthly_snapshots")
