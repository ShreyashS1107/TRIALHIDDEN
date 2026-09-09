from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import DominantStressorEnum, EsiTierEnum, PrescriptiveActionEnum

if TYPE_CHECKING:
    from app.models.project import Project


class ExecutionStressScore(Base):
    """
    Execution Stress Scores Table (Pillar 2 Operational Surveillance).
    The underlying PostgreSQL table enforces uq_esi_project_month (project_id, report_month).
    SQLAlchemy ORM identity is mapped as composite primary keys (project_id, report_month).
    """
    __tablename__ = "execution_stress_scores"
    __table_args__ = (
        UniqueConstraint("project_id", "report_month", name="uq_esi_project_month"),
    )

    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    report_month: Mapped[str] = mapped_column(String(7), primary_key=True, nullable=False)

    s_stag: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    s_vel: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    s_div: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    s_sched: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    s_rep: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)

    flag_stag: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"), nullable=False)
    flag_vel: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"), nullable=False)
    flag_div: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"), nullable=False)
    flag_sched: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"), nullable=False)
    flag_rep: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"), nullable=False)
    total_stress_flags: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"), nullable=False)

    execution_stress_index: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    esi_tier: Mapped[EsiTierEnum] = mapped_column(
        Enum(EsiTierEnum, name="esi_tier_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    dominant_stressor: Mapped[DominantStressorEnum] = mapped_column(
        Enum(DominantStressorEnum, name="dominant_stressor_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    suggested_action: Mapped[PrescriptiveActionEnum] = mapped_column(
        Enum(PrescriptiveActionEnum, name="prescriptive_action_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    execution_index_version: Mapped[str] = mapped_column(
        String(32), default="v1.0.0-esi-5dim", server_default=text("'v1.0.0-esi-5dim'"), nullable=False
    )
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    # Inverse relationship to Project
    project: Mapped["Project"] = relationship("Project", back_populates="execution_stress_scores")
