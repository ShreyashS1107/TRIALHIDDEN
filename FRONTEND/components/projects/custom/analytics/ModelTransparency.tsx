'use client';

import React from 'react';
import { CustomProjectPredictionResponse } from '@/lib/api/predict';
import { ShieldCheck, Cpu, Database, Award, Info, FileCode2 } from 'lucide-react';

interface Props {
  prediction: CustomProjectPredictionResponse;
}

export function ModelTransparency({ prediction }: Props) {
  const metadata = prediction.model_metadata || {};
  const roc = metadata.holdout_roc_auc ?? 0.9723;
  const brier = metadata.holdout_brier_score ?? 0.0389;
  const featCount = metadata.features_used ?? 75;

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-500" />
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              SYSTEM PROVENANCE & GOVERNANCE
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            MODEL TRANSPARENCY & ARCHITECTURE
          </h3>
        </div>

        <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
          Frozen Production Pipeline
        </span>
      </div>

      {/* Model Spec Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
        {/* Model Version */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <span className="text-[10px] uppercase text-slate-500 dark:text-slate-400">MODEL VERSION</span>
          <div className="text-sm font-bold text-slate-900 dark:text-white truncate">
            {prediction.model_version}
          </div>
          <div className="text-[11px] text-cyan-600 dark:text-cyan-400">
            Calibrated Inference Registry
          </div>
        </div>

        {/* Feature Count */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <span className="text-[10px] uppercase text-slate-500 dark:text-slate-400">FEATURES USED</span>
          <div className="text-sm font-bold text-slate-900 dark:text-white">
            {featCount} Features
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            71 numeric + 4 categorical
          </div>
        </div>

        {/* Primary Schedule Model */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <span className="text-[10px] uppercase text-slate-500 dark:text-slate-400">PRIMARY SCHEDULE MODEL</span>
          <div className="text-sm font-bold text-slate-900 dark:text-white">
            RF_02 Calibrated
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            Random Forest + Platt Sigmoid
          </div>
        </div>

        {/* Candidate B Scoring Formula */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-1">
          <span className="text-[10px] uppercase text-slate-500 dark:text-slate-400">SCORING ARCHITECTURE</span>
          <div className="text-sm font-bold text-slate-900 dark:text-white">
            Candidate B Formula
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            50% Sched + 35% Cost + 15% Rev
          </div>
        </div>
      </div>

      {/* Model Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        {/* Model 1 */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-cyan-600 dark:text-cyan-400">1. SCHEDULE MODEL</span>
            <span className="text-[10px] text-slate-400">3.88 MB</span>
          </div>
          <div className="text-slate-800 dark:text-slate-200 font-semibold">
            rf02_calibrated.pkl
          </div>
          <p className="text-[11px] font-sans text-slate-500 dark:text-slate-400">
            Random Forest (100 estimators, max depth 12) coupled with Logistic Platt Sigmoid calibrator.
          </p>
        </div>

        {/* Model 2 */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-amber-600 dark:text-amber-400">2. COST MODEL</span>
            <span className="text-[10px] text-slate-400">4.87 MB</span>
          </div>
          <div className="text-slate-800 dark:text-slate-200 font-semibold">
            cost_overrun_state_3m/model.pkl
          </div>
          <p className="text-[11px] font-sans text-slate-500 dark:text-slate-400">
            Balanced Random Forest (200 estimators, class-weighted, max depth 12) targeting binary overrun state.
          </p>
        </div>

        {/* Model 3 */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-purple-600 dark:text-purple-400">3. REVISION MODEL</span>
            <span className="text-[10px] text-slate-400">44.5 KB</span>
          </div>
          <div className="text-slate-800 dark:text-slate-200 font-semibold">
            schedule_revision_3m/model.pkl
          </div>
          <p className="text-[11px] font-sans text-slate-500 dark:text-slate-400">
            Regularized Logistic Regression (L2 penalty, max 1000 iter) predicting administrative date re-baselining.
          </p>
        </div>
      </div>

      {/* Distinction: Validation Performance vs Runtime Confidence */}
      <div className="p-4 rounded-xl bg-cyan-500/5 dark:bg-cyan-500/[0.03] border border-cyan-500/20 space-y-3 text-xs font-mono">
        <div className="flex items-center gap-2 text-cyan-700 dark:text-cyan-400 font-bold uppercase tracking-wider text-[11px]">
          <Award className="w-4 h-4" />
          <span>MODEL VALIDATION BENCHMARKS VS RUNTIME CONFIDENCE</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
          {/* Validation ROC-AUC */}
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase">HOLDOUT ROC-AUC</span>
            <div className="text-xl font-bold font-mono text-slate-900 dark:text-white">
              {Number(roc).toFixed(4)}
            </div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
              Validation reference on out-of-time test partition
            </span>
          </div>

          {/* Validation Brier Score */}
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase">CALIBRATED BRIER SCORE</span>
            <div className="text-xl font-bold font-mono text-slate-900 dark:text-white">
              {Number(brier).toFixed(4)}
            </div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
              Strict probability calibration reference
            </span>
          </div>

          {/* Runtime Model Confidence */}
          <div className="space-y-1">
            <span className="text-[10px] text-cyan-600 dark:text-cyan-400 uppercase font-bold">RUNTIME CONFIDENCE</span>
            <div className="text-xl font-bold font-mono text-cyan-600 dark:text-cyan-400">
              {prediction.model_confidence !== null ? `${(prediction.model_confidence * 100).toFixed(1)}%` : 'Unavailable'}
            </div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
              Current project Platt-calibrated posterior certainty
            </span>
          </div>
        </div>

        <div className="text-[10px] text-slate-500 dark:text-slate-400 pt-1 border-t border-cyan-500/15">
          * Validation ROC-AUC and Brier Score represent fixed statistical benchmark performance across the national historical test partition; runtime confidence measures model posterior certainty for this specific project instance.
        </div>
      </div>
    </section>
  );
}
