'use client';

import React from 'react';
import { CustomProjectPredictionResponse } from '@/lib/api/predict';
import { Cpu, CheckCircle2, Clock, IndianRupee, Layers } from 'lucide-react';

interface Props {
  prediction: CustomProjectPredictionResponse;
}

export function RiskOverview({ prediction }: Props) {
  const overallRiskPct = Math.round(prediction.selected_integrated_risk * 1000) / 10;
  const schedRiskPct = Math.round(prediction.schedule_delay_risk * 1000) / 10;
  const costRiskPct = Math.round(prediction.cost_overrun_risk * 1000) / 10;
  const revRiskPct = Math.round(prediction.schedule_revision_risk * 1000) / 10;

  const bandStyles: Record<string, { bg: string; text: string; border: string; glow: string; badge: string }> = {
    LOW: {
      bg: 'bg-emerald-500/10 dark:bg-emerald-500/10',
      text: 'text-emerald-700 dark:text-emerald-400',
      border: 'border-emerald-500/30',
      glow: 'shadow-[0_0_35px_rgba(16,185,129,0.18)]',
      badge: 'bg-emerald-500 text-slate-950 font-bold'
    },
    MEDIUM: {
      bg: 'bg-amber-500/10 dark:bg-amber-500/10',
      text: 'text-amber-700 dark:text-amber-400',
      border: 'border-amber-500/30',
      glow: 'shadow-[0_0_35px_rgba(245,158,11,0.18)]',
      badge: 'bg-amber-500 text-slate-950 font-bold'
    },
    HIGH: {
      bg: 'bg-rose-500/10 dark:bg-rose-500/10',
      text: 'text-rose-700 dark:text-rose-400',
      border: 'border-rose-500/30',
      glow: 'shadow-[0_0_35px_rgba(244,63,94,0.22)]',
      badge: 'bg-rose-500 text-white font-bold'
    },
    VERY_HIGH: {
      bg: 'bg-rose-600/10 dark:bg-rose-600/15',
      text: 'text-rose-700 dark:text-rose-300',
      border: 'border-rose-600/40',
      glow: 'shadow-[0_0_40px_rgba(225,29,72,0.28)]',
      badge: 'bg-rose-600 text-white font-bold animate-pulse'
    }
  };

  const currentTheme = bandStyles[prediction.risk_band] || bandStyles.MEDIUM;

  return (
    <section className={`p-6 sm:p-9 rounded-3xl bg-white dark:bg-gradient-to-b dark:from-slate-900 dark:via-[#06131c] dark:to-[#040d13] text-slate-900 dark:text-white border ${currentTheme.border} ${currentTheme.glow} relative overflow-hidden shadow-xl`}>
      {/* Background ambient light */}
      <div className="absolute top-0 right-0 w-[450px] h-[450px] bg-cyan-500/5 dark:bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 space-y-8">
        {/* Header Ribbon */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-600 dark:text-cyan-400 animate-pulse" />
            <span className="text-xs font-mono font-bold tracking-widest text-cyan-600 dark:text-cyan-400 uppercase">
              CENTRAL ML INFERENCE ASSESSMENT • THREE-PILLAR ENGINE
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-600 dark:text-slate-400">
            <span>Model:</span>
            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-cyan-700 dark:text-cyan-300 font-semibold">
              {prediction.model_version}
            </span>
          </div>
        </div>

        {/* Central Risk Callout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Main Integrated Risk */}
          <div className="lg:col-span-5 flex flex-col items-center sm:items-start text-center sm:text-left space-y-3">
            <div className="text-xs font-mono tracking-widest text-slate-500 dark:text-slate-400 uppercase font-semibold">
              OVERALL INTEGRATED RISK
            </div>

            <div className="flex items-baseline gap-4">
              <span className="text-6xl sm:text-7xl font-extrabold font-mono tracking-tight text-slate-950 dark:text-white">
                {overallRiskPct}%
              </span>
              <span className={`text-xs font-mono px-3 py-1.5 rounded-full border ${currentTheme.bg} ${currentTheme.text} ${currentTheme.border} font-bold`}>
                {prediction.risk_band} RISK PRIORITY
              </span>
            </div>

            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 max-w-md leading-relaxed">
              Synthesized via Candidate B Evidence-Weighted formulation. Dominant risk stressor:{' '}
              <strong className="text-cyan-600 dark:text-cyan-300 font-mono font-bold">
                {prediction.dominant_component}
              </strong>.
            </p>

            {prediction.model_confidence !== null && (
              <div className="flex items-center gap-2 pt-1 text-xs font-mono text-slate-500 dark:text-slate-400">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Runtime Model Certainty: </span>
                <strong className="text-slate-900 dark:text-white font-semibold">
                  {(prediction.model_confidence * 100).toFixed(1)}%
                </strong>
                <span className="text-[11px] text-slate-400 dark:text-slate-500">(Platt Calibrated)</span>
              </div>
            )}
          </div>

          {/* 3 Real Model Outputs (Candidate B Inputs) */}
          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Pillar 1: Schedule Delay */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 space-y-2 relative overflow-hidden">
              <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
                <span className="font-semibold uppercase text-[10px]">Schedule Delay Risk</span>
                <Clock className="w-3.5 h-3.5 text-cyan-500" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
                {schedRiskPct}%
              </div>
              <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1 border-t border-slate-200/60 dark:border-white/5">
                <span>Model: Calibrated RF</span>
                <span className="text-cyan-600 dark:text-cyan-400 font-bold">Weight 50%</span>
              </div>
            </div>

            {/* Pillar 2: Cost Overrun */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 space-y-2 relative overflow-hidden">
              <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
                <span className="font-semibold uppercase text-[10px]">Cost Overrun Risk</span>
                <IndianRupee className="w-3.5 h-3.5 text-amber-500" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
                {costRiskPct}%
              </div>
              <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1 border-t border-slate-200/60 dark:border-white/5">
                <span>Model: Balanced RF</span>
                <span className="text-amber-600 dark:text-amber-400 font-bold">Weight 35%</span>
              </div>
            </div>

            {/* Pillar 3: Schedule Revision */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 space-y-2 relative overflow-hidden">
              <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
                <span className="font-semibold uppercase text-[10px]">Schedule Revision Risk</span>
                <Layers className="w-3.5 h-3.5 text-purple-500" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
                {revRiskPct}%
              </div>
              <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between pt-1 border-t border-slate-200/60 dark:border-white/5">
                <span>Model: Logistic Reg</span>
                <span className="text-purple-600 dark:text-purple-400 font-bold">Weight 15%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
