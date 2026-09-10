'use client';

import React from 'react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';
import { IndianRupee, Calendar, TrendingUp, Activity, FileText } from 'lucide-react';

interface Props {
  project: ProjectSearchRecord;
}

export function ProjectSnapshotCards({ project }: Props) {
  const origCost = project.original_cost_crore || 0;
  const revCost = project.revised_cost_crore || origCost;
  const variancePct = project.cost_variance_percent;

  const origComp = project.original_completion_date || 'Not Specified';
  const revComp = project.has_revision && project.revised_completion_date
    ? project.revised_completion_date
    : 'No revision recorded.';

  const progress = project.physical_progress_percent ?? 0;
  const latestReport = project.last_reported_month || '2026-06';

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 01 — Baseline Telemetry
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            PROJECT SNAPSHOT
          </h2>
        </div>
        <div className="text-xs font-mono text-slate-500 dark:text-slate-400">
          Source: Official MoSPI Flash Telemetry
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3">
        {/* Card 1: ORIGINAL COST */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Original Cost</span>
            <IndianRupee className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="mt-3">
            <div className="text-lg sm:text-xl font-bold font-mono text-slate-900 dark:text-white truncate">
              ₹{formatIndianNumber(origCost)}
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              ₹ Crore
            </div>
          </div>
        </div>

        {/* Card 2: REVISED COST */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Revised Cost</span>
            <IndianRupee className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="mt-3">
            <div className="text-lg sm:text-xl font-bold font-mono text-slate-900 dark:text-white truncate">
              ₹{formatIndianNumber(revCost)}
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              ₹ Crore
            </div>
          </div>
        </div>

        {/* Card 3: COST VARIANCE */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Cost Variance</span>
            <TrendingUp className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="mt-3">
            <div
              className={`text-lg sm:text-xl font-bold font-mono ${
                variancePct > 0
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-slate-700 dark:text-slate-200'
              }`}
            >
              {variancePct > 0 ? `+${variancePct}%` : `${variancePct}%`}
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              {variancePct > 0 ? 'Escalation' : 'Nominal'}
            </div>
          </div>
        </div>

        {/* Card 4: ORIGINAL COMPLETION */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Original Target</span>
            <Calendar className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="mt-3">
            <div className="text-sm sm:text-base font-bold font-mono text-slate-900 dark:text-white truncate">
              {origComp}
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              Approved Horizon
            </div>
          </div>
        </div>

        {/* Card 5: REVISED COMPLETION */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Revised Target</span>
            <Calendar className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="mt-3">
            <div
              className={`text-sm sm:text-base font-bold font-mono ${
                project.has_revision
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-slate-600 dark:text-slate-300'
              }`}
            >
              {revComp}
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 truncate">
              {project.has_revision ? 'Revision Recorded' : 'No Extension'}
            </div>
          </div>
        </div>

        {/* Card 6: PHYSICAL PROGRESS */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Progress</span>
            <Activity className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="mt-3">
            <div className="text-lg sm:text-xl font-bold font-mono text-cyan-600 dark:text-cyan-400">
              {progress}%
            </div>
            <div className="w-full bg-slate-200 dark:bg-white/10 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-cyan-500 h-full rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          </div>
        </div>

        {/* Card 7: LATEST REPORT */}
        <div className="p-4 rounded-xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-mono uppercase">
            <span>Latest Report</span>
            <FileText className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="mt-3">
            <div className="text-sm sm:text-base font-bold font-mono text-slate-900 dark:text-white">
              {latestReport}
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              Reporting Epoch
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
