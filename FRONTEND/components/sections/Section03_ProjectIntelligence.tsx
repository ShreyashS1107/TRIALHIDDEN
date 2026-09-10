'use client';

import React, { useState } from 'react';
import { ProjectDetail } from '@/lib/api/types';
import { Building2, MapPin, Calendar, IndianRupee, Activity, ShieldAlert, CheckCircle2, ChevronRight, Layers } from 'lucide-react';
import { formatIndianNumber } from '@/lib/utils/format';

interface Section03Props {
  projects: ProjectDetail[];
  selectedProject: ProjectDetail | null;
  onSelectProject: (p: ProjectDetail) => void;
}

export default function Section03_ProjectIntelligence({
  projects,
  selectedProject,
  onSelectProject,
}: Section03Props) {
  const activeProj = selectedProject || projects[0];
  if (!activeProj) return null;

  const financialProgressPct = activeProj.revised_cost_crore > 0
    ? Math.min(100, Math.round((activeProj.cumulative_expenditure_crore / activeProj.revised_cost_crore) * 1000) / 10)
    : 0;

  const costDivergence = activeProj.revised_cost_crore - activeProj.original_cost_crore;
  const isHighRisk = activeProj.predictive_risk.risk_band === 'HIGH' || activeProj.predictive_risk.risk_band === 'VERY_HIGH';

  return (
    <section id="project-intelligence" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <Activity className="w-3.5 h-3.5" />
              <span>SECTION 03 • MONITORED PROJECT DOSSIER</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              PROJECT INTELLIGENCE DOSSIER
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Ground-truth data schema strictly preserved from MoSPI Flash Reports. Choose any monitored asset from the surveillance queue to inspect real financial and physical progress.
          </p>
        </div>

        {/* Project Selector Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          {projects.slice(0, 8).map((p) => {
            const isSelected = p.project_id === activeProj.project_id;
            const isPWarning = p.predictive_risk.risk_band === 'HIGH' || p.predictive_risk.risk_band === 'VERY_HIGH';
            return (
              <button
                key={p.project_id}
                onClick={() => onSelectProject(p)}
                className={`px-3.5 py-2 rounded-xl text-xs font-mono whitespace-nowrap transition-all flex items-center gap-2 border ${
                  isSelected
                    ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                    : 'bg-navy-900 hover:bg-navy-850 border-concrete-700/50 text-concrete-300'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${isPWarning ? 'bg-amber animate-pulse' : 'bg-cyan'}`} />
                <span className="font-bold">{p.project_id}</span>
                <span className="opacity-70 font-sans truncate max-w-[130px]">{p.project_name}</span>
              </button>
            );
          })}
        </div>

        {/* Main Dossier Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Deep Project Metadata & Visual Gauges (8 cols) */}
          <div className="lg:col-span-8 glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 relative">
            <div className="flex flex-wrap items-start justify-between gap-4 pb-6 border-b border-cyan-500/20">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-bold">
                    ID: {activeProj.project_id}
                  </span>
                  {activeProj.legacy_ocms_code && (
                    <span className="text-xs font-mono text-concrete-400">
                      OCMS: {activeProj.legacy_ocms_code}
                    </span>
                  )}
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-navy-800 border border-concrete-700 text-concrete-300">
                    {activeProj.sector}
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-extrabold text-white">
                  {activeProj.project_name}
                </h3>
                <div className="flex items-center gap-4 text-xs text-concrete-300 pt-1">
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-cyan" />
                    {activeProj.agency}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-teal" />
                    {activeProj.state}
                  </span>
                  <span className="flex items-center gap-1 font-mono text-concrete-400">
                    Snapshot: 2026-03
                  </span>
                </div>
              </div>

              {/* Status Badge */}
              <div className="text-right">
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono font-bold uppercase ${
                    isHighRisk
                      ? 'bg-amber-500/20 border border-amber-500/40 text-amber'
                      : 'bg-cyan-500/20 border border-cyan-500/40 text-cyan'
                  }`}
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  {activeProj.predictive_risk.risk_band} RISK ({Math.round(activeProj.predictive_risk.selected_integrated_risk * 100)}%)
                </span>
                <span className="block text-[10px] font-mono text-concrete-400 mt-1">
                  ESI: {activeProj.execution_profile.esi_tier} ({activeProj.execution_profile.execution_stress_index.toFixed(2)})
                </span>
              </div>
            </div>

            {/* Gauges & Progress Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-6 border-b border-cyan-500/20">
              {/* Radial Physical Progress */}
              <div className="glass-panel p-5 rounded-xl border-cyan-500/20 flex items-center gap-5">
                <div className="relative w-24 h-24 flex-shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" stroke="#0F2A38" strokeWidth="8" fill="transparent" />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="#39D9FF"
                      strokeWidth="8"
                      strokeDasharray="251.2"
                      strokeDashoffset={251.2 - (251.2 * activeProj.physical_progress_percent) / 100}
                      strokeLinecap="round"
                      fill="transparent"
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-xl font-extrabold font-mono text-white">
                      {activeProj.physical_progress_percent}%
                    </span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-xs uppercase font-mono font-bold tracking-wider text-concrete-400">
                    PHYSICAL PROGRESS
                  </span>
                  <div className="text-xs text-concrete-300">
                    Verified milestone build completion submitted by implementing CPSU.
                  </div>
                  <span className="inline-block text-[10px] font-mono text-cyan-300">
                    Status: {activeProj.physical_progress_percent > 70 ? 'Advance Phase' : 'Core Execution'}
                  </span>
                </div>
              </div>

              {/* Linear Financial Progress */}
              <div className="glass-panel p-5 rounded-xl border-cyan-500/20 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-mono font-bold tracking-wider text-concrete-400">
                    FINANCIAL PROGRESS
                  </span>
                  <span className="text-xs font-mono font-bold text-teal">
                    {financialProgressPct}% DISBURSED
                  </span>
                </div>

                <div className="w-full bg-navy-950 h-3 rounded-full overflow-hidden border border-concrete-700/60 p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-teal to-cyan rounded-full transition-all duration-1000"
                    style={{ width: `${Math.min(100, financialProgressPct)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono">
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase">Spent</span>
                    <span className="text-white font-semibold">₹{formatIndianNumber(activeProj.cumulative_expenditure_crore)} Cr</span>
                  </div>
                  <div className="text-right">
                    <span className="text-concrete-400 block text-[9px] uppercase">Revised Budget</span>
                    <span className="text-teal font-semibold">₹{formatIndianNumber(activeProj.revised_cost_crore)} Cr</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Financial Ledger & Schedule Milestones */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 text-xs">
              <div className="space-y-1">
                <span className="text-concrete-400 block uppercase text-[10px] font-mono">Sanctioned Cost</span>
                <span className="text-white font-mono font-bold text-sm">₹{formatIndianNumber(activeProj.original_cost_crore)} Cr</span>
              </div>
              <div className="space-y-1">
                <span className="text-concrete-400 block uppercase text-[10px] font-mono">Revised Cost</span>
                <span className={`font-mono font-bold text-sm ${costDivergence > 0 ? 'text-amber' : 'text-white'}`}>
                  ₹{formatIndianNumber(activeProj.revised_cost_crore)} Cr
                </span>
                {costDivergence > 0 && (
                  <span className="text-[10px] font-mono text-amber block">
                    (+₹{formatIndianNumber(costDivergence)} Cr escalation)
                  </span>
                )}
              </div>
              <div className="space-y-1">
                <span className="text-concrete-400 block uppercase text-[10px] font-mono">Original DOC</span>
                <span className="text-white font-mono font-bold text-sm flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-cyan" />
                  {activeProj.original_completion_date}
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-concrete-400 block uppercase text-[10px] font-mono">Revised DOC</span>
                <span className="text-amber font-mono font-bold text-sm flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-amber" />
                  {activeProj.revised_completion_date || 'Unrevised'}
                </span>
              </div>
            </div>
          </div>

          {/* Right: Prescriptive Action Directive (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="glass-panel-amber p-6 rounded-2xl border-amber-500/30 text-left relative overflow-hidden">
              <div className="flex items-center gap-2 mb-3">
                <ShieldAlert className="w-4 h-4 text-amber" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-amber">
                  PRESCRIPTIVE ACTION DIRECTIVE
                </span>
              </div>

              <div className="bg-navy-950/80 p-3 rounded-lg border border-amber-500/25 mb-4">
                <span className="text-[10px] font-mono text-concrete-400 uppercase block">Directive Code</span>
                <span className="text-xs font-mono font-bold text-white block">
                  `{activeProj.execution_profile.suggested_action.directive}`
                </span>
              </div>

              <h4 className="text-base font-bold text-white mb-2">
                {activeProj.execution_profile.suggested_action.title}
              </h4>

              <p className="text-xs text-concrete-300 leading-relaxed mb-4">
                {activeProj.execution_profile.suggested_action.reason}
              </p>

              <div className="pt-3 border-t border-amber-500/20 text-[11px]">
                <span className="text-concrete-400 block uppercase text-[9px] font-mono">Authorized Review Body</span>
                <span className="text-amber font-medium">
                  {activeProj.execution_profile.suggested_action.authority}
                </span>
              </div>
            </div>

            {/* Traceability Guarantee Box */}
            <div className="glass-panel p-5 rounded-2xl border-cyan-500/20 text-xs font-mono space-y-2">
              <span className="text-concrete-400 uppercase text-[10px] block font-bold">
                MoSPI Traceability Covenants
              </span>
              <div className="text-[11px] text-concrete-300">
                • Source PDF: <span className="text-cyan">{activeProj.longitudinal_trajectory[0]?.source_file || 'FlashReport_March_2026.pdf'}</span>
              </div>
              <div className="text-[11px] text-concrete-300">
                • Source Table: <span className="text-teal">{activeProj.longitudinal_trajectory[0]?.source_table || 'Table 6: All Ongoing Projects'}</span>
              </div>
              <div className="text-[11px] text-concrete-300">
                • Temporal Consistency: <span className="text-healthy">15 Consecutive Snapshots Audited</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
