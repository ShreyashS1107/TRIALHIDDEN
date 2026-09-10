export interface CustomProjectInput {
  project_name: string;
  project_id: string;
  agency: string;
  state: string;
  original_cost_crore: number;
  revised_cost_crore: number;
  approval_start_date: string;
  original_completion_date: string;
  revised_completion_date?: string;
  physical_progress_percent: number;
  is_completed: boolean;
  cumulative_expenditure_crore?: number;
  sector?: string;
}

export interface RiskDriver {
  id: string;
  name: string;
  impact_pct: number;
  impact_level: 'High impact' | 'Medium impact' | 'Low impact';
  description: string;
}

export interface ModelRiskSignal {
  id: string;
  feature_name: string;
  label: string;
  observed_value: string;
  importance_weight: number;
  importance_pct: number;
  impact_level: 'High impact' | 'Medium impact' | 'Low impact';
  directional_signal: string;
  risk_component: 'Schedule Delay' | 'Cost Overrun' | 'Physical Execution' | 'Administrative' | string;
  attribution_type: string;
}

export interface CustomProjectPredictionResponse {
  project_id: string;
  project_name: string;
  agency: string;
  state: string;
  original_cost_crore?: number;
  revised_cost_crore?: number;
  approval_start_date?: string;
  original_completion_date?: string;
  revised_completion_date?: string;
  physical_progress_percent?: number;
  cumulative_expenditure_crore?: number;
  schedule_delay_risk: number;
  cost_overrun_risk: number;
  schedule_revision_risk: number;
  selected_integrated_risk: number;
  risk_band: 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
  dominant_component: string;
  predicted_cost_crore: number;
  predicted_delay_months: number;
  predicted_completion_date: string;
  model_confidence: number | null;
  recommended_intervention: string;
  risk_drivers: RiskDriver[];
  model_risk_signals?: ModelRiskSignal[];
  execution_stress_index: number;
  esi_tier: 'NOMINAL' | 'WATCH' | 'ATTENTION' | 'HIGH_PRIORITY' | string;
  is_ml_model?: boolean;
  model_version: string;
  model_metadata?: Record<string, any>;
  timestamp: string;
}



/**
 * Primary ML Prediction Gateway.
 * Dispatches project data to the authoritative trained ML inference pipeline.
 * The trained ML inference pipeline is the sole source of truth; no client-side approximations are performed.
 */
export async function predictCustomProject(input: CustomProjectInput): Promise<CustomProjectPredictionResponse> {
  const res = await fetch('/api/predict/project', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(input)
  });

  if (!res.ok) {
    const errJson = await res.json().catch(() => ({}));
    throw new Error(errJson.detail || errJson.error || `ML Prediction API returned HTTP ${res.status}`);
  }

  const data: CustomProjectPredictionResponse = await res.json();
  return data;
}

