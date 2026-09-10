'use client';

import React from 'react';
import { CustomProjectPredictionResponse, CustomProjectInput } from '@/lib/api/predict';
import { Calendar, Clock, AlertTriangle, CheckCircle2, Milestone } from 'lucide-react';

interface Props {
  input: CustomProjectInput;
  prediction: CustomProjectPredictionResponse;
}

function diffMonths(ym1?: string, ym2?: string): number {
  if (!ym1 || !ym2) return 0;
  try {
    const [y1, m1] = ym1.split('-').map(Number);
    const [y2, m2] = ym2.split('-').map(Number);
    if (isNaN(y1) || isNaN(m1) || isNaN(y2) || isNaN(m2)) return 0;
    return (y1 - y2) * 12 + (m1 - m2);
  } catch {
    return 0;
  }
}

export function ScheduleTimeline({ input, prediction }: Props) {
  const approvalDate = prediction.approval_start_date || input.approval_start_date || '2022-01';
  const origDoc = prediction.original_completion_date || input.original_completion_date || '2026-12';
  const revDoc = prediction.revised_completion_date || input.revised_completion_date || origDoc;
  const predDoc = prediction.predicted_completion_date || revDoc;

  // Calculated metrics
  const originalDurationMonths = Math.max(1, diffMonths(origDoc, approvalDate));
  const currentElapsedMonths = Math.max(0, diffMonths('2026-09', approvalDate));
  const slippageMonths = Math.max(0, diffMonths(revDoc, origDoc));
  const predictedDelayMonths = Number(prediction.predicted_delay_months) || 0;

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              DELIVERY SCHEDULE INTELLIGENCE
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-500">
              MILESTONE TRAJECTORY
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            SCHEDULE MILESTONES & HORIZON FORECAST
          </h3>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
            <span className="text-slate-600 dark:text-slate-400">Observed Timeline</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
            <span className="text-slate-600 dark:text-slate-400">Model Forecast</span>
          </div>
        </div>
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Original Sanctioned Duration */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <div className="text-xs font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between">
            <span>SANCTIONED DURATION</span>
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            {originalDurationMonths} Mo
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            {approvalDate} &rarr; {origDoc}
          </div>
        </div>

        {/* Current Elapsed Duration */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <div className="text-xs font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between">
            <span>CURRENT ELAPSED</span>
            <Clock className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-600 dark:text-cyan-400">
            {currentElapsedMonths} Mo
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            {Math.round((currentElapsedMonths / originalDurationMonths) * 100)}% of original schedule elapsed
          </div>
        </div>

        {/* Milestone Slippage */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <div className="text-xs font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between">
            <span>MILESTONE SLIPPAGE</span>
            <Milestone className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-500">
            +{slippageMonths} Mo
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            Target revised to {revDoc}
          </div>
        </div>

        {/* Model Predicted Horizon */}
        <div className="p-4 rounded-xl bg-amber-500/5 dark:bg-amber-500/[0.04] border border-amber-500/30 space-y-1">
          <div className="text-xs font-mono text-amber-600 dark:text-amber-400 flex items-center justify-between font-bold">
            <span>PREDICTED DELAY</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
            +{predictedDelayMonths} Mo
          </div>
          <div className="text-[11px] font-mono text-amber-700/80 dark:text-amber-300/80">
            Forecasted: {predDoc}
          </div>
        </div>
      </div>

      {/* Visual Step Timeline */}
      <div className="p-6 rounded-xl bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/5 space-y-6">
        <div className="text-xs font-mono uppercase tracking-wider text-slate-600 dark:text-slate-400 font-semibold">
          SEQUENTIAL MILESTONE PROGRESSION
        </div>

        {/* Timeline Horizontal Track */}
        <div className="relative">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
            {/* Step 1: Inception */}
            <div className="p-4 rounded-xl bg-white dark:bg-[#06131c] border border-slate-200 dark:border-white/10 relative shadow-sm">
              <div className="flex items-center justify-between pb-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
                  01 • INCEPTION
                </span>
                <span className="text-[10px] font-mono text-slate-400">[OBSERVED]</span>
              </div>
              <div className="text-base font-bold font-mono text-slate-900 dark:text-white">
                {approvalDate}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 pt-1">
                Project approval & baseline financial sanction
              </div>
            </div>

            {/* Step 2: Current Evaluation Horizon */}
            <div className="p-4 rounded-xl bg-white dark:bg-[#06131c] border border-cyan-500/30 relative shadow-sm">
              <div className="flex items-center justify-between pb-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500 text-slate-950 font-bold">
                  02 • CURRENT
                </span>
                <span className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400 font-bold">[OBSERVED]</span>
              </div>
              <div className="text-base font-bold font-mono text-slate-900 dark:text-white">
                {input.physical_progress_percent}% Scope
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 pt-1">
                Evaluation month (Sep 2026) with {100 - input.physical_progress_percent}% scope pending
              </div>
            </div>

            {/* Step 3: Sanctioned Target */}
            <div className="p-4 rounded-xl bg-white dark:bg-[#06131c] border border-slate-200 dark:border-white/10 relative shadow-sm">
              <div className="flex items-center justify-between pb-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-white/10 text-slate-700 dark:text-slate-300 font-bold">
                  03 • TARGET DOC
                </span>
                <span className="text-[10px] font-mono text-slate-400">[OBSERVED]</span>
              </div>
              <div className="text-base font-bold font-mono text-slate-900 dark:text-white">
                {revDoc}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 pt-1">
                {slippageMonths > 0 ? `Revised target (+${slippageMonths} Mo slippage from ${origDoc})` : `Original target (${origDoc})`}
              </div>
            </div>

            {/* Step 4: Model Forecast Horizon */}
            <div className="p-4 rounded-xl bg-amber-500/10 dark:bg-amber-500/10 border border-amber-500/40 relative shadow-sm">
              <div className="flex items-center justify-between pb-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500 text-slate-950 font-bold animate-pulse">
                  04 • FORECAST
                </span>
                <span className="text-[10px] font-mono text-amber-600 dark:text-amber-400 font-bold">[MODEL PREDICTION]</span>
              </div>
              <div className="text-base font-bold font-mono text-amber-600 dark:text-amber-400">
                {predDoc}
              </div>
              <div className="text-xs text-amber-700/80 dark:text-amber-300/80 pt-1">
                Calibrated ML horizon (+{predictedDelayMonths} months total delay)
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
