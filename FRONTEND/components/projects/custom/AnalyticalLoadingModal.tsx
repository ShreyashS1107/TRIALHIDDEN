'use client';

import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, Loader2, Database, ShieldAlert, Sparkles, Binary } from 'lucide-react';

interface Props {
  isOpen: boolean;
  projectName: string;
}

const STAGES = [
  { id: 1, label: 'INGESTING PROJECT TELEMETRY', detail: 'Parsing baseline dates, expenditure metrics, and sanction baselines' },
  { id: 2, label: 'ENGINEERING FEATURES', detail: 'Constructing 75-feature vector with empirical State/Agency priors' },
  { id: 3, label: 'RUNNING RISK MODELS', detail: 'Executing RF_02 Platt Calibrator, Balanced Cost RF & SRev Classifier' },
  { id: 4, label: 'CALCULATING INTEGRATED RISK', detail: 'Evaluating Candidate B evidence-weighted multi-target formulation' },
  { id: 5, label: 'GENERATING EXPLANATION', detail: 'Ranking model-derived Gini risk signals and prescriptive directives' }
];

export function AnalyticalLoadingModal({ isOpen, projectName }: Props) {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setActiveStage(0);
      return;
    }

    const interval = setInterval(() => {
      setActiveStage((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 400);

    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-md transition-all">
      <div className="w-full max-w-lg p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#06131c] border border-cyan-500/30 shadow-[0_0_50px_rgba(57,217,255,0.2)] text-slate-900 dark:text-white relative overflow-hidden space-y-6 animate-in fade-in zoom-in-95 duration-200">
        {/* Subtle background ambient pulse */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-white/10 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                PAIMANA ML INFERENCE PIPELINE
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Evaluating Infrastructure Risk
              </h3>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-600 dark:text-purple-400 text-[10px] font-mono font-bold uppercase tracking-wider animate-pulse">
            LIVE INFERENCE
          </span>
        </div>

        {/* Project Target */}
        <div className="p-3 rounded-xl bg-slate-100 dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 font-mono text-xs">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-0.5">TARGET ASSET:</span>
          <p className="font-semibold text-slate-900 dark:text-white truncate">
            {projectName || 'Custom Infrastructure Project'}
          </p>
        </div>

        {/* Step-by-Step Telemetry Stages */}
        <div className="space-y-3">
          {STAGES.map((s, idx) => {
            const isDone = activeStage > idx;
            const isCurrent = activeStage === idx;

            return (
              <div
                key={s.id}
                className={`p-3 rounded-xl border transition-all duration-300 flex items-start gap-3 ${
                  isCurrent
                    ? 'bg-cyan-500/10 border-cyan-500/40 shadow-sm'
                    : isDone
                    ? 'bg-emerald-500/5 border-emerald-500/20 text-slate-600 dark:text-slate-400'
                    : 'bg-transparent border-transparent opacity-40 text-slate-400'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-cyan-500 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-300 dark:border-slate-700 flex items-center justify-center text-[9px] font-mono">
                      {s.id}
                    </div>
                  )}
                </div>

                <div className="space-y-0.5 flex-1 min-w-0">
                  <div className="flex items-center justify-between text-xs font-mono font-bold">
                    <span className={isCurrent ? 'text-cyan-600 dark:text-cyan-300' : isDone ? 'text-emerald-700 dark:text-emerald-400' : ''}>
                      {s.label}
                    </span>
                    {isCurrent && (
                      <span className="text-[10px] uppercase font-normal text-cyan-500 animate-pulse">
                        PROCESSING...
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                    {s.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info */}
        <div className="pt-2 text-center text-[10px] font-mono text-slate-400 dark:text-slate-500">
          FastAPI Microservice (Port 8000) • Calibrated Random Forest Ensemble
        </div>
      </div>
    </div>
  );
}
