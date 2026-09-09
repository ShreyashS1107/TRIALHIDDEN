from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import DominantComponentEnum, RiskBandEnum

if TYPE_CHECKING:
    from app.models.project import Project


class MLRiskScore(Base):
    """
    Machine Learning Risk Scores Table (Layer C Predictions).
    Stores multi-dimensional risk scores across reporting epochs.
    """
    __tablename__ = "ml_risk_scores"
    __table_args__ = (
        UniqueConstraint("project_id", "report_month", name="uq_ml_project_month"),
    )

    score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()")
    )
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    schedule_delay_risk: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    cost_overrun_risk: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    schedule_revision_risk: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    selected_integrated_risk: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    risk_band: Mapped[RiskBandEnum] = mapped_column(
        Enum(RiskBandEnum, name="risk_band_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    dominant_component: Mapped[DominantComponentEnum] = mapped_column(
        Enum(DominantComponentEnum, name="dominant_component_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    schedule_contribution: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    cost_contribution: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    schedule_revision_contribution: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    model_version: Mapped[str] = mapped_column(
        String(32), default="v1.0.0-rf02-calibrated", server_default=text("'v1.0.0-rf02-calibrated'"), nullable=False
    )
    scored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    # Inverse relationship to Project
    project: Mapped["Project"] = relationship("Project", back_populates="ml_risk_scores")
