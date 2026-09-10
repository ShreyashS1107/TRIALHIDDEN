'use client';

import React from 'react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { HelpCircle, AlertCircle, TrendingDown, Clock, IndianRupee } from 'lucide-react';

interface Props {
  project: ProjectSearchRecord;
}

export function RiskDriversView({ project }: Props) {
  const hasML = project.has_ml_telemetry;

  // Derive driver impacts from authentic ML contributions or fallback heuristics
  const schedRisk = project.schedule_delay_risk !== null ? project.schedule_delay_risk : 0.2;
  const costRisk = project.cost_overrun_risk !== null ? project.cost_overrun_risk : 0.1;
  const revRisk = project.schedule_revision_risk !== null ? project.schedule_revision_risk : 0.05;

  // Physical progress drag
  const progressLag = Math.max(0, 1 - (project.physical_progress_percent / 100));

  const drivers = [
    {
      id: 'schedule_delay',
      title: 'Schedule Slippage & Milestone Drag',
      category: 'MODEL-DERIVED SIGNAL' as const,
      desc: project.has_revision
        ? 'Project has recorded milestone extensions, compressing downstream delivery windows.'
        : 'Critical path target approaching while physical completion remains incomplete.',
      icon: <Clock className="w-4 h-4 text-amber-500" />,
      impactValue: Math.round(schedRisk * 100),
      impactLabel: schedRisk >= 0.7 ? 'High impact' : schedRisk >= 0.3 ? 'Medium impact' : 'Low impact',
      impactColor: schedRisk >= 0.7 ? 'bg-rose-500' : schedRisk >= 0.3 ? 'bg-amber-500' : 'bg-cyan-500'
    },
    {
      id: 'cost_escalation',
      title: 'Cost Escalation & Budget Variance',
      category: 'OBSERVED PROJECT METRIC' as const,
      desc: project.cost_variance_percent > 0
        ? `Budget revised upwards with +${project.cost_variance_percent}% capital variance.`
        : 'Sanctioned budget remains within nominal threshold without major baseline hike.',
      icon: <IndianRupee className="w-4 h-4 text-cyan-500" />,
      impactValue: Math.round(costRisk * 100),
      impactLabel: costRisk >= 0.5 ? 'High impact' : costRisk >= 0.2 ? 'Medium impact' : 'Low impact',
      impactColor: costRisk >= 0.5 ? 'bg-rose-500' : costRisk >= 0.2 ? 'bg-amber-500' : 'bg-cyan-500'
    },
    {
      id: 'physical_progress',
      title: 'Physical Completion Velocity',
      category: 'OBSERVED PROJECT METRIC' as const,
      desc: `Physical execution currently certified at ${project.physical_progress_percent}%. Remaining scope requires accelerated burn.`,
      icon: <TrendingDown className="w-4 h-4 text-emerald-500" />,
      impactValue: Math.round(progressLag * 80),
      impactLabel: project.physical_progress_percent < 50 ? 'High impact' : project.physical_progress_percent < 80 ? 'Medium impact' : 'Low impact',
      impactColor: project.physical_progress_percent < 50 ? 'bg-rose-500' : project.physical_progress_percent < 80 ? 'bg-amber-500' : 'bg-emerald-500'
    },
    {
      id: 'revision_risk',
      title: 'Schedule Revision Event Probability',
      category: 'MODEL-DERIVED SIGNAL' as const,
      desc: project.has_revision
        ? 'Project has previously recorded completion date adjustments.'
        : 'Likelihood of imminent administrative schedule re-baselining based on historical reporting cadence.',
      icon: <AlertCircle className="w-4 h-4 text-purple-500" />,
      impactValue: Math.round(revRisk * 100),
      impactLabel: revRisk >= 0.4 ? 'High impact' : revRisk >= 0.15 ? 'Medium impact' : 'Low impact',
      impactColor: revRisk >= 0.4 ? 'bg-rose-500' : revRisk >= 0.15 ? 'bg-amber-500' : 'bg-purple-500'
    }
  ];

  // Sort drivers by impactValue descending
  drivers.sort((a, b) => b.impactValue - a.impactValue);

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 06 — Root-Cause Decomposition
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            TOP RISK DRIVERS
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Decomposed risk factors explaining why the ML model prioritizes or flags this infrastructure asset.
          </p>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>WHY IS THIS PROJECT AT RISK?</span>
        </div>
      </div>

      {/* Horizontal Impact Bars */}
      <div className="space-y-4 pt-1">
        {drivers.map((driver, index) => (
          <div
            key={driver.id}
            className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2.5 transition-all hover:border-cyan-500/30"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-white/10 text-[11px] font-mono font-bold flex items-center justify-center text-slate-700 dark:text-slate-300">
                  {index + 1}
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-sm text-slate-900 dark:text-white">
                    {driver.title}
                  </span>
                  <span
                    className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                      driver.category === 'MODEL-DERIVED SIGNAL'
                        ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                        : 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                    }`}
                  >
                    {driver.category}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                    driver.impactLabel === 'High impact'
                      ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                      : driver.impactLabel === 'Medium impact'
                      ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                      : 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                  }`}
                >
                  {driver.impactLabel}
                </span>
                <span className="text-xs font-mono font-bold text-slate-900 dark:text-white min-w-[36px] text-right">
                  {driver.impactValue}%
                </span>
              </div>
            </div>

            {/* Impact Bar */}
            <div className="w-full bg-slate-200 dark:bg-white/10 h-2 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${driver.impactColor} transition-all duration-500`}
                style={{ width: `${Math.max(4, driver.impactValue)}%` }}
              />
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-400 pt-0.5">
              {driver.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
