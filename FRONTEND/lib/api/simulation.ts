import { SimulationParams, SimulationResult, PrescriptiveAction } from './types';
import { getFeaturedProjects } from './projects';

export async function runWhatIfSimulation(params: SimulationParams): Promise<SimulationResult> {
  const projects = await getFeaturedProjects();
  const project = projects.find((p) => p.project_id === params.baseProjectId) || projects[0];

  const baseRisk = project.predictive_risk.selected_integrated_risk;
  const baseESI = project.execution_profile.execution_stress_index;

  // Simulate progress velocity change impact
  // Negative progress change increases schedule risk and velocity stress
  const progressShift = -params.progressDeltaPct * 0.015;
  // Spend acceleration without matching physical progress increases divergence
  const spendShift = params.monthlySpendDeltaPct * 0.008;
  // Cost variance directly lifts cost overrun risk
  const costShift = params.costVariancePct * 0.01;
  // Timeline delay adds to schedule slippage
  const delayShift = params.timelineDelayMonths * 0.02;

  let simulatedRisk = Math.min(0.99, Math.max(0.01, baseRisk + progressShift + costShift + delayShift * 0.6));
  let simulatedESI = Math.min(0.99, Math.max(0.01, baseESI + progressShift * 0.8 + spendShift + delayShift * 0.4));

  // Determine simulated tier
  let simulatedTier: 'NOMINAL' | 'WATCH' | 'ATTENTION' | 'HIGH_PRIORITY' = 'NOMINAL';
  if (simulatedESI >= 0.75) simulatedTier = 'HIGH_PRIORITY';
  else if (simulatedESI >= 0.55) simulatedTier = 'ATTENTION';
  else if (simulatedESI >= 0.35) simulatedTier = 'WATCH';

  // Primary risk driver identification
  let primaryDriver = 'Progress Velocity Deterioration';
  if (costShift > progressShift && costShift > delayShift) {
    primaryDriver = 'Capital Cost Revision Escalation';
  } else if (delayShift > progressShift) {
    primaryDriver = 'Schedule Slippage Accumulation';
  } else if (spendShift > progressShift) {
    primaryDriver = 'Expenditure/Progress Divergence';
  }

  // Recommended intervention based on simulated state
  let action: PrescriptiveAction = {
    directive: 'RESOURCE_MOBILIZATION_DIRECTIVE',
    title: 'Resource Mobilization Directive',
    authority: 'Project Review Committee (PRC)',
    reason: `Simulated velocity collapse requires joint plant & labor inspection to recover ${Math.abs(params.progressDeltaPct)}% progress gap.`
  };

  if (simulatedTier === 'HIGH_PRIORITY' || simulatedRisk >= 0.80) {
    action = {
      directive: 'INTER_MINISTERIAL_COMMITTEE_ESCALATION',
      title: 'Inter-Ministerial Committee Escalation',
      authority: 'MoSPI / IPMD Central Monitoring Committee & Pragati Secretariat',
      reason: `Multi-dimensional risk exceeded 80% threshold under simulated conditions (+${((simulatedRisk - baseRisk) * 100).toFixed(1)}% risk shift).`
    };
  } else if (params.costVariancePct > 20) {
    action = {
      directive: 'FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT',
      title: 'Financial-Physical Alignment Audit',
      authority: 'Field Inspection & Technical Audit Directorate',
      reason: 'Cost variance divergence detected; direct field audit of contractor billing milestones required.'
    };
  }

  return {
    baseRisk: Math.round(baseRisk * 1000) / 1000,
    simulatedRisk: Math.round(simulatedRisk * 1000) / 1000,
    riskDelta: Math.round((simulatedRisk - baseRisk) * 1000) / 1000,
    baseESI: Math.round(baseESI * 1000) / 1000,
    simulatedESI: Math.round(simulatedESI * 1000) / 1000,
    baseTier: project.execution_profile.esi_tier,
    simulatedTier,
    primaryRiskDriver: primaryDriver,
    recommendedIntervention: action,
    isDemoSimulation: true,
  };
}
