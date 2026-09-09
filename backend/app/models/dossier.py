from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import (
    BigInteger,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ProjectMonthlyDossier(Base):
    """
    Deterministic Layer B Derived Analytics Engine (SQL View: v_project_monthly_dossier).
    Computes rolling lag deltas, stagnation streaks, cost escalation, schedule slippage,
    and joins Layer C ML Risk Signals and Pillar 2 Execution Stress Scores.

    READ-ONLY: This model reflects an analytical PostgreSQL view.
    Mutations (INSERT, UPDATE, DELETE) are strictly prohibited.
    """
    __tablename__ = "v_project_monthly_dossier"
    __table_args__ = {"info": {"read_only": True}}

    # Unique identity confirmed against live view (21,555 distinct non-null rows)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(32), nullable=True)
    report_month: Mapped[str] = mapped_column(String(7), nullable=True)
    revised_completion_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    revised_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    cumulative_expenditure_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    physical_progress_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    source_file: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_table: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    project_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    legacy_ocms_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    approval_start_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    original_completion_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    original_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    prev_prog_1m: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    prev_prog_3m: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    prev_exp_1m: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    months_since_last_progress_increase: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Derived Metrics
    cost_escalation_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    cost_escalation_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    expenditure_ratio_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    remaining_physical_progress: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    schedule_slippage_months: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    months_to_original_doc: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress_velocity_1m: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    progress_velocity_3m: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    stagnant_3m_flag: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expenditure_progress_divergence: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    project_age_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    planned_duration_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Layer C Machine Learning Signals (Left-joined from ml_risk_scores)
    schedule_delay_risk: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    cost_overrun_risk: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    schedule_revision_risk: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    selected_integrated_risk: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    risk_band: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    dominant_component: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    schedule_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    cost_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    schedule_revision_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    schedule_contrib_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    cost_contrib_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    schedule_rev_contrib_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)

    # Pillar 2 Execution Surveillance Signals (Left-joined from execution_stress_scores)
    execution_stress_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    s_stag: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    s_vel: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    s_sched: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    s_div: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    s_rep: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    flag_stag: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    flag_vel: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    flag_sched: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    flag_div: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    flag_rep: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    total_stress_flags: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    esi_tier: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    dominant_stressor: Mapped[Optional[str]] = mapped_column(String(28), nullable=True)
    suggested_action: Mapped[Optional[str]] = mapped_column(String(38), nullable=True)
    execution_index_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


# Strict read-only enforcement hooks
@event.listens_for(ProjectMonthlyDossier, "before_insert")
def _block_dossier_insert(mapper, connection, target):
    raise RuntimeError("ProjectMonthlyDossier maps to a read-only PostgreSQL view. INSERT is not permitted.")


@event.listens_for(ProjectMonthlyDossier, "before_update")
def _block_dossier_update(mapper, connection, target):
    raise RuntimeError("ProjectMonthlyDossier maps to a read-only PostgreSQL view. UPDATE is not permitted.")


@event.listens_for(ProjectMonthlyDossier, "before_delete")
def _block_dossier_delete(mapper, connection, target):
    raise RuntimeError("ProjectMonthlyDossier maps to a read-only PostgreSQL view. DELETE is not permitted.")
