'use client';

import React from 'react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { ShieldAlert, AlertTriangle, CheckCircle2, Cpu, Info } from 'lucide-react';

interface Props {
  project: ProjectSearchRecord;
}

export function RiskPredictionPanel({ project }: Props) {
  const hasML = project.has_ml_telemetry && project.selected_integrated_risk !== null;

  const riskScorePct = hasML
    ? Math.round(project.selected_integrated_risk! * 100)
    : null;

  const costOverrunPct = hasML && project.cost_overrun_risk !== null
    ? Math.round(project.cost_overrun_risk * 100)
    : null;

  const timeOverrunPct = hasML && project.schedule_delay_risk !== null
    ? Math.round(project.schedule_delay_risk * 100)
    : null;

  const overallRiskPct = riskScorePct;

  const band = project.risk_band || 'NOT_ASSESSED';

  const bandStyles: Record<string, { bg: string; text: string; border: string; glow: string; label: string }> = {
    LOW: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-500 dark:text-emerald-400',
      border: 'border-emerald-500/30',
      glow: 'shadow-[0_0_25px_rgba(16,185,129,0.15)]',
      label: 'LOW RISK'
    },
    MEDIUM: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-500 dark:text-amber-400',
      border: 'border-amber-500/30',
      glow: 'shadow-[0_0_25px_rgba(245,158,11,0.15)]',
      label: 'MEDIUM RISK'
    },
    MODERATE: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-500 dark:text-amber-400',
      border: 'border-amber-500/30',
      glow: 'shadow-[0_0_25px_rgba(245,158,11,0.15)]',
      label: 'MEDIUM RISK'
    },
    HIGH: {
      bg: 'bg-rose-500/10',
      text: 'text-rose-500 dark:text-rose-400',
      border: 'border-rose-500/30',
      glow: 'shadow-[0_0_25px_rgba(244,63,94,0.2)]',
      label: 'HIGH RISK'
    },
    VERY_HIGH: {
      bg: 'bg-rose-600/10',
      text: 'text-rose-600 dark:text-rose-400',
      border: 'border-rose-600/30',
      glow: 'shadow-[0_0_30px_rgba(225,29,72,0.25)]',
      label: 'VERY HIGH RISK'
    },
    NOT_ASSESSED: {
      bg: 'bg-slate-500/10',
      text: 'text-slate-500 dark:text-slate-400',
      border: 'border-slate-500/30',
      glow: '',
      label: 'UNAVAILABLE'
    }
  };

  const currentTheme = bandStyles[band] || bandStyles.NOT_ASSESSED;

  return (
    <div className={`p-6 sm:p-7 rounded-2xl bg-gradient-to-b from-slate-900 via-[#06131c] to-[#040d13] text-white border ${currentTheme.border} ${currentTheme.glow} relative overflow-hidden`}>
      {/* Background radial highlight */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 space-y-6">
        {/* Top bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400 animate-pulse" />
            <span className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase">
              Section 05 — Machine Learning Inference Engine
            </span>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Model Pipeline:</span>
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-cyan-300">
              Random Forest + Tuned Gradient Boosting
            </span>
          </div>
        </div>

        {/* Hero Risk Display */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Main Risk Score Gauge */}
          <div className="lg:col-span-5 flex flex-col items-center sm:items-start text-center sm:text-left space-y-3">
            <div className="text-xs font-mono tracking-wider text-slate-400 uppercase">
              Predictive Risk Assessment
            </div>

            {hasML ? (
              <div className="flex items-baseline gap-4">
                <span className="text-5xl sm:text-6xl font-extrabold font-mono tracking-tight text-white">
                  {riskScorePct}%
                </span>
                <span className={`text-xs font-mono font-bold px-3 py-1.5 rounded-full border ${currentTheme.bg} ${currentTheme.text} ${currentTheme.border}`}>
                  {currentTheme.label}
                </span>
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-400">
                  ASSESSMENT UNAVAILABLE
                </span>
                <p className="text-xs text-slate-400 font-mono">
                  Telemetry pipeline is actively calibrating baseline parameters for this project.
                </p>
              </div>
            )}

            <div className="text-xs text-slate-300 max-w-sm pt-1">
              {hasML ? (
                <span>
                  Synthesized from 12-month longitudinal telemetry. Dominant risk component:{' '}
                  <strong className="text-cyan-300">{project.dominant_component}</strong>.
                </span>
              ) : (
                <span>
                  No verified predictive weights found in the ML inference repository for Project ID {project.project_id}.
                </span>
              )}
            </div>
          </div>

          {/* 3 Separate Predictions */}
          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            {/* Prediction 1: COST OVERRUN RISK */}
            <div className="p-4 rounded-xl bg-white/[0.04] border border-white/10 flex flex-col justify-between space-y-3">
              <div className="text-[11px] font-mono uppercase text-slate-400 tracking-wider">
                Cost Overrun Risk
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-white">
                  {costOverrunPct !== null ? `${costOverrunPct}%` : 'Unavailable'}
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">
                  Budget Escalation Probability
                </div>
              </div>
              <div className="w-full bg-white/10 h-1 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-400 h-full rounded-full"
                  style={{ width: `${costOverrunPct || 0}%` }}
                />
              </div>
            </div>

            {/* Prediction 2: TIME OVERRUN RISK */}
            <div className="p-4 rounded-xl bg-white/[0.04] border border-white/10 flex flex-col justify-between space-y-3">
              <div className="text-[11px] font-mono uppercase text-slate-400 tracking-wider">
                Time Overrun Risk
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-amber-400">
                  {timeOverrunPct !== null ? `${timeOverrunPct}%` : 'Unavailable'}
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">
                  Schedule Delay Probability
                </div>
              </div>
              <div className="w-full bg-white/10 h-1 rounded-full overflow-hidden">
                <div
                  className="bg-amber-400 h-full rounded-full"
                  style={{ width: `${timeOverrunPct || 0}%` }}
                />
              </div>
            </div>

            {/* Prediction 3: OVERALL PROJECT RISK */}
            <div className="p-4 rounded-xl bg-white/[0.04] border border-white/10 flex flex-col justify-between space-y-3">
              <div className="text-[11px] font-mono uppercase text-slate-400 tracking-wider">
                Overall Project Risk
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-cyan-300">
                  {overallRiskPct !== null ? `${overallRiskPct}%` : 'Unavailable'}
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">
                  Integrated ML Score
                </div>
              </div>
              <div className="w-full bg-white/10 h-1 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-300 h-full rounded-full"
                  style={{ width: `${overallRiskPct || 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Audit Disclaimer */}
        <div className="flex items-center gap-2 pt-2 text-[11px] font-mono text-slate-400 border-t border-white/5">
          <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
          <span>
            Predictions are evaluated by PAIMANA's integrated ML risk engine against 2,741 longitudinal national infrastructure assets.
          </span>
        </div>
      </div>
    </div>
  );
}
