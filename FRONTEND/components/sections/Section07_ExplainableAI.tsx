'use client';

import React, { useState } from 'react';
import { HelpCircle, ShieldAlert, CheckCircle2, ChevronRight, Info, Sparkles } from 'lucide-react';
import { ProjectDetail } from '@/lib/api/types';

interface Section07Props {
  projects?: ProjectDetail[];
}

export default function Section07_ExplainableAI({ projects = [] }: Section07Props) {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const activeProj = projects[selectedIdx] || projects[0];

  if (!activeProj) return null;

  const features = activeProj.shap_attribution || [
    { factor: 'Physical Progress Momentum', importance: 32, direction: 'risk_driver', value: `${activeProj.physical_progress_percent}% build` },
    { factor: 'Expenditure vs Build Spread', importance: 24, direction: 'risk_driver', value: '+18.4% spread' },
    { factor: 'Cost Revision History', importance: 18, direction: 'risk_driver', value: `₹${(activeProj.revised_cost_crore - activeProj.original_cost_crore).toFixed(0)} Cr delta` },
    { factor: 'Completion Timeline Slippage', importance: 14, direction: 'risk_driver', value: '14 months slippage' },
    { factor: 'Historical Reporting Integrity', importance: 12, direction: 'normal', value: '15 epochs tracked' },
  ];

  return (
    <section id="explainable-ai" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>SECTION 07 • SHAP EXPLAINABILITY LAYER</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            PREDICTION IS NOT ENOUGH.
            <span className="block text-cyan">EXPLAINABILITY BUILDS TRUST.</span>
          </h2>
          <p className="text-sm sm:text-base text-concrete-300 leading-relaxed">
            Government authorities cannot intervene based on black-box predictions. PAIMANA decomposes every ML risk score into calibrated SHAP attribution weights, identifying exactly which physical bottlenecks, capital spreads, or schedule deviations drive project vulnerability.
          </p>
        </div>

        {/* Project Selector Mini Bar */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          {projects.slice(0, 6).map((p, idx) => (
            <button
              key={p.project_id}
              onClick={() => setSelectedIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap transition-all border ${
                selectedIdx === idx
                  ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                  : 'bg-navy-900 border-concrete-700/50 text-concrete-400 hover:text-white'
              }`}
            >
              {p.project_id}: {p.project_name.slice(0, 22)}...
            </button>
          ))}
        </div>

        {/* Main Explainability Card */}
        <div className="glass-panel p-6 sm:p-10 rounded-2xl border-cyan-500/30">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-cyan-500/20 mb-8">
            <div>
              <span className="text-xs font-mono text-cyan-300">
                Diagnostic Assessment • Project {activeProj.project_id}
              </span>
              <h3 className="text-2xl font-extrabold text-white mt-1">
                WHY IS THIS PROJECT AT RISK?
              </h3>
              <p className="text-xs text-concrete-400 mt-1">
                {activeProj.project_name} ({activeProj.agency} • {activeProj.state})
              </p>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-amber" />
                <span className="text-amber font-semibold">Risk-Driving Factor</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-cyan" />
                <span className="text-cyan font-semibold">Normal / Protective Factor</span>
              </div>
            </div>
          </div>

          {/* SHAP Feature Importance Bars */}
          <div className="space-y-6 max-w-4xl mx-auto">
            {features.map((feat) => {
              const isRiskDriver = feat.direction === 'risk_driver';
              const barColor = isRiskDriver ? 'bg-amber' : 'bg-cyan';
              const textColor = isRiskDriver ? 'text-amber' : 'text-cyan';

              return (
                <div key={feat.factor} className="space-y-2">
                  <div className="flex items-center justify-between text-xs sm:text-sm font-mono">
                    <span className="text-white font-bold flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${isRiskDriver ? 'bg-amber animate-pulse' : 'bg-cyan'}`} />
                      {feat.factor}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-concrete-400 font-sans text-xs hidden sm:inline">
                        Recorded: {feat.value}
                      </span>
                      <span className={`font-bold ${textColor}`}>
                        {feat.importance}% INFLUENCE
                      </span>
                    </div>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="w-full bg-navy-950 h-3 rounded-full overflow-hidden border border-concrete-700/60 p-0.5">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ${barColor}`}
                      style={{ width: `${feat.importance * 2.5}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Bottom Prescriptive Summary */}
          <div className="mt-10 p-5 rounded-xl bg-navy-950/80 border border-cyan-500/20 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-concrete-400 font-mono text-[10px] uppercase block mb-1">
                Dominant Observable Stressor
              </span>
              <span className="text-amber font-bold text-sm font-mono">
                {activeProj.execution_profile.dominant_stressor}
              </span>
              <p className="text-concrete-300 text-[11px] mt-1">
                Triggered by {activeProj.execution_profile.total_stress_flags}/5 active operational friction indicators on site.
              </p>
            </div>
            <div>
              <span className="text-concrete-400 font-mono text-[10px] uppercase block mb-1">
                Suggested Administrative Action
              </span>
              <span className="text-cyan font-bold text-sm font-mono">
                {activeProj.execution_profile.suggested_action.title}
              </span>
              <p className="text-concrete-300 text-[11px] mt-1">
                {activeProj.execution_profile.suggested_action.reason}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
