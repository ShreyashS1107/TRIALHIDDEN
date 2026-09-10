'use client';

import React from 'react';
import RiskTrajectory3D from '../three/RiskTrajectory3D';
import { ShieldAlert, Cpu, BarChart3, AlertOctagon, Layers, ArrowRight } from 'lucide-react';
import { NationalSummary } from '@/lib/api/types';

interface Section04Props {
  summary?: NationalSummary | null;
}

export default function Section04_RiskPrediction({ summary }: Section04Props) {
  return (
    <section id="risk-prediction" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-xs font-mono text-amber mb-4">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>SECTION 04 • PREDICTIVE DIVERGENCE ENGINE</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            RISK DETECTED BEFORE FAILURE.
          </h2>
          <p className="text-sm sm:text-base text-concrete-300 leading-relaxed">
            By continuously coupling supervised Platt-calibrated machine learning (Pillar 1) with deterministic Execution-Stress surveillance (Pillar 2), PAIMANA detects project divergence months before contractor defaults or formal budget revisions occur.
          </p>
        </div>

        {/* 3D Visual Trajectory Canvas Container */}
        <div className="mb-14">
          <RiskTrajectory3D />
        </div>

        {/* Dual Pillar Architecture Explanation */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Pillar 1: Predictive Risk Engine */}
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 space-y-4 text-left">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-cyan" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">PILLAR 1: PREDICTIVE ML ENGINE</h4>
                  <span className="text-xs font-mono text-cyan-300">Point-in-Time Supervised Classifier</span>
                </div>
              </div>
              <span className="text-xs font-mono px-2 py-1 rounded bg-cyan-500/15 text-cyan border border-cyan-500/30">
                Candidate B Index
              </span>
            </div>

            <p className="text-xs text-concrete-300 leading-relaxed">
              Synthesizes 75 point-in-time features without temporal leakage to output calibrated completion delay and budget breach probabilities.
            </p>

            <div className="p-3.5 rounded-xl bg-navy-950/80 border border-cyan-500/20 font-mono text-xs text-cyan-300 space-y-1.5">
              <span className="text-[10px] text-concrete-400 uppercase block font-sans">Formula Weighting</span>
              <div className="font-bold">
                Integrated Risk = 0.50 × SchedDelay + 0.35 × CostOverrun + 0.15 × SchedRev
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono pt-2">
              <div className="p-2 rounded bg-navy-950/50 border border-concrete-800">
                <span className="text-[10px] text-concrete-400 block font-sans">Schedule OOT ROC</span>
                <span className="text-white font-bold">0.9723</span>
              </div>
              <div className="p-2 rounded bg-navy-950/50 border border-concrete-800">
                <span className="text-[10px] text-concrete-400 block font-sans">Cost OOT ROC</span>
                <span className="text-white font-bold">0.9895</span>
              </div>
              <div className="p-2 rounded bg-navy-950/50 border border-concrete-800">
                <span className="text-[10px] text-concrete-400 block font-sans">Revision OOT ROC</span>
                <span className="text-white font-bold">0.8264</span>
              </div>
            </div>
          </div>

          {/* Pillar 2: Operational Execution Surveillance */}
          <div className="glass-panel p-6 sm:p-8 rounded-2xl border-teal-500/30 space-y-4 text-left">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/40 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-teal" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">PILLAR 2: EXECUTION STRESS (ESI)</h4>
                  <span className="text-xs font-mono text-teal-300">Deterministic Operational Surveillance</span>
                </div>
              </div>
              <span className="text-xs font-mono px-2 py-1 rounded bg-teal-500/15 text-teal border border-teal-500/30">
                Analytical Index
              </span>
            </div>

            <p className="text-xs text-concrete-300 leading-relaxed">
              Detects physical stagnation, velocity deceleration, capital expenditure divergence, and overdue schedule debt directly from reported monthly facts.
            </p>

            <div className="p-3.5 rounded-xl bg-navy-950/80 border border-teal-500/20 font-mono text-xs text-teal-300 space-y-1.5">
              <span className="text-[10px] text-concrete-400 uppercase block font-sans">Deterministic Formula</span>
              <div className="font-bold">
                ESI = 0.30 × S_stag + 0.25 × S_vel + 0.20 × S_div + 0.15 × S_sched + 0.10 × S_rep
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono pt-2">
              <div className="p-2 rounded bg-navy-950/50 border border-concrete-800">
                <span className="text-[10px] text-concrete-400 block font-sans">Cross-Correlation (ρ)</span>
                <span className="text-teal font-bold">0.1360 (Non-Redundant)</span>
              </div>
              <div className="p-2 rounded bg-navy-950/50 border border-concrete-800">
                <span className="text-[10px] text-concrete-400 block font-sans">Off-Diagonal Stress</span>
                <span className="text-teal font-bold">65.4% on Mod/Low Risk</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quote Callout Banner */}
        <div className="glass-panel p-6 rounded-2xl border-cyan-500/20 text-center max-w-3xl mx-auto">
          <p className="text-sm sm:text-base font-semibold text-white tracking-wide">
            “PAIMANA helps authorities understand what is happening, what may happen next, why it may happen, which project requires attention, and where intervention should happen first.”
          </p>
          <span className="block text-[11px] font-mono text-cyan-300 uppercase tracking-widest mt-2">
            MoSPI / IPMD Strategic Mandate • SIH26103
          </span>
        </div>
      </div>
    </section>
  );
}
