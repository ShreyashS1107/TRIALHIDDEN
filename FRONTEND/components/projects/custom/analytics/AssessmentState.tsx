'use client';

import React from 'react';
import { CustomProjectPredictionResponse } from '@/lib/api/predict';
import { Activity, ShieldAlert, Clock, IndianRupee, Layers } from 'lucide-react';

interface Props {
  prediction: CustomProjectPredictionResponse;
}

export function AssessmentState({ prediction }: Props) {
  const schedPct = Math.round(prediction.schedule_delay_risk * 1000) / 10;
  const costPct = Math.round(prediction.cost_overrun_risk * 1000) / 10;
  const revPct = Math.round(prediction.schedule_revision_risk * 1000) / 10;
  const integratedPct = Math.round(prediction.selected_integrated_risk * 1000) / 10;

  // Weighted contributions
  const schedContrib = ((0.50 * prediction.schedule_delay_risk) * 100).toFixed(1);
  const costContrib = ((0.35 * prediction.cost_overrun_risk) * 100).toFixed(1);
  const revContrib = ((0.15 * prediction.schedule_revision_risk) * 100).toFixed(1);

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              MULTI-DIMENSIONAL DECOMPOSITION
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            CURRENT MODEL ASSESSMENT STATE
          </h3>
        </div>

        <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
          Point-in-Time Calibrated Evaluation
        </div>
      </div>

      {/* Multi-Dimensional Component Breakdown */}
      <div className="space-y-4">
        {/* Component 1: Schedule Delay */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-500" />
              <span className="font-bold text-slate-900 dark:text-white">1. Schedule Delay Probability</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-slate-500 dark:text-slate-400 text-[11px]">
                Contribution: +{schedContrib}%
              </span>
              <span className="font-bold text-cyan-600 dark:text-cyan-400">
                {schedPct}%
              </span>
            </div>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div className="h-full bg-cyan-500 rounded-full transition-all duration-500" style={{ width: `${schedPct}%` }} />
          </div>
        </div>

        {/* Component 2: Cost Overrun */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2">
              <IndianRupee className="w-4 h-4 text-amber-500" />
              <span className="font-bold text-slate-900 dark:text-white">2. Cost Overrun Probability</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-slate-500 dark:text-slate-400 text-[11px]">
                Contribution: +{costContrib}%
              </span>
              <span className="font-bold text-amber-500">
                {costPct}%
              </span>
            </div>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div className="h-full bg-amber-500 rounded-full transition-all duration-500" style={{ width: `${costPct}%` }} />
          </div>
        </div>

        {/* Component 3: Schedule Revision */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-500" />
              <span className="font-bold text-slate-900 dark:text-white">3. Schedule Revision Probability</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-slate-500 dark:text-slate-400 text-[11px]">
                Contribution: +{revContrib}%
              </span>
              <span className="font-bold text-purple-500">
                {revPct}%
              </span>
            </div>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
            <div className="h-full bg-purple-500 rounded-full transition-all duration-500" style={{ width: `${revPct}%` }} />
          </div>
        </div>

        {/* Synthesis Row */}
        <div className="p-4 rounded-xl bg-cyan-500/5 dark:bg-cyan-500/10 border border-cyan-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="text-xs font-mono font-bold text-slate-900 dark:text-white uppercase">
              Candidate B Holding Formulation:
            </div>
            <div className="text-[11px] font-mono text-cyan-700 dark:text-cyan-300">
              Integrated_Risk = (0.50 &times; {schedPct}%) + (0.35 &times; {costPct}%) + (0.15 &times; {revPct}%)
            </div>
          </div>

          <div className="text-right">
            <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">
              = {integratedPct}%
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500 text-slate-950 font-bold uppercase">
              {prediction.risk_band} RISK PRIORITY
            </span>
          </div>
        </div>
      </div>

      {/* Explicit Data Integrity Notice */}
      <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 text-[11px] font-mono text-slate-500 dark:text-slate-400 flex items-start gap-2">
        <span className="text-cyan-500 font-bold">*</span>
        <span>
          Data Integrity Notice: This visualization displays the genuine multi-dimensional risk state evaluated at submission time. Historical monthly risk trajectories do not exist for newly evaluated custom assets, and synthetic historical points are strictly excluded to preserve analytical integrity.
        </span>
      </div>
    </section>
  );
}
