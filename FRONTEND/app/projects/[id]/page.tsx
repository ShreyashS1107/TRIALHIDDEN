import React from 'react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import { ArrowLeft, AlertTriangle, Compass, CheckCircle2, ShieldAlert } from 'lucide-react';
import { getProjectDossier } from '@/lib/api/search';
import { ProjectHeader } from '@/components/projects/dossier/ProjectHeader';
import { ProjectSnapshotCards } from '@/components/projects/dossier/ProjectSnapshotCards';
import { CostTrajectoryChart } from '@/components/projects/dossier/CostTrajectoryChart';
import { ScheduleTrajectoryView } from '@/components/projects/dossier/ScheduleTrajectoryView';
import { PhysicalProgressChart } from '@/components/projects/dossier/PhysicalProgressChart';
import { RiskPredictionPanel } from '@/components/projects/dossier/RiskPredictionPanel';
import { RiskDriversView } from '@/components/projects/dossier/RiskDriversView';
import { RiskVsTimeChart } from '@/components/projects/dossier/RiskVsTimeChart';
import { ProjectTimelineView } from '@/components/projects/dossier/ProjectTimelineView';
import { DataProvenancePanel } from '@/components/projects/dossier/DataProvenancePanel';
import { SimulationCTA } from '@/components/projects/dossier/SimulationCTA';

interface PageProps {
  params: {
    id: string;
  };
}

export default async function ProjectDossierPage({ params }: PageProps) {
  const dossier = await getProjectDossier(params.id);

  if (!dossier) {
    return (
      <main className="min-h-screen bg-slate-50 dark:bg-[#040d13] text-slate-900 dark:text-slate-100 pt-32 pb-24">
        <Navbar />
        <div className="max-w-xl mx-auto px-4 text-center py-20">
          <div className="p-8 sm:p-12 rounded-3xl bg-white dark:bg-[#06131c] border border-slate-200 dark:border-white/10 shadow-xl space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/15 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
              Project Record Not Found
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              No monitored infrastructure asset found under Project ID or legacy identifier{' '}
              <strong className="font-mono text-cyan-600 dark:text-cyan-400">&ldquo;{params.id}&rdquo;</strong>.
            </p>
            <div className="pt-2">
              <Link
                href="/projects"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-700 dark:text-cyan-400 font-mono font-bold text-xs tracking-wider transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>RETURN TO PROJECT SEARCH</span>
              </Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  const { project, timeline, risk_trajectory } = dossier;

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-[#040d13] text-slate-900 dark:text-slate-100">
      <Navbar />

      {/* Header section with breadcrumbs and key asset identity */}
      <div className="pt-20">
        <ProjectHeader project={project} />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {/* Core Intelligence Pillar Questions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 shadow-sm space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-bold">
              1. WHAT IS HAPPENING?
            </div>
            <div className="text-xs font-semibold text-slate-900 dark:text-white">
              Physical Progress: {project.physical_progress_percent}%
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Cumulative expenditure at ₹{project.cumulative_expenditure_crore} Cr against ₹{project.revised_cost_crore} Cr revised budget.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 shadow-sm space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-bold">
              2. WHY IS IT HAPPENING?
            </div>
            <div className="text-xs font-semibold text-slate-900 dark:text-white">
              Primary Bottleneck: {project.dominant_component}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {project.has_revision ? 'Milestone extension recorded.' : 'Critical milestones approaching target completion window.'}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 shadow-sm space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-bold">
              3. WHAT WILL HAPPEN?
            </div>
            <div className="text-xs font-semibold text-slate-900 dark:text-white">
              Risk: {project.risk_band === 'NOT_ASSESSED' ? 'Under Evaluation' : `${project.risk_band} (${Math.round((project.selected_integrated_risk || 0) * 100)}%)`}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Model predicts {project.schedule_delay_risk ? Math.round(project.schedule_delay_risk * 100) : 0}% schedule delay risk.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 shadow-sm space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-bold">
              4. WHAT SHOULD WE WATCH?
            </div>
            <div className="text-xs font-semibold text-slate-900 dark:text-white">
              Target Horizon: {project.revised_completion_date || project.original_completion_date}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Risk trajectory trend is {project.risk_trend}. Monitor capital burn velocity.
            </p>
          </div>
        </div>

        {/* SECTION 1: PROJECT SNAPSHOT */}
        <ProjectSnapshotCards project={project} />

        {/* SECTION 2: COST TRAJECTORY */}
        <CostTrajectoryChart
          timeline={timeline}
          originalCost={project.original_cost_crore}
          revisedCost={project.revised_cost_crore}
        />

        {/* SECTION 3: SCHEDULE TRAJECTORY */}
        <ScheduleTrajectoryView project={project} />

        {/* SECTION 4: PHYSICAL PROGRESS */}
        <PhysicalProgressChart
          timeline={timeline}
          currentProgress={project.physical_progress_percent}
        />

        {/* SECTION 5: ML RISK PREDICTION */}
        <RiskPredictionPanel project={project} />

        {/* SECTION 6: RISK DRIVERS */}
        <RiskDriversView project={project} />

        {/* SECTION 7: RISK VS TIME */}
        <RiskVsTimeChart
          riskTrajectory={risk_trajectory}
          currentRisk={project.selected_integrated_risk}
          previousRisk={project.previous_risk}
          riskTrend={project.risk_trend}
        />

        {/* SECTION 8: PROJECT TIMELINE */}
        <ProjectTimelineView
          project={project}
          timeline={timeline}
        />

        {/* SECTION 9: DATA PROVENANCE */}
        <DataProvenancePanel project={project} />

        {/* FINAL CTA: RUN WHAT-IF SIMULATION */}
        <SimulationCTA projectId={project.project_id} />
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-white/10 py-10 mt-16 bg-slate-100 dark:bg-[#03090e] text-center text-xs font-mono text-slate-500 dark:text-slate-400 space-y-2">
        <p>PAIMANA • Project Intelligence Dossier • MoSPI National Infrastructure Surveillance</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500">Asset Record {project.project_id} | Verified Against Longitudinal Flash Reports (Apr 2025 – Jun 2026)</p>
      </footer>
    </main>
  );
}
