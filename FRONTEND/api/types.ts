export type RiskBand = 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH';
export type ESITier = 'NOMINAL' | 'WATCH' | 'ATTENTION' | 'HIGH_PRIORITY';
export type DominantComponent = 'Schedule Delay' | 'Cost Overrun' | 'Schedule Revision';
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertSource = 'PREDICTIVE_ML' | 'EXECUTION_SURVEILLANCE' | 'RULE_ENGINE';

export interface MonthlySnapshot {
  report_month: string;
  original_cost_crore: number;
  revised_cost_crore: number;
  cumulative_expenditure_crore: number;
  physical_progress_percent: number;
  revised_completion_date?: string;
  source_file: string;
  source_table: string;
}

export interface PrescriptiveAction {
  directive: string;
  title: string;
  authority: string;
  reason: string;
}

export interface PredictiveRisk {
  schedule_delay_risk: number;
  cost_overrun_risk: number;
  schedule_revision_risk: number;
  selected_integrated_risk: number;
  risk_band: RiskBand;
  schedule_contribution: number;
  cost_contribution: number;
  schedule_revision_contribution: number;
  dominant_component: DominantComponent;
}

export interface ExecutionProfile {
  execution_stress_index: number;
  esi_tier: ESITier;
  s_stag: number;
  s_vel: number;
  s_div: number;
  s_sched: number;
  s_rep: number;
  flag_stag: number;
  flag_vel: number;
  flag_div: number;
  flag_sched: number;
  flag_rep: number;
  total_stress_flags: number;
  divergence_spread: number;
  schedule_slippage_months: number;
  dominant_stressor: string;
  suggested_action: PrescriptiveAction;
}

export interface SHAPAttribution {
  factor: string;
  importance: number;
  direction: 'risk_driver' | 'normal' | 'protective';
  value: string;
}

export interface AnomalyItem {
  project_id: string;
  report_month: string;
  project_name: string;
  source_file: string;
  flag_category: string;
  severity: string;
  flag_reason: string;
}

export interface ProjectDetail {
  project_id: string;
  project_name: string;
  agency: string;
  legacy_ocms_code?: string;
  state: string;
  sector: string;
  approval_start_date: string;
  original_completion_date: string;
  revised_completion_date: string;
  original_cost_crore: number;
  revised_cost_crore: number;
  cumulative_expenditure_crore: number;
  physical_progress_percent: number;
  predictive_risk: PredictiveRisk;
  execution_profile: ExecutionProfile;
  shap_attribution: SHAPAttribution[];
  anomalies: AnomalyItem[];
  longitudinal_trajectory: MonthlySnapshot[];
}

export interface SystemAlert {
  id: string;
  source: AlertSource;
  severity: AlertSeverity;
  project_id: string;
  project_name: string;
  agency: string;
  state: string;
  condition: string;
  timestamp: string;
  recommended_action: string;
}

export interface IndiaNode {
  project_id: string;
  project_name: string;
  agency: string;
  state: string;
  sector: string;
  lat: number;
  lng: number;
  risk_score: number;
  risk_band: RiskBand;
  status: 'critical' | 'attention' | 'healthy';
  physical_progress: number;
  revised_cost_crore: number;
}

export interface DatasetScale {
  total_project_months: number;
  unique_projects: number;
  completed_projects: number;
  newly_added_projects: number;
  months_coverage: number;
  start_month: string;
  end_month: string;
  total_sanctioned_cost_crore: number;
  total_revised_cost_crore: number;
  total_expenditure_crore: number;
  total_cost_escalation_crore: number;
  cost_escalation_percent: number;
  total_verified_anomalies: number;
}

export interface NationalSummary {
  dataset_scale: DatasetScale;
  model_performance: {
    schedule_delay_model: {
      algorithm: string;
      oot_roc_auc: number;
      oot_pr_auc: number;
      brier_score: number;
    };
    cost_overrun_model: {
      algorithm: string;
      oot_roc_auc: number;
      oot_pr_auc: number;
      brier_score: number;
    };
    schedule_revision_model: {
      algorithm: string;
      oot_roc_auc: number;
      oot_pr_auc: number;
      brier_score: number;
    };
    integrated_risk_formula: string;
    execution_stress_formula: string;
    non_redundancy_correlation: number;
    off_diagonal_divergence_pct: number;
  };
  sector_breakdown: Array<{
    sector: string;
    project_count: number;
    revised_cost_crore: number;
  }>;
  state_breakdown: Array<{
    state: string;
    count: number;
  }>;
  risk_distribution: Record<string, number>;
  esi_distribution: Record<string, number>;
  pipeline_stages: Array<{
    stage: string;
    description: string;
  }>;
}

export interface SimulationParams {
  baseProjectId: string;
  progressDeltaPct: number; // e.g. -10 to +10
  monthlySpendDeltaPct: number; // e.g. -20 to +20
  costVariancePct: number; // e.g. 0 to +50
  timelineDelayMonths: number; // e.g. 0 to 24
}

export interface SimulationResult {
  baseRisk: number;
  simulatedRisk: number;
  riskDelta: number;
  baseESI: number;
  simulatedESI: number;
  baseTier: ESITier;
  simulatedTier: ESITier;
  primaryRiskDriver: string;
  recommendedIntervention: PrescriptiveAction;
  isDemoSimulation: true;
}
