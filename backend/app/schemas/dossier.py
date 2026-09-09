from decimal import Decimal
from typing import Optional
import uuid
from pydantic import Field

from app.schemas.common import BaseSchema


class ProjectMonthlyDossierResponse(BaseSchema):
    """
    Full unified analytical dossier response reflecting the v_project_monthly_dossier view.
    Encompasses Layer A raw snapshot facts, Layer B derived deterministic metrics,
    Layer C machine learning risk signals, and Pillar 2 execution surveillance metrics.
    """
    snapshot_id: uuid.UUID = Field(..., description="Underlying snapshot UUID")
    project_id: Optional[str] = Field(None, description="Project identifier")
    report_month: Optional[str] = Field(None, description="Report month epoch (YYYY-MM)")
    revised_completion_date: Optional[str] = Field(None, description="Anticipated DOC (YYYY-MM)")
    revised_cost_crore: Optional[Decimal] = Field(None, description="Revised cost in ₹ Crore")
    cumulative_expenditure_crore: Optional[Decimal] = Field(None, description="Cumulative expenditure in ₹ Crore")
    physical_progress_percent: Optional[Decimal] = Field(None, description="Physical progress percentage [0.00, 100.00]")
    source_file: Optional[str] = Field(None, description="Flash Report source PDF")
    source_table: Optional[str] = Field(None, description="Flash Report source table")
    project_name: Optional[str] = Field(None, description="Official project title")
    agency: Optional[str] = Field(None, description="Implementing agency")
    state: Optional[str] = Field(None, description="Location state")
    legacy_ocms_code: Optional[str] = Field(None, description="Legacy OCMS code")
    approval_start_date: Optional[str] = Field(None, description="Sanction date (YYYY-MM)")
    original_completion_date: Optional[str] = Field(None, description="Original DOC (YYYY-MM)")
    original_cost_crore: Optional[Decimal] = Field(None, description="Sanctioned cost in ₹ Crore")
    prev_prog_1m: Optional[Decimal] = Field(None, description="1-month prior physical progress")
    prev_prog_3m: Optional[Decimal] = Field(None, description="3-month prior physical progress")
    prev_exp_1m: Optional[Decimal] = Field(None, description="1-month prior cumulative expenditure")
    months_since_last_progress_increase: Optional[int] = Field(None, description="Duration in months without progress increase")

    # Layer B Derived Metrics
    cost_escalation_crore: Optional[Decimal] = Field(None, description="Cost escalation in ₹ Crore")
    cost_escalation_percent: Optional[Decimal] = Field(None, description="Cost escalation percentage")
    expenditure_ratio_percent: Optional[Decimal] = Field(None, description="Expenditure vs original budget ratio")
    remaining_physical_progress: Optional[Decimal] = Field(None, description="Remaining physical progress percent")
    schedule_slippage_months: Optional[Decimal] = Field(None, description="Schedule slippage in months")
    months_to_original_doc: Optional[int] = Field(None, description="Months remaining to original deadline")
    progress_velocity_1m: Optional[Decimal] = Field(None, description="1-month progress velocity")
    progress_velocity_3m: Optional[Decimal] = Field(None, description="3-month rolling average progress velocity")
    stagnant_3m_flag: Optional[int] = Field(None, description="3-month stagnation flag (1=stagnant, 0=progressing)")
    expenditure_progress_divergence: Optional[Decimal] = Field(None, description="Capital burn vs physical progress divergence")
    project_age_months: Optional[int] = Field(None, description="Project age in months from approval")
    planned_duration_months: Optional[int] = Field(None, description="Planned project duration in months")

    # Layer C Machine Learning Risk Signals
    schedule_delay_risk: Optional[Decimal] = Field(None, description="Schedule delay probability")
    cost_overrun_risk: Optional[Decimal] = Field(None, description="Cost overrun score")
    schedule_revision_risk: Optional[Decimal] = Field(None, description="Schedule revision risk score")
    selected_integrated_risk: Optional[Decimal] = Field(None, description="Weighted composite risk index")
    risk_band: Optional[str] = Field(None, description="Risk band classification")
    dominant_component: Optional[str] = Field(None, description="Leading risk component")
    schedule_contribution: Optional[Decimal] = Field(None, description="Schedule risk contribution")
    cost_contribution: Optional[Decimal] = Field(None, description="Cost risk contribution")
    schedule_revision_contribution: Optional[Decimal] = Field(None, description="Schedule revision risk contribution")
    schedule_contrib_pct: Optional[Decimal] = Field(None, description="Schedule contribution percentage")
    cost_contrib_pct: Optional[Decimal] = Field(None, description="Cost contribution percentage")
    schedule_rev_contrib_pct: Optional[Decimal] = Field(None, description="Schedule revision contribution percentage")

    # Pillar 2 Execution Surveillance Signals
    execution_stress_index: Optional[Decimal] = Field(None, description="Execution Stress Index (ESI)")
    s_stag: Optional[Decimal] = Field(None, description="Stagnation stress score")
    s_vel: Optional[Decimal] = Field(None, description="Velocity collapse stress score")
    s_sched: Optional[Decimal] = Field(None, description="Schedule slippage debt stress score")
    s_div: Optional[Decimal] = Field(None, description="Expenditure divergence stress score")
    s_rep: Optional[Decimal] = Field(None, description="Reporting friction stress score")
    flag_stag: Optional[int] = Field(None, description="Stagnation flag")
    flag_vel: Optional[int] = Field(None, description="Velocity flag")
    flag_sched: Optional[int] = Field(None, description="Schedule slippage flag")
    flag_div: Optional[int] = Field(None, description="Divergence flag")
    flag_rep: Optional[int] = Field(None, description="Reporting friction flag")
    total_stress_flags: Optional[int] = Field(None, description="Total active stress flags")
    esi_tier: Optional[str] = Field(None, description="ESI tier")
    dominant_stressor: Optional[str] = Field(None, description="Leading operational stressor")
    suggested_action: Optional[str] = Field(None, description="Suggested prescriptive directive")
    execution_index_version: Optional[str] = Field(None, description="Surveillance index version tag")
