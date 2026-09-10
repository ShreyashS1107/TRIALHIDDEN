'use client';

import React, { useState } from 'react';
import { LineChart, Calendar, TrendingUp, ArrowRight, Activity, ShieldAlert } from 'lucide-react';
import { ProjectDetail } from '@/lib/api/types';

interface Section11Props {
  projects?: ProjectDetail[];
}

export default function Section11_LongitudinalTimeline({ projects = [] }: Section11Props) {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const activeProj = projects[selectedIdx] || projects[0];

  if (!activeProj) return null;

  const trajectory = activeProj.longitudinal_trajectory || [];

  return (
    <section id="longitudinal-timeline" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <Calendar className="w-3.5 h-3.5" />
              <span>SECTION 11 • POINT-IN-TIME TRAJECTORY</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              PROJECTS ARE NOT STATIC.
              <span className="block text-cyan">THEIR TRAJECTORY TELLS THE STORY.</span>
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Audit the exact historical trajectory across 15 monthly reporting epochs. Observe month-by-month changes in physical execution pace and cumulative capital deployment.
          </p>
        </div>

        {/* Project Selector Mini Bar */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          {projects.slice(0, 6).map((p, idx) => (
            <button
              key={p.project_id}
              onClick={() => setSelectedIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap transition-all border ${
                selectedIdx === idx
                  ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                  : 'bg-navy-900 border-concrete-700/50 text-concrete-400 hover:text-white'
              }`}
            >
              {p.project_id}: {p.project_name.slice(0, 22)}...
            </button>
          ))}
        </div>

        {/* Longitudinal History Chart Card */}
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-cyan-500/20 mb-8">
            <div>
              <span className="text-xs font-mono text-cyan-300">
                15-Month Chronological Audit • Project {activeProj.project_id}
              </span>
              <h3 className="text-xl font-bold text-white mt-1">
                {activeProj.project_name}
              </h3>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-cyan">
                <span className="w-3 h-1 bg-cyan rounded-full" /> Physical Progress (%)
              </span>
              <span className="flex items-center gap-1.5 text-teal">
                <span className="w-3 h-1 bg-teal rounded-full" /> Expenditure Incurred (₹ Cr)
              </span>
            </div>
          </div>

          {/* Monthly Trajectory Snapshot Table / Stepper */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mb-8">
            {trajectory.map((snap, i) => (
              <div
                key={snap.report_month}
                className="p-3 rounded-xl bg-navy-950/80 border border-concrete-800 space-y-1.5 text-xs font-mono hover:border-cyan-500/40 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-cyan font-bold">{snap.report_month}</span>
                  <span className="text-[9px] text-concrete-500">M{i + 1}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-concrete-400 text-[10px] uppercase">Progress</span>
                  <span className="text-white font-bold">{snap.physical_progress_percent}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-concrete-400 text-[10px] uppercase">Spend</span>
                  <span className="text-teal font-semibold">₹{snap.cumulative_expenditure_crore.toFixed(1)} Cr</span>
                </div>
              </div>
            ))}
          </div>

          {/* SVG Animated Chart of Monthly Progression */}
          <div className="p-4 rounded-xl bg-navy-950 border border-concrete-800">
            <span className="text-[10px] font-mono text-concrete-400 uppercase block mb-2">
              Physical Progress Curve (Apr 2025 → Jun 2026)
            </span>
            <div className="w-full h-32 flex items-end gap-2 pt-4">
              {trajectory.map((snap) => {
                const heightPct = Math.max(5, Math.min(100, snap.physical_progress_percent));
                return (
                  <div key={snap.report_month} className="flex-1 flex flex-col items-center gap-1 group">
                    <span className="text-[9px] font-mono text-cyan opacity-0 group-hover:opacity-100 transition-opacity">
                      {snap.physical_progress_percent}%
                    </span>
                    <div
                      className="w-full bg-gradient-to-t from-cyan-500/30 to-cyan rounded-t transition-all duration-500 group-hover:brightness-125"
                      style={{ height: `${heightPct}%` }}
                    />
                    <span className="text-[8px] font-mono text-concrete-500 truncate w-full text-center">
                      {snap.report_month.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
