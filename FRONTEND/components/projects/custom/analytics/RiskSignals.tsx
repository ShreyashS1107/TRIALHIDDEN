'use client';

import React from 'react';
import { CustomProjectPredictionResponse } from '@/lib/api/predict';
import { ShieldAlert, AlertTriangle, Layers, ArrowUpRight, Info } from 'lucide-react';

interface Props {
  prediction: CustomProjectPredictionResponse;
}

export function RiskSignals({ prediction }: Props) {
  // Use model_risk_signals if provided by the backend, otherwise fallback to risk_drivers
  const signals = prediction.model_risk_signals && prediction.model_risk_signals.length > 0
    ? prediction.model_risk_signals
    : (prediction.risk_drivers || []).map((d) => ({
        id: d.id,
        feature_name: d.id,
        label: d.name,
        observed_value: d.description.split(';')[0] || 'Metric observed',
        importance_weight: d.impact_pct / 100,
        importance_pct: d.impact_pct,
        impact_level: d.impact_level,
        directional_signal: d.description,
        risk_component: d.id.includes('schedule') ? 'Schedule Delay' : (d.id.includes('cost') ? 'Cost Overrun' : 'Execution'),
        attribution_type: 'MODEL-DERIVED SIGNAL'
      }));

  const impactStyles: Record<string, { badge: string; bar: string }> = {
    'High impact': {
      badge: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30',
      bar: 'bg-rose-500'
    },
    'Medium impact': {
      badge: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30',
      bar: 'bg-amber-500'
    },
    'Low impact': {
      badge: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30',
      bar: 'bg-cyan-500'
    }
  };

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              FEATURE ATTRIBUTION & EXPLAINABILITY
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
              MODEL-DERIVED RISK SIGNALS
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            WHY DID THE MODEL ASSIGN THIS RISK SCORE?
          </h3>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-500 dark:text-slate-400">
          <Info className="w-3.5 h-3.5 text-cyan-500" />
          <span>Gini Feature Importance + Intake Metrics</span>
        </div>
      </div>

      {/* Visual Provenance Legend */}
      <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex flex-wrap items-center gap-4 text-xs font-mono">
        <span className="text-slate-500 dark:text-slate-400 uppercase text-[10px] font-bold">Provenance Layers:</span>
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 rounded bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30 text-[10px] font-bold">
            MODEL-DERIVED SIGNAL
          </span>
          <span className="text-slate-600 dark:text-slate-300 text-[11px]">= Gini weight in Random Forest</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 text-[10px] font-bold">
            OBSERVED PROJECT METRIC
          </span>
          <span className="text-slate-600 dark:text-slate-300 text-[11px]">= Certified intake submission</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 text-[10px] font-bold">
            DECISION INTERPRETATION
          </span>
          <span className="text-slate-600 dark:text-slate-300 text-[11px]">= Directional risk signal</span>
        </div>
      </div>

      {/* Ranked Signals List */}
      <div className="space-y-4">
        {signals.map((sig, idx) => {
          const style = impactStyles[sig.impact_level] || impactStyles['Medium impact'];
          const rankNumber = String(idx + 1).padStart(2, '0');

          return (
            <div
              key={sig.id || idx}
              className="p-5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-4 hover:border-cyan-500/30 transition-all duration-150"
            >
              {/* Top Row: Rank, Title, Pillar, Impact Badge */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-extrabold text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
                    {rankNumber}
                  </span>
                  <div>
                    <h4 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                      {sig.label}
                    </h4>
                    <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      Pillar: <strong className="text-cyan-600 dark:text-cyan-400">{sig.risk_component}</strong> • Feature: <code className="text-slate-600 dark:text-slate-300">{sig.feature_name}</code>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
                    {(sig.importance_weight * 100).toFixed(1)}% Gini Weight
                  </span>
                  <span className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${style.badge}`}>
                    {sig.impact_level.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Gini Importance Progress Bar */}
              <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
                <div
                  className={`h-full rounded-full ${style.bar} transition-all duration-500`}
                  style={{ width: `${Math.min(100, sig.importance_pct * 3)}%` }}
                />
              </div>

              {/* Bottom 2-Column Details: Observed Metric vs Decision-Support Direction */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-2 text-xs font-mono border-t border-slate-200/60 dark:border-white/5">
                {/* Observed Metric */}
                <div className="md:col-span-4 p-2.5 rounded-lg bg-white dark:bg-black/30 border border-slate-200 dark:border-white/5 space-y-1">
                  <div className="text-[10px] text-cyan-600 dark:text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1">
                    <span>[OBSERVED PROJECT METRIC]</span>
                  </div>
                  <div className="text-slate-900 dark:text-white font-semibold">
                    {sig.observed_value}
                  </div>
                </div>

                {/* Directional Signal */}
                <div className="md:col-span-8 p-2.5 rounded-lg bg-white dark:bg-black/30 border border-slate-200 dark:border-white/5 space-y-1">
                  <div className="text-[10px] text-amber-600 dark:text-amber-400 font-bold uppercase tracking-wider flex items-center gap-1">
                    <span>[DECISION-SUPPORT INTERPRETATION]</span>
                  </div>
                  <div className="text-slate-700 dark:text-slate-300 font-sans leading-relaxed text-[11px]">
                    {sig.directional_signal}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
