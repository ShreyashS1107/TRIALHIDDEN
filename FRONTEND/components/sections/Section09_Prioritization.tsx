'use client';

import React from 'react';
import { ShieldAlert, ArrowUpRight, CheckCircle2, ChevronRight, AlertTriangle, Layers } from 'lucide-react';
import { ProjectDetail } from '@/lib/api/types';

interface Section09Props {
  projects?: ProjectDetail[];
  onSelectProject?: (p: ProjectDetail) => void;
}

export default function Section09_Prioritization({ projects = [], onSelectProject }: Section09Props) {
  // Sort projects by composite priority (High Risk & High ESI first)
  const prioritized = [...projects].sort((a, b) => {
    const scoreA = a.predictive_risk.selected_integrated_risk * 0.5 + a.execution_profile.execution_stress_index * 0.5;
    const scoreB = b.predictive_risk.selected_integrated_risk * 0.5 + b.execution_profile.execution_stress_index * 0.5;
    return scoreB - scoreA;
  });

  return (
    <section id="prioritization" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-xs font-mono text-amber mb-3">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>SECTION 09 • DECISION-SUPPORT QUEUE</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              INTERVENTION PRIORITY
            </h2>
          </div>
          <div className="max-w-md text-xs sm:text-sm text-concrete-300">
            <p className="font-semibold text-white">
              NOT ALL PROJECTS REQUIRE THE SAME LEVEL OF ATTENTION.
            </p>
            <p className="mt-1">
              PAIMANA optimizes ministerial bandwidth by ranking ongoing assets according to multi-dimensional urgency and prescriptive action impact.
            </p>
          </div>
        </div>

        {/* Prioritized Ranked List Table */}
        <div className="space-y-4">
          {prioritized.slice(0, 6).map((proj, idx) => {
            const rank = idx + 1;
            const isHighPriority = proj.execution_profile.esi_tier === 'HIGH_PRIORITY' || proj.predictive_risk.risk_band === 'VERY_HIGH';
            const costOverrun = Math.max(0, proj.revised_cost_crore - proj.original_cost_crore);
            const slippageMonths = proj.execution_profile.schedule_slippage_months || 0;

            const priorityBadge = isHighPriority ? 'HIGH PRIORITY' : 'MEDIUM PRIORITY';
            const badgeColor = isHighPriority ? 'bg-amber-500/20 text-amber border-amber-500/40' : 'bg-cyan-500/20 text-cyan border-cyan-500/40';

            return (
              <div
                key={proj.project_id}
                className={`glass-panel p-5 sm:p-6 rounded-2xl border transition-all duration-300 hover:border-cyan-500/50 hover:bg-navy-850/80 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 ${
                  isHighPriority ? 'border-amber-500/30' : 'border-cyan-500/20'
                }`}
              >
                {/* Left: Rank & Project Identifier */}
                <div className="flex items-center gap-5">
                  <div className="text-3xl sm:text-4xl font-extrabold font-mono text-white/40 tracking-tight w-12 text-center flex-shrink-0">
                    0{rank}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-cyan font-bold">
                        ID: {proj.project_id}
                      </span>
                      <span className="text-xs text-concrete-400 font-mono">
                        • {proj.agency}
                      </span>
                      <span className="text-xs text-teal font-mono">
                        • {proj.state}
                      </span>
                    </div>
                    <h4 className="text-sm sm:text-base font-bold text-white max-w-xl line-clamp-1">
                      {proj.project_name}
                    </h4>
                  </div>
                </div>

                {/* Middle: Metrics Grid (Progress, Cost Pressure, Schedule Pressure) */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono w-full lg:w-auto">
                  <div className="p-2.5 rounded-xl bg-navy-950/80 border border-concrete-800">
                    <span className="text-[9px] uppercase font-sans text-concrete-400 block">Progress</span>
                    <span className="text-cyan font-bold text-sm">{proj.physical_progress_percent}%</span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-navy-950/80 border border-concrete-800">
                    <span className="text-[9px] uppercase font-sans text-concrete-400 block">Cost Pressure</span>
                    <span className={costOverrun > 0 ? 'text-amber font-bold text-sm' : 'text-white font-bold text-sm'}>
                      {costOverrun > 0 ? `+₹${costOverrun.toFixed(0)} Cr` : '₹0 Cr'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-navy-950/80 border border-concrete-800">
                    <span className="text-[9px] uppercase font-sans text-concrete-400 block">Schedule Debt</span>
                    <span className={slippageMonths > 6 ? 'text-amber font-bold text-sm' : 'text-white font-bold text-sm'}>
                      {slippageMonths > 0 ? `+${slippageMonths.toFixed(0)}m` : '0m'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-navy-950/80 border border-concrete-800">
                    <span className="text-[9px] uppercase font-sans text-concrete-400 block">ML Risk</span>
                    <span className="text-white font-bold text-sm">
                      {Math.round(proj.predictive_risk.selected_integrated_risk * 100)}%
                    </span>
                  </div>
                </div>

                {/* Right: Priority Tier & Action */}
                <div className="flex items-center justify-between lg:justify-end gap-4 w-full lg:w-auto pt-4 lg:pt-0 border-t lg:border-t-0 border-concrete-800">
                  <div className="text-left lg:text-right">
                    <span className={`inline-block text-[10px] font-mono px-2.5 py-1 rounded font-bold uppercase border ${badgeColor}`}>
                      {priorityBadge}
                    </span>
                    <span className="block text-[10px] text-concrete-400 font-mono mt-1">
                      {proj.execution_profile.suggested_action.directive}
                    </span>
                  </div>

                  {onSelectProject && (
                    <button
                      onClick={() => onSelectProject(proj)}
                      className="p-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan transition-all"
                      title="Inspect dossier"
                    >
                      <ArrowUpRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
