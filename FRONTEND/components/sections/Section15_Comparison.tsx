'use client';

import React, { useState } from 'react';
import { GitCompare, Building2, MapPin, IndianRupee, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { ProjectDetail } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';

interface Section15Props {
  projects?: ProjectDetail[];
}

export default function Section15_Comparison({ projects = [] }: Section15Props) {
  const [projIdA, setProjIdA] = useState<string>(projects[0]?.project_id || '105236');
  const [projIdB, setProjIdB] = useState<string>(projects[1]?.project_id || '400178');

  const projA = projects.find((p) => p.project_id === projIdA) || projects[0];
  const projB = projects.find((p) => p.project_id === projIdB) || projects[1] || projects[0];

  if (!projA || !projB) return null;

  return (
    <section id="comparison" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <GitCompare className="w-3.5 h-3.5" />
              <span>SECTION 15 • SIDE-BY-SIDE BENCHMARKING</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              PROJECT COMPARISON
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Compare two monitored infrastructure assets side-by-side across capital escalation, build pace, execution friction, and ML risk vulnerability.
          </p>
        </div>

        {/* Project Dropdown Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="glass-panel p-4 rounded-xl border-cyan-500/30 flex items-center justify-between">
            <span className="text-xs font-mono text-cyan font-bold">PROJECT A:</span>
            <select
              value={projIdA}
              onChange={(e) => setProjIdA(e.target.value)}
              className="bg-navy-950 border border-cyan-500/30 text-white rounded-lg px-3 py-1.5 text-xs font-mono outline-none max-w-xs"
            >
              {projects.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.project_id}: {p.project_name.slice(0, 30)}...
                </option>
              ))}
            </select>
          </div>

          <div className="glass-panel p-4 rounded-xl border-teal-500/30 flex items-center justify-between">
            <span className="text-xs font-mono text-teal font-bold">PROJECT B:</span>
            <select
              value={projIdB}
              onChange={(e) => setProjIdB(e.target.value)}
              className="bg-navy-950 border border-teal-500/30 text-white rounded-lg px-3 py-1.5 text-xs font-mono outline-none max-w-xs"
            >
              {projects.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.project_id}: {p.project_name.slice(0, 30)}...
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Visual Comparative Matrix Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Card A */}
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 space-y-6">
            <div className="pb-4 border-b border-cyan-500/20">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-xs font-mono text-cyan font-bold">
                  ID: {projA.project_id}
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    projA.predictive_risk.risk_band === 'HIGH' || projA.predictive_risk.risk_band === 'VERY_HIGH'
                      ? 'bg-amber-500/20 text-amber border border-amber-500/40'
                      : 'bg-cyan-500/20 text-cyan border border-cyan-500/40'
                  }`}
                >
                  {projA.predictive_risk.risk_band} RISK ({Math.round(projA.predictive_risk.selected_integrated_risk * 100)}%)
                </span>
              </div>
              <h4 className="text-base font-extrabold text-white line-clamp-2">
                {projA.project_name}
              </h4>
              <div className="flex items-center gap-3 text-xs text-concrete-400 mt-2 font-mono">
                <span>{projA.agency}</span>
                <span>•</span>
                <span>{projA.state}</span>
                <span>•</span>
                <span>{projA.sector}</span>
              </div>
            </div>

            {/* Visual Bars Comparison for A */}
            <div className="space-y-4 text-xs font-mono">
              <div>
                <div className="flex justify-between text-concrete-300 mb-1">
                  <span>PHYSICAL PROGRESS</span>
                  <span className="text-cyan font-bold">{projA.physical_progress_percent}%</span>
                </div>
                <div className="w-full bg-navy-950 h-2.5 rounded-full overflow-hidden p-0.5">
                  <div className="h-full bg-cyan rounded-full" style={{ width: `${projA.physical_progress_percent}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-concrete-300 mb-1">
                  <span>BUDGET UTILIZATION</span>
                  <span className="text-teal font-bold">
                    {Math.round((projA.cumulative_expenditure_crore / (projA.revised_cost_crore || 1)) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-navy-950 h-2.5 rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-teal rounded-full"
                    style={{ width: `${Math.min(100, Math.round((projA.cumulative_expenditure_crore / (projA.revised_cost_crore || 1)) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-2.5 rounded-xl bg-navy-950 border border-concrete-800">
                  <span className="text-[9px] uppercase text-concrete-400 block font-sans">Revised Cost</span>
                  <span className="text-white font-bold text-sm">₹{formatIndianNumber(projA.revised_cost_crore)} Cr</span>
                </div>
                <div className="p-2.5 rounded-xl bg-navy-950 border border-concrete-800">
                  <span className="text-[9px] uppercase text-concrete-400 block font-sans">Schedule DOC</span>
                  <span className="text-white font-bold text-sm">{projA.revised_completion_date}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card B */}
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border-teal-500/30 space-y-6">
            <div className="pb-4 border-b border-teal-500/20">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-xs font-mono text-teal font-bold">
                  ID: {projB.project_id}
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    projB.predictive_risk.risk_band === 'HIGH' || projB.predictive_risk.risk_band === 'VERY_HIGH'
                      ? 'bg-amber-500/20 text-amber border border-amber-500/40'
                      : 'bg-teal-500/20 text-teal border border-teal-500/40'
                  }`}
                >
                  {projB.predictive_risk.risk_band} RISK ({Math.round(projB.predictive_risk.selected_integrated_risk * 100)}%)
                </span>
              </div>
              <h4 className="text-base font-extrabold text-white line-clamp-2">
                {projB.project_name}
              </h4>
              <div className="flex items-center gap-3 text-xs text-concrete-400 mt-2 font-mono">
                <span>{projB.agency}</span>
                <span>•</span>
                <span>{projB.state}</span>
                <span>•</span>
                <span>{projB.sector}</span>
              </div>
            </div>

            {/* Visual Bars Comparison for B */}
            <div className="space-y-4 text-xs font-mono">
              <div>
                <div className="flex justify-between text-concrete-300 mb-1">
                  <span>PHYSICAL PROGRESS</span>
                  <span className="text-teal font-bold">{projB.physical_progress_percent}%</span>
                </div>
                <div className="w-full bg-navy-950 h-2.5 rounded-full overflow-hidden p-0.5">
                  <div className="h-full bg-teal rounded-full" style={{ width: `${projB.physical_progress_percent}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-concrete-300 mb-1">
                  <span>BUDGET UTILIZATION</span>
                  <span className="text-cyan font-bold">
                    {Math.round((projB.cumulative_expenditure_crore / (projB.revised_cost_crore || 1)) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-navy-950 h-2.5 rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-cyan rounded-full"
                    style={{ width: `${Math.min(100, Math.round((projB.cumulative_expenditure_crore / (projB.revised_cost_crore || 1)) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-2.5 rounded-xl bg-navy-950 border border-concrete-800">
                  <span className="text-[9px] uppercase text-concrete-400 block font-sans">Revised Cost</span>
                  <span className="text-white font-bold text-sm">₹{formatIndianNumber(projB.revised_cost_crore)} Cr</span>
                </div>
                <div className="p-2.5 rounded-xl bg-navy-950 border border-concrete-800">
                  <span className="text-[9px] uppercase text-concrete-400 block font-sans">Schedule DOC</span>
                  <span className="text-white font-bold text-sm">{projB.revised_completion_date}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
