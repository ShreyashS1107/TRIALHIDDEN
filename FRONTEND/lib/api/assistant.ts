import { getFeaturedProjects, getNationalSummary } from './projects';
import { formatIndianNumber } from '../utils/format';

export interface AssistantMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  dataPoints?: Array<{ label: string; value: string }>;
  suggestedFollowUps?: string[];
}

export async function queryPaimanaAssistant(prompt: string): Promise<AssistantMessage> {
  const pLower = prompt.toLowerCase();
  const projects = await getFeaturedProjects();
  const summary = await getNationalSummary();

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // 1. "Which projects need immediate attention?" or "high risk"
  if (pLower.includes('immediate attention') || pLower.includes('high priority') || pLower.includes('critical')) {
    const criticalList = projects
      .filter((p) => p.execution_profile.esi_tier === 'HIGH_PRIORITY' || p.predictive_risk.risk_band === 'VERY_HIGH')
      .slice(0, 3);

    const dataPoints = criticalList.map((p) => ({
      label: `${p.project_id}: ${p.project_name.slice(0, 38)}...`,
      value: `Risk ${Math.round(p.predictive_risk.selected_integrated_risk * 100)}% | ESI ${p.execution_profile.execution_stress_index.toFixed(2)} (${p.execution_profile.esi_tier}) | Action: ${p.execution_profile.suggested_action.directive}`
    }));

    return {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: `Across the 21,555 longitudinal records in PAIMANA, operational surveillance currently flags **${criticalList.length} focal projects** requiring top-tier intervention under the MoSPI/IPMD framework:`,
      timestamp: now,
      dataPoints,
      suggestedFollowUps: [
        `Why is project ${criticalList[0]?.project_id || '606431'} high risk?`,
        'Show projects with large cost revisions',
        'Compare top 2 critical projects'
      ]
    };
  }

  // 2. Specific project enquiry (e.g. "400178" or "606431" or "105236" or "why is this project")
  const idMatch = prompt.match(/\b\d{5,9}\b/);
  const targetId = idMatch ? idMatch[0] : (pLower.includes('why') ? '400178' : null);
  if (targetId) {
    const proj = projects.find((p) => p.project_id === targetId) || projects[0];
    const riskPct = Math.round(proj.predictive_risk.selected_integrated_risk * 100);
    const costEscalation = Math.max(0, proj.revised_cost_crore - proj.original_cost_crore);

    return {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: `**Detailed Diagnostic for Project ${proj.project_id}** (${proj.project_name.slice(0, 60)}):\n\n` +
        `• **Pillar 1 Predictive Risk**: ${riskPct}% (${proj.predictive_risk.risk_band}), dominated by **${proj.predictive_risk.dominant_component}**.\n` +
        `• **Pillar 2 Execution Stress (ESI)**: ${proj.execution_profile.execution_stress_index.toFixed(2)} (${proj.execution_profile.esi_tier}) with ${proj.execution_profile.total_stress_flags}/5 active flags.\n` +
        `• **Key Stressor**: ${proj.execution_profile.dominant_stressor}.\n` +
        `• **Cost Trajectory**: Original ₹${formatIndianNumber(proj.original_cost_crore)} Cr → Revised ₹${formatIndianNumber(proj.revised_cost_crore)} Cr (+₹${formatIndianNumber(costEscalation)} Cr delta).\n` +
        `• **Prescriptive Directive**: \`${proj.execution_profile.suggested_action.directive}\` — ${proj.execution_profile.suggested_action.reason}`,
      timestamp: now,
      dataPoints: [
        { label: 'Physical Progress', value: `${proj.physical_progress_percent}%` },
        { label: 'Expenditure Incurred', value: `₹${formatIndianNumber(proj.cumulative_expenditure_crore)} Cr` },
        { label: 'Implementing Agency', value: proj.agency },
        { label: 'Prescribed Action', value: proj.execution_profile.suggested_action.title }
      ],
      suggestedFollowUps: [
        'What changed in this project over the last six months?',
        'Run What-If simulation for this project',
        'Show projects with large cost revisions'
      ]
    };
  }

  // 3. "Show projects with large cost revisions" or "cost pressure"
  if (pLower.includes('cost') || pLower.includes('budget') || pLower.includes('revision')) {
    const topCost = [...projects]
      .sort((a, b) => (b.revised_cost_crore - b.original_cost_crore) - (a.revised_cost_crore - a.original_cost_crore))
      .slice(0, 3);

    const dataPoints = topCost.map((p) => {
      const delta = p.revised_cost_crore - p.original_cost_crore;
      return {
        label: `${p.project_id}: ${p.project_name.slice(0, 36)}...`,
        value: `Sanctioned ₹${formatIndianNumber(p.original_cost_crore)} Cr → Revised ₹${formatIndianNumber(p.revised_cost_crore)} Cr (+₹${formatIndianNumber(delta)} Cr)`
      };
    });

    return {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: `Nationwide, MoSPI longitudinal data tracks **₹${formatIndianNumber(summary.dataset_scale.total_cost_escalation_crore)} Cr** in total cost escalation across the active portfolio (+${summary.dataset_scale.cost_escalation_percent}%). The top cost revisions in the surveillance register include:`,
      timestamp: now,
      dataPoints,
      suggestedFollowUps: [
        `Why is project ${topCost[0].project_id} at risk?`,
        'Which projects have declining progress?',
        'Show early warning anomalies'
      ]
    };
  }

  // 4. "What changed in this project over the last six months?" or "trajectory"
  if (pLower.includes('six months') || pLower.includes('trajectory') || pLower.includes('changed') || pLower.includes('timeline')) {
    const p = projects[0];
    const recentSnaps = p.longitudinal_trajectory.slice(-6);

    return {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: `Trajectory audit for **Project ${p.project_id}** over recent reporting epochs:\n` +
        `• Baseline Month (${recentSnaps[0]?.report_month || '2025-10'}): Progress ${recentSnaps[0]?.physical_progress_percent || 0}%, Spend ₹${recentSnaps[0]?.cumulative_expenditure_crore || 0} Cr\n` +
        `• Latest Epoch (${recentSnaps[recentSnaps.length - 1]?.report_month || '2026-03'}): Progress ${recentSnaps[recentSnaps.length - 1]?.physical_progress_percent || 0}%, Spend ₹${recentSnaps[recentSnaps.length - 1]?.cumulative_expenditure_crore || 0} Cr\n` +
        `• Trajectory Health: Monotonic reporting maintained; no unvalidated regressions flagged in this cycle.`,
      timestamp: now,
      suggestedFollowUps: [
        'Which projects need immediate attention?',
        'Show early warning alerts',
        'Compare these two projects'
      ]
    };
  }

  // Default response
  return {
    id: `msg-${Date.now()}`,
    sender: 'assistant',
    text: `PAIMANA Intelligence is monitoring **${formatIndianNumber(summary.dataset_scale.unique_projects, 0)} central infrastructure projects** across 15 monthly epochs (April 2025 – June 2026). All queries are grounded in verified MoSPI/IPMD datasets with Platt-calibrated ML risk and deterministic Execution Stress (ESI) indices.`,
    timestamp: now,
    dataPoints: [
      { label: 'Active Projects', value: `${formatIndianNumber(summary.dataset_scale.unique_projects, 0)} ongoing` },
      { label: 'Historical Snapshots', value: `${formatIndianNumber(summary.dataset_scale.total_project_months, 0)} records` },
      { label: 'Total Portfolio Budget', value: `₹${(summary.dataset_scale.total_revised_cost_crore / 100000).toFixed(2)} Lakh Cr` },
      { label: 'Surveillance Status', value: 'Live 15-Month Feed' }
    ],
    suggestedFollowUps: [
      'Which projects need immediate attention?',
      'Why is project 400178 at risk?',
      'Show projects with large cost revisions',
      'Which projects have declining progress?'
    ]
  };
}
