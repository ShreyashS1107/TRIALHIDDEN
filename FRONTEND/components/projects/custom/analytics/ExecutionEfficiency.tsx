'use client';

import React from 'react';
import { CustomProjectPredictionResponse, CustomProjectInput } from '@/lib/api/predict';
import { formatIndianNumber } from '@/lib/utils/format';
import { Activity, AlertTriangle, CheckCircle2, TrendingUp, HelpCircle } from 'lucide-react';

interface Props {
  input: CustomProjectInput;
  prediction: CustomProjectPredictionResponse;
}

export function ExecutionEfficiency({ input, prediction }: Props) {
  const prog = Math.min(100, Math.max(0, Number(prediction.physical_progress_percent ?? input.physical_progress_percent) || 0));
  const revCost = Number(prediction.revised_cost_crore ?? input.revised_cost_crore) || Number(input.original_cost_crore) || 1;
  const spend = prediction.cumulative_expenditure_crore !== undefined && prediction.cumulative_expenditure_crore !== null
    ? Number(prediction.cumulative_expenditure_crore)
    : (input.cumulative_expenditure_crore !== undefined && input.cumulative_expenditure_crore !== null ? Number(input.cumulative_expenditure_crore) : null);

  const hasSpend = spend !== null && spend >= 0 && revCost > 0;
  const expRatio = hasSpend ? (spend / revCost) * 100 : null;

  // Divergence between capital expenditure ratio and physical progress
  const divergence = expRatio !== null ? expRatio - prog : null;

  let statusTitle = 'Execution Aligned';
  let statusDesc = 'Physical milestone completion is commensurate with or leading capital disbursements.';
  let statusBadge = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
  let statusIcon = CheckCircle2;

  if (expRatio !== null && divergence !== null) {
    if (divergence > 15) {
      statusTitle = 'Capital Front-Loading Warning';
      statusDesc = `Expenditure ratio (${expRatio.toFixed(1)}%) leads physical completion (${prog.toFixed(1)}%) by +${divergence.toFixed(1)}%. Financial disbursements have significantly outrun verified on-site scope.`;
      statusBadge = 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
      statusIcon = AlertTriangle;
    } else if (divergence > 5) {
      statusTitle = 'Moderate Capital Lead';
      statusDesc = `Expenditure ratio (${expRatio.toFixed(1)}%) marginally leads physical completion (${prog.toFixed(1)}%) by +${divergence.toFixed(1)}%, within acceptable material mobilization thresholds.`;
      statusBadge = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
      statusIcon = TrendingUp;
    }
  }

  const StatusIconComponent = statusIcon;

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              PHYSICAL VS FINANCIAL CONVERGENCE
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
              OBSERVED PROJECT METRIC
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            EXECUTION EFFICIENCY SIGNAL
          </h3>
        </div>

        <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 max-w-xs text-right hidden sm:block">
          * Derived deterministically from intake progress and expenditure data. Not an ML model prediction.
        </div>
      </div>

      {/* Comparison Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Physical Progress */}
        <div className="p-5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
            <span>PHYSICAL PROGRESS</span>
            <span className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400">[OBSERVED]</span>
          </div>
          <div className="text-3xl font-extrabold font-mono text-cyan-600 dark:text-cyan-400">
            {prog.toFixed(1)}%
          </div>
          {/* Progress Bar */}
          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${prog}%` }} />
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            Certified on-site scope completed
          </div>
        </div>

        {/* Metric 2: Expenditure Ratio */}
        <div className="p-5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
            <span>EXPENDITURE RATIO</span>
            <span className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400">[OBSERVED]</span>
          </div>
          <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
            {expRatio !== null ? `${expRatio.toFixed(1)}%` : 'Not available'}
          </div>
          {/* Progress Bar */}
          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div
              className="h-full bg-slate-700 dark:bg-slate-300 rounded-full"
              style={{ width: `${Math.min(100, expRatio || 0)}%` }}
            />
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            {hasSpend
              ? `₹${formatIndianNumber(spend)} Cr spent of ₹${formatIndianNumber(revCost)} Cr budget`
              : 'Cumulative spend not submitted'}
          </div>
        </div>

        {/* Metric 3: Convergence Divergence */}
        <div className="p-5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
            <span>BURN DIVERGENCE</span>
            <span className="text-[10px] font-bold text-slate-400">[DELTA]</span>
          </div>
          <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
            {divergence !== null ? (
              <span className={divergence > 15 ? 'text-rose-600 dark:text-rose-400' : (divergence > 0 ? 'text-amber-500' : 'text-emerald-500')}>
                {divergence >= 0 ? `+${divergence.toFixed(1)}%` : `${divergence.toFixed(1)}%`}
              </span>
            ) : (
              'N/A'
            )}
          </div>
          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                (divergence || 0) > 15 ? 'bg-rose-500' : ((divergence || 0) > 0 ? 'bg-amber-500' : 'bg-emerald-500')
              }`}
              style={{ width: `${Math.min(100, Math.abs(divergence || 0) * 3)}%` }}
            />
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            {divergence !== null ? 'Disbursement lead over physical scope' : 'Requires expenditure data'}
          </div>
        </div>
      </div>

      {/* Signal Callout Banner */}
      {hasSpend && (
        <div className={`p-4 rounded-xl border ${statusBadge} flex items-start gap-3`}>
          <StatusIconComponent className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs">
            <div className="font-mono font-bold uppercase tracking-wider">
              {statusTitle}
            </div>
            <p className="font-sans leading-relaxed text-slate-700 dark:text-slate-300">
              {statusDesc}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
