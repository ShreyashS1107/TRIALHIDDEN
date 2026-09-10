'use client';

import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCw, ShieldAlert, CheckCircle2, ArrowRight, Sparkles, AlertOctagon } from 'lucide-react';
import { ProjectDetail, SimulationResult } from '@/lib/api/types';
import { runWhatIfSimulation } from '@/lib/api/simulation';

interface Section14Props {
  projects?: ProjectDetail[];
}

export default function Section14_WhatIfSimulation({ projects = [] }: Section14Props) {
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projects[0]?.project_id || '105236');
  const [progressDelta, setProgressDelta] = useState<number>(-10); // -10% progress slowdown
  const [spendDelta, setSpendDelta] = useState<number>(15); // +15% spend acceleration
  const [costVariance, setCostVariance] = useState<number>(20); // +20% cost escalation
  const [timelineDelay, setTimelineDelay] = useState<number>(8); // +8 months timeline slip

  const [simResult, setSimResult] = useState<SimulationResult | null>(null);

  useEffect(() => {
    runWhatIfSimulation({
      baseProjectId: selectedProjectId,
      progressDeltaPct: progressDelta,
      monthlySpendDeltaPct: spendDelta,
      costVariancePct: costVariance,
      timelineDelayMonths: timelineDelay,
    }).then(setSimResult);
  }, [selectedProjectId, progressDelta, spendDelta, costVariance, timelineDelay]);

  const activeProj = projects.find((p) => p.project_id === selectedProjectId) || projects[0];

  const handleReset = () => {
    setProgressDelta(0);
    setSpendDelta(0);
    setCostVariance(0);
    setTimelineDelay(0);
  };

  return (
    <section id="what-if" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <Sliders className="w-3.5 h-3.5" />
              <span>SECTION 14 • DECISION-SUPPORT COUNTERFACTUAL ENGINE</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              WHAT IF?
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber font-mono font-bold text-xs">
              DEMO SIMULATION
            </span>
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-navy-800 border border-concrete-700 text-concrete-300 hover:text-white text-xs font-mono"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Main Simulation Workspace Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Controls Panel (6 cols) */}
          <div className="lg:col-span-6 glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
              <span className="text-xs font-mono text-cyan-300 uppercase tracking-wider font-bold">
                Simulation Variables
              </span>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-navy-950 border border-cyan-500/30 text-white rounded-lg px-2.5 py-1 text-xs font-mono outline-none"
              >
                {projects.slice(0, 6).map((p) => (
                  <option key={p.project_id} value={p.project_id}>
                    {p.project_id}: {p.project_name.slice(0, 24)}...
                  </option>
                ))}
              </select>
            </div>

            {/* Slider 1: Physical Progress Delta */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-concrete-300">PHYSICAL PROGRESS PACE</span>
                <span className={`font-bold ${progressDelta < 0 ? 'text-amber' : 'text-cyan'}`}>
                  {progressDelta > 0 ? `+${progressDelta}%` : `${progressDelta}%`}
                </span>
              </div>
              <input
                type="range"
                min="-30"
                max="20"
                step="5"
                value={progressDelta}
                onChange={(e) => setProgressDelta(Number(e.target.value))}
                className="w-full accent-cyan bg-navy-950 cursor-pointer"
              />
              <span className="text-[10px] text-concrete-400 block font-sans">
                Simulate site access bottlenecks or accelerated monsoon downtime.
              </span>
            </div>

            {/* Slider 2: Monthly Expenditure Delta */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-concrete-300">MONTHLY EXPENDITURE OUTFLOW</span>
                <span className={`font-bold ${spendDelta > 0 ? 'text-amber' : 'text-teal'}`}>
                  {spendDelta > 0 ? `+${spendDelta}%` : `${spendDelta}%`}
                </span>
              </div>
              <input
                type="range"
                min="-20"
                max="40"
                step="5"
                value={spendDelta}
                onChange={(e) => setSpendDelta(Number(e.target.value))}
                className="w-full accent-teal bg-navy-950 cursor-pointer"
              />
              <span className="text-[10px] text-concrete-400 block font-sans">
                Simulate advance mobilization payouts or contractor billing surge.
              </span>
            </div>

            {/* Slider 3: Capital Cost Revision Variance */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-concrete-300">CAPITAL COST VARIANCE</span>
                <span className={`font-bold ${costVariance > 0 ? 'text-amber' : 'text-white'}`}>
                  +{costVariance}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="60"
                step="5"
                value={costVariance}
                onChange={(e) => setCostVariance(Number(e.target.value))}
                className="w-full accent-amber bg-navy-950 cursor-pointer"
              />
              <span className="text-[10px] text-concrete-400 block font-sans">
                Anticipated revised charter escalation over baseline sanctioned outlay.
              </span>
            </div>

            {/* Slider 4: Timeline Slippage Delay */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-concrete-300">SCHEDULE TIMELINE DELAY</span>
                <span className={`font-bold ${timelineDelay > 0 ? 'text-amber' : 'text-white'}`}>
                  +{timelineDelay} Months
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="24"
                step="2"
                value={timelineDelay}
                onChange={(e) => setTimelineDelay(Number(e.target.value))}
                className="w-full accent-amber bg-navy-950 cursor-pointer"
              />
              <span className="text-[10px] text-concrete-400 block font-sans">
                Target date extension beyond original sanctioned commissioning date.
              </span>
            </div>
          </div>

          {/* Dynamic Result Panel (6 cols) */}
          <div className="lg:col-span-6 flex flex-col justify-between glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20 mb-6">
                <span className="text-xs font-mono text-cyan-300 uppercase tracking-wider font-bold">
                  Simulated Outcome Metrics
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber border border-amber-500/40">
                  DEMO SIMULATION
                </span>
              </div>

              {simResult && (
                <div className="space-y-6">
                  {/* Current vs Simulated Risk Reveal */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="glass-panel p-4 rounded-xl border-concrete-800">
                      <span className="text-[10px] font-mono text-concrete-400 uppercase block mb-1">
                        CURRENT RISK
                      </span>
                      <span className="text-3xl sm:text-4xl font-extrabold font-mono text-white">
                        {Math.round(simResult.baseRisk * 100)}%
                      </span>
                      <span className="text-[11px] font-mono text-concrete-400 block mt-1">
                        Baseline ({activeProj?.predictive_risk.risk_band})
                      </span>
                    </div>

                    <div className="glass-panel-amber p-4 rounded-xl border-amber-500/40">
                      <span className="text-[10px] font-mono text-amber uppercase block mb-1 font-bold">
                        PREDICTED RISK
                      </span>
                      <span className="text-3xl sm:text-4xl font-extrabold font-mono text-amber">
                        {Math.round(simResult.simulatedRisk * 100)}%
                      </span>
                      <span className="text-[11px] font-mono text-amber block mt-1 font-bold">
                        {simResult.riskDelta >= 0 ? `+${Math.round(simResult.riskDelta * 100)}% SHIFT` : `${Math.round(simResult.riskDelta * 100)}% SHIFT`}
                      </span>
                    </div>
                  </div>

                  {/* Primary Simulated Driver */}
                  <div className="p-4 rounded-xl bg-navy-950/80 border border-concrete-800 text-xs font-mono">
                    <span className="text-concrete-400 text-[10px] uppercase block mb-1">
                      Primary Simulated Vulnerability Driver
                    </span>
                    <span className="text-white font-bold text-sm">
                      {simResult.primaryRiskDriver}
                    </span>
                  </div>

                  {/* Recommended Intervention */}
                  <div className="glass-panel-amber p-5 rounded-xl border-amber-500/30 text-xs space-y-2">
                    <div className="flex items-center gap-2 text-amber font-mono font-bold">
                      <ShieldAlert className="w-4 h-4" />
                      <span>RECOMMENDED COUNTER-MEASURE DIRECTIVE</span>
                    </div>
                    <h5 className="font-bold text-white text-sm">
                      {simResult.recommendedIntervention.title}
                    </h5>
                    <p className="text-concrete-300 text-xs leading-relaxed">
                      {simResult.recommendedIntervention.reason}
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-concrete-800 mt-6 text-[10px] font-mono text-concrete-400 text-center">
              DEMO SIMULATION: Parameters model heuristic sensitivity curves to assist what-if policy exploration.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
