'use client';

import React from 'react';
import { CustomProjectPredictionResponse, CustomProjectInput } from '@/lib/api/predict';
import { formatIndianNumber } from '@/lib/utils/format';
import { IndianRupee, TrendingUp, AlertTriangle, ArrowRight, Layers } from 'lucide-react';

interface Props {
  input: CustomProjectInput;
  prediction: CustomProjectPredictionResponse;
}

export function CostAnalytics({ input, prediction }: Props) {
  const origCost = Number(prediction.original_cost_crore ?? input.original_cost_crore) || 0;
  const revCost = Number(prediction.revised_cost_crore ?? input.revised_cost_crore) || origCost;
  const currExp = prediction.cumulative_expenditure_crore !== undefined && prediction.cumulative_expenditure_crore !== null
    ? Number(prediction.cumulative_expenditure_crore)
    : (input.cumulative_expenditure_crore !== undefined && input.cumulative_expenditure_crore !== null ? Number(input.cumulative_expenditure_crore) : null);
  const predCost = Number(prediction.predicted_cost_crore) || revCost;

  // Cost Escalation over original sanction
  const escalationDelta = Math.max(0, revCost - origCost);
  const escalationPct = origCost > 0 ? (escalationDelta / origCost) * 100 : 0;

  // Expected Additional Exposure over revised budget
  const additionalExposure = Math.max(0, predCost - revCost);

  // Maximum value for proportional bar scale
  const maxBarValue = Math.max(origCost, revCost, predCost, currExp || 0, 1);

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-amber-600 dark:text-amber-400 font-bold">
              FINANCIAL EXPOSURE AUDIT
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-500">
              OBSERVED VS FORECAST
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            COST ANALYSIS & CAPITAL EXPOSURE
          </h3>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
            <span className="text-slate-600 dark:text-slate-400">Observed Baselines</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-slate-600 dark:text-slate-400">ML Forecast</span>
          </div>
        </div>
      </div>

      {/* 4 Financial Milestones (Original -> Revised -> Current Spend -> Predicted) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Original Sanction */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
            <span>ORIGINAL SANCTION</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
              OBSERVED
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            ₹{formatIndianNumber(origCost)} Cr
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            Initial sanctioned capital envelope
          </div>
        </div>

        {/* Card 2: Revised Anticipated Cost */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
            <span>REVISED ANTICIPATED</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
              OBSERVED
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            ₹{formatIndianNumber(revCost)} Cr
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            {escalationPct > 0 ? (
              <span className="text-rose-600 dark:text-rose-400 font-semibold">
                +{escalationPct.toFixed(1)}% escalation
              </span>
            ) : (
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                0.0% variance
              </span>
            )}
            <span>(₹{formatIndianNumber(escalationDelta)} Cr)</span>
          </div>
        </div>

        {/* Card 3: Current Cumulative Expenditure */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 dark:text-slate-400">
            <span>CUMULATIVE EXPENDITURE</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
              OBSERVED
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            {currExp !== null ? `₹${formatIndianNumber(currExp)} Cr` : 'Not available'}
          </div>
          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
            {currExp !== null && revCost > 0
              ? `${((currExp / revCost) * 100).toFixed(1)}% of revised budget disbursed`
              : 'Cumulative spend not submitted'}
          </div>
        </div>

        {/* Card 4: Predicted / Forecast Cost */}
        <div className="p-4 rounded-xl bg-amber-500/5 dark:bg-amber-500/[0.04] border border-amber-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-amber-600 dark:text-amber-400">
            <span className="font-bold">FORECASTED COMPLETION</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 font-bold">
              PREDICTED
            </span>
          </div>
          <div className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
            ₹{formatIndianNumber(predCost)} Cr
          </div>
          <div className="text-[11px] font-mono text-amber-700/80 dark:text-amber-300/80">
            Expected exposure: +₹{formatIndianNumber(additionalExposure)} Cr
          </div>
        </div>
      </div>

      {/* Visual Proportional Comparison Bar Chart */}
      <div className="p-5 rounded-xl bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/5 space-y-4">
        <div className="text-xs font-mono uppercase tracking-wider text-slate-600 dark:text-slate-400 font-semibold">
          FINANCIAL TRAJECTORY EXPANSION
        </div>

        <div className="space-y-3">
          {/* Original Cost Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] font-mono text-slate-600 dark:text-slate-400">
              <span className="flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-slate-400" />
                Original Approved Cost
              </span>
              <span className="font-semibold text-slate-900 dark:text-white">₹{formatIndianNumber(origCost)} Cr</span>
            </div>
            <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-white/5 overflow-hidden">
              <div
                className="h-full bg-slate-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (origCost / maxBarValue) * 100)}%` }}
              />
            </div>
          </div>

          {/* Revised Cost Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] font-mono text-slate-600 dark:text-slate-400">
              <span className="flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-cyan-500" />
                Revised Anticipated Cost (Approved Escalation)
              </span>
              <span className="font-semibold text-slate-900 dark:text-white">₹{formatIndianNumber(revCost)} Cr</span>
            </div>
            <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-white/5 overflow-hidden">
              <div
                className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (revCost / maxBarValue) * 100)}%` }}
              />
            </div>
          </div>

          {/* Current Expenditure Bar */}
          {currExp !== null && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono text-slate-600 dark:text-slate-400">
                <span className="flex items-center gap-1.5 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  Cumulative Expenditure to Date
                </span>
                <span className="font-semibold text-slate-900 dark:text-white">₹{formatIndianNumber(currExp)} Cr</span>
              </div>
              <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-white/5 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (currExp / maxBarValue) * 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* Predicted Terminal Cost Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] font-mono text-amber-600 dark:text-amber-400">
              <span className="flex items-center gap-1.5 font-semibold">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Model Forecasted Terminal Cost
              </span>
              <span className="font-bold">₹{formatIndianNumber(predCost)} Cr</span>
            </div>
            <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-white/5 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 via-amber-500 to-rose-500 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (predCost / maxBarValue) * 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
