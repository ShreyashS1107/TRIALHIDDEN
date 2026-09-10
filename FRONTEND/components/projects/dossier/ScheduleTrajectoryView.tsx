'use client';

import React from 'react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { Calendar, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface Props {
  project: ProjectSearchRecord;
}

export function ScheduleTrajectoryView({ project }: Props) {
  const approval = project.approval_start_date || 'N/A';
  const origComp = project.original_completion_date || 'Not Specified';
  const revComp = project.has_revision && project.revised_completion_date
    ? project.revised_completion_date
    : 'No revision recorded.';

  // Calculate delay months if both dates are available
  let delayMonths = 0;
  if (project.has_revision && project.original_completion_date && project.revised_completion_date) {
    const [origY, origM] = project.original_completion_date.split('-').map(Number);
    const [revY, revM] = project.revised_completion_date.split('-').map(Number);
    if (!isNaN(origY) && !isNaN(origM) && !isNaN(revY) && !isNaN(revM)) {
      delayMonths = Math.max(0, (revY - origY) * 12 + (revM - origM));
    }
  }

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 03 — Timeline Surveillance
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            SCHEDULE TRAJECTORY & SLIPPAGE
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Evolution of target commissioning horizon, revision milestones, and accumulated schedule debt.
          </p>
        </div>

        {/* Delay Status Chip */}
        <div className="flex items-center gap-2">
          {delayMonths > 0 ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
              <AlertTriangle className="w-3.5 h-3.5" />
              {delayMonths} MONTHS SCHEDULE SLIPPAGE
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              NO EXTENSION DEBT RECORDED
            </span>
          )}
        </div>
      </div>

      {/* Visual Timeline Bar */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10">
        <div className="relative pt-2 pb-6">
          {/* Base Track */}
          <div className="h-3 w-full bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden flex">
            <div className="h-full bg-cyan-500 rounded-l-full" style={{ width: delayMonths > 0 ? '70%' : '100%' }} />
            {delayMonths > 0 && (
              <div
                className="h-full bg-amber-500 dark:bg-amber-400 rounded-r-full animate-pulse"
                style={{ width: '30%' }}
              />
            )}
          </div>

          {/* Timeline Nodes */}
          <div className="flex justify-between items-start mt-3 text-xs font-mono">
            {/* Start Node */}
            <div className="space-y-0.5">
              <span className="text-[10px] uppercase text-slate-400 dark:text-slate-500 block">Sanctioned</span>
              <span className="font-bold text-slate-900 dark:text-white">{approval}</span>
            </div>

            {/* Original Target Node */}
            <div className="space-y-0.5 text-center">
              <span className="text-[10px] uppercase text-slate-400 dark:text-slate-500 block">Original DOC</span>
              <span className="font-bold text-cyan-600 dark:text-cyan-400">{origComp}</span>
            </div>

            {/* Revised Target Node */}
            <div className="space-y-0.5 text-right">
              <span className="text-[10px] uppercase text-slate-400 dark:text-slate-500 block">Revised DOC</span>
              <span
                className={`font-bold ${
                  project.has_revision
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                {revComp}
              </span>
            </div>
          </div>
        </div>

        {/* Descriptive Annotation */}
        <div className="pt-3 border-t border-slate-200 dark:border-white/10 flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400">
          <Clock className="w-4 h-4 text-cyan-500 flex-shrink-0 mt-0.5" />
          <div>
            {project.has_revision ? (
              <span>
                Project target completion date was officially revised from <strong className="text-slate-900 dark:text-white font-mono">{origComp}</strong> to{' '}
                <strong className="text-amber-600 dark:text-amber-400 font-mono">{revComp}</strong>, introducing an accumulated slippage debt of{' '}
                <strong className="text-amber-600 dark:text-amber-400 font-mono">{delayMonths} months</strong>.
              </span>
            ) : (
              <span>
                <strong className="text-emerald-600 dark:text-emerald-400">No revision recorded.</strong> The project continues to be monitored against its original sanctioned completion baseline of{' '}
                <strong className="text-slate-900 dark:text-white font-mono">{origComp}</strong> without any approved timeline extension.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
