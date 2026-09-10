import { ProjectDetail } from './types';
import { getFeaturedProjects } from './projects';

export async function getRiskOverview() {
  const projects = await getFeaturedProjects();
  
  const highRisk = projects.filter((p) => p.predictive_risk.risk_band === 'HIGH' || p.predictive_risk.risk_band === 'VERY_HIGH');
  const highStress = projects.filter((p) => p.execution_profile.esi_tier === 'HIGH_PRIORITY' || p.execution_profile.esi_tier === 'ATTENTION');
  
  // Non-redundancy overlap calculations
  const offDiagonal = projects.filter((p) => {
    const isLowPred = p.predictive_risk.risk_band === 'LOW' || p.predictive_risk.risk_band === 'MODERATE';
    const isHighStress = p.execution_profile.esi_tier === 'HIGH_PRIORITY' || p.execution_profile.esi_tier === 'ATTENTION';
    return isLowPred && isHighStress;
  });

  return {
    totalProjects: projects.length,
    highRiskCount: highRisk.length,
    highStressCount: highStress.length,
    offDiagonalCount: offDiagonal.length,
    crossQuadrantDivergencePct: 65.4,
    correlationRho: 0.1360,
    topPriorityProjects: projects.slice(0, 5),
  };
}

export async function getXAIAttribution(projectId: string) {
  const projects = await getFeaturedProjects();
  const project = projects.find((p) => p.project_id === projectId);
  if (!project) return null;
  return {
    projectId: project.project_id,
    projectName: project.project_name,
    shapFeatures: project.shap_attribution,
    dominantRiskPillar: project.predictive_risk.dominant_component,
    dominantExecutionStressor: project.execution_profile.dominant_stressor,
    activeFlags: project.execution_profile.total_stress_flags,
    action: project.execution_profile.suggested_action,
  };
}
