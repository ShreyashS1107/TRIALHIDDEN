'use client';

import React from 'react';
import { CustomProjectPredictionResponse } from '@/lib/api/predict';
import { Sparkles, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';

interface Props {
  prediction: CustomProjectPredictionResponse;
}

export function DecisionSupport({ prediction }: Props) {
  const isHighRisk = prediction.risk_band === 'HIGH' || prediction.risk_band === 'VERY_HIGH';
  const isMediumRisk = prediction.risk_band === 'MEDIUM';
  const dominant = prediction.dominant_component;

  // Derive structured operational actions based on the backend recommended intervention & dominant stressor
  const immediateAction = isHighRisk
    ? (dominant === 'Schedule Delay'
        ? 'Mobilize Project Management Unit (PMU) critical path acceleration taskforce.'
        : 'Freeze non-essential variation orders and mandate immediate financial audit of balance civil works.')
    : (isMediumRisk
        ? 'Initiate bi-weekly technical milestone monitoring and contractor equipment audit.'
        : 'Reaffirm standard MoSPI IPMD surveillance baseline protocols.');

  const thirtyDayAction = isHighRisk
    ? 'Convene tripartite executive review with implementing ministry, state authorities, and EPC contractors.'
    : (isMediumRisk
        ? 'Review contractor sub-vendor liquidity and verify raw material supply-chain security.'
        : 'Conduct scheduled quarterly physical milestone validation.');

  const continuousAction = isHighRisk
    ? 'Enforce real-time milestone burn tracking and contract escalation index monitoring.'
    : (isMediumRisk
        ? 'Maintain weekly equipment mobilization registers and progress telemetry.'
        : 'Preserve automated surveillance telemetry without active emergency escalation.');

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-cyan-500/25 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-500" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              DECISION-SUPPORT LAYER
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            WHAT SHOULD HAPPEN NEXT?
          </h3>
        </div>

        <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
          MoSPI Prescriptive Protocol
        </span>
      </div>

      {/* Primary Authoritative Recommendation from Backend */}
      <div className="p-5 rounded-xl bg-slate-50 dark:bg-black/30 border border-slate-200 dark:border-white/10 space-y-2">
        <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-bold">
          AUTHORITATIVE INTERVENTION DIRECTIVE
        </div>
        <div className="text-sm sm:text-base font-sans font-semibold text-slate-900 dark:text-white leading-relaxed">
          &ldquo;{prediction.recommended_intervention}&rdquo;
        </div>
      </div>

      {/* 3 Actionable Horizon Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Immediate */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 uppercase">
              IMMEDIATE (0–7 DAYS)
            </span>
            <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
          </div>
          <div className="text-xs font-semibold text-slate-900 dark:text-white pt-1">
            {immediateAction}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            Rapid operational escalation to unblock primary critical path bottleneck.
          </div>
        </div>

        {/* Card 2: Next 30 Days */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 uppercase">
              NEXT 30 DAYS
            </span>
            <CheckCircle2 className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="text-xs font-semibold text-slate-900 dark:text-white pt-1">
            {thirtyDayAction}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            Contractual alignment & tripartite institutional consensus.
          </div>
        </div>

        {/* Card 3: Continuous Monitoring */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 uppercase">
              CONTINUOUS SURVEILLANCE
            </span>
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-500" />
          </div>
          <div className="text-xs font-semibold text-slate-900 dark:text-white pt-1">
            {continuousAction}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            Automated threshold surveillance to prevent repeat baseline slippage.
          </div>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div className="pt-2 border-t border-slate-200/60 dark:border-white/5 flex items-center gap-2 text-[11px] font-mono text-slate-500 dark:text-slate-400">
        <span>*</span>
        <span>
          Prediction identifies risk; intervention recommendations are generated by the decision-support layer.
        </span>
      </div>
    </section>
  );
}
