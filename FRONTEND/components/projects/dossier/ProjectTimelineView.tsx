'use client';

import React from 'react';
import { ProjectSearchRecord, ProjectHistoricalRecord } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';
import { CheckCircle2, Clock, Calendar, Flag, AlertCircle, FileSpreadsheet } from 'lucide-react';

interface Props {
  project: ProjectSearchRecord;
  timeline: ProjectHistoricalRecord[];
}

export function ProjectTimelineView({ project, timeline }: Props) {
  const approval = project.approval_start_date || 'N/A';
  const origTarget = project.original_completion_date || 'Not Specified';
  const expectedEnd = project.has_revision && project.revised_completion_date
    ? project.revised_completion_date
    : origTarget;

  // Key milestones constructed from actual longitudinal epochs
  const firstSnapshot = timeline.length > 0 ? timeline[0] : null;
  const midSnapshot = timeline.length > 2 ? timeline[Math.floor(timeline.length / 2)] : null;
  const latestSnapshot = timeline.length > 0 ? timeline[timeline.length - 1] : null;

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 08 — Lifecycle Milestones
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            PROJECT LIFECYCLE TIMELINE
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Chronological audit of sanction approvals, baseline targets, longitudinal reporting epochs, and completion horizons.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-500 dark:text-slate-400">
          Total Recorded Epochs: <strong className="text-cyan-600 dark:text-cyan-400 font-bold">{timeline.length || project.total_snapshots}</strong>
        </div>
      </div>

      {/* Timeline track */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-2.5 sm:before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-white/10">
        {/* Milestone 1: Approval */}
        <div className="relative flex items-start gap-4">
          <div className="absolute -left-6 sm:-left-8 mt-1 w-5 h-5 rounded-full bg-cyan-500/20 border-2 border-cyan-500 flex items-center justify-center">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                1. Project Inception & Approval
              </span>
              <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded">
                {approval}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              Sanctioned by {project.agency} with initial baseline cost of ₹{formatIndianNumber(project.original_cost_crore)} Crore.
            </p>
          </div>
        </div>

        {/* Milestone 2: Baseline Target Milestone */}
        <div className="relative flex items-start gap-4">
          <div className="absolute -left-6 sm:-left-8 mt-1 w-5 h-5 rounded-full bg-slate-400/20 border-2 border-slate-400 flex items-center justify-center">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                2. Original Scheduled Completion (DOC)
              </span>
              <span className="text-xs font-mono text-slate-700 dark:text-slate-300 font-bold bg-slate-200 dark:bg-white/10 px-2 py-0.5 rounded">
                {origTarget}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              Original planned Date of Commissioning formally approved at investment decision.
            </p>
          </div>
        </div>

        {/* Milestone 3: Longitudinal Reporting Ingestion */}
        {firstSnapshot && (
          <div className="relative flex items-start gap-4">
            <div className="absolute -left-6 sm:-left-8 mt-1 w-5 h-5 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                  3. Early Surveillance Epoch
                </span>
                <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded">
                  {firstSnapshot.report_month}
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                First longitudinal record: Physical progress at {firstSnapshot.physical_progress_percent}%, cumulative spend ₹{formatIndianNumber(firstSnapshot.cumulative_expenditure_crore)} Cr.
              </p>
            </div>
          </div>
        )}

        {/* Milestone 4: Revisions (if any) */}
        {project.has_revision && (
          <div className="relative flex items-start gap-4">
            <div className="absolute -left-6 sm:-left-8 mt-1 w-5 h-5 rounded-full bg-amber-500/20 border-2 border-amber-500 flex items-center justify-center">
              <AlertCircle className="w-3 h-3 text-amber-500" />
            </div>
            <div className="p-3.5 rounded-xl bg-amber-500/5 border border-amber-500/30 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wide">
                  4. Schedule / Cost Revision Event
                </span>
                <span className="text-xs font-mono text-amber-600 dark:text-amber-400 font-bold bg-amber-500/10 px-2 py-0.5 rounded">
                  {project.revised_completion_date}
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                Target commissioning extended to {project.revised_completion_date}. Revised cost anticipated at ₹{formatIndianNumber(project.revised_cost_crore)} Cr.
              </p>
            </div>
          </div>
        )}

        {/* Milestone 5: Latest Status */}
        <div className="relative flex items-start gap-4">
          <div className="absolute -left-6 sm:-left-8 mt-1 w-5 h-5 rounded-full bg-cyan-500/20 border-2 border-cyan-500 flex items-center justify-center">
            <CheckCircle2 className="w-3 h-3 text-cyan-500" />
          </div>
          <div className="p-3.5 rounded-xl bg-cyan-500/5 border border-cyan-500/30 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-cyan-700 dark:text-cyan-400 uppercase tracking-wide">
                5. Latest Monitoring Status
              </span>
              <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded">
                {project.last_reported_month}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              Certified physical progress reached <strong className="text-slate-900 dark:text-white font-mono">{project.physical_progress_percent}%</strong> with cumulative expenditure of <strong className="text-slate-900 dark:text-white font-mono">₹{formatIndianNumber(project.cumulative_expenditure_crore)} Cr</strong>.
            </p>
          </div>
        </div>

        {/* Milestone 6: Expected Completion */}
        <div className="relative flex items-start gap-4">
          <div className="absolute -left-6 sm:-left-8 mt-1 w-5 h-5 rounded-full bg-purple-500/20 border-2 border-purple-500 flex items-center justify-center">
            <Flag className="w-3 h-3 text-purple-500" />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wide">
                6. Expected Commissioning Horizon
              </span>
              <span className="text-xs font-mono text-purple-600 dark:text-purple-400 font-bold bg-purple-500/10 px-2 py-0.5 rounded">
                {expectedEnd}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              Active target window for full operational handover and commissioning.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
