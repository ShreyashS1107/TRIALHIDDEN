'use client';

import React from 'react';
import Link from 'next/link';
import { CustomProjectInput, CustomProjectPredictionResponse } from '@/lib/api/predict';
import { formatIndianNumber } from '@/lib/utils/format';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  IndianRupee,
  TrendingUp,
  Cpu,
  Download,
  Edit3,
  RotateCcw,
  ArrowLeft,
  Share2,
  Activity,
  Layers,
  Sparkles
} from 'lucide-react';

interface Props {
  input: CustomProjectInput;
  result: CustomProjectPredictionResponse;
  onEdit: () => void;
  onReset: () => void;
}

export function CustomProjectResult({ input, result, onEdit, onReset }: Props) {
  const costOverrunPct = Math.round(result.cost_overrun_risk * 100);
  const timeOverrunPct = Math.round(result.schedule_delay_risk * 100);
  const overallRiskPct = Math.round(result.selected_integrated_risk * 100);

  const bandStyles: Record<string, { bg: string; text: string; border: string; glow: string }> = {
    LOW: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-500 dark:text-emerald-400',
      border: 'border-emerald-500/30',
      glow: 'shadow-[0_0_25px_rgba(16,185,129,0.15)]'
    },
    MEDIUM: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-500 dark:text-amber-400',
      border: 'border-amber-500/30',
      glow: 'shadow-[0_0_25px_rgba(245,158,11,0.15)]'
    },
    MODERATE: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-500 dark:text-amber-400',
      border: 'border-amber-500/30',
      glow: 'shadow-[0_0_25px_rgba(245,158,11,0.15)]'
    },
    HIGH: {
      bg: 'bg-rose-500/10',
      text: 'text-rose-500 dark:text-rose-400',
      border: 'border-rose-500/30',
      glow: 'shadow-[0_0_25px_rgba(244,63,94,0.2)]'
    },
    VERY_HIGH: {
      bg: 'bg-rose-600/10',
      text: 'text-rose-600 dark:text-rose-400',
      border: 'border-rose-600/30',
      glow: 'shadow-[0_0_30px_rgba(225,29,72,0.25)]'
    }
  };

  const currentTheme = bandStyles[result.risk_band] || bandStyles.LOW;

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({ input, result }, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `PAIMANA_Assessment_${result.project_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Result Hero Header */}
      <div className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="px-2.5 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-bold border border-cyan-500/20">
              CUSTOM ASSESSMENT DOSSIER
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-white/5 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-white/10">
              ID: {result.project_id}
            </span>
            <span className="text-slate-500 dark:text-slate-400">• {result.agency}</span>
            <span className="text-slate-500 dark:text-slate-400">• {result.state}</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {result.project_name}
          </h2>
        </div>

        <div className="flex items-center gap-2 self-start md:self-center">
          <button
            onClick={handleDownload}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-white/5 border border-slate-300 dark:border-white/10 text-xs font-mono font-bold text-slate-700 dark:text-slate-300 hover:text-cyan-500 transition-colors"
            title="Download JSON dossier"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT DOSSIER</span>
          </button>
        </div>
      </div>

      {/* 4 PRIMARY RESULT CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: PREDICTED COST OVERRUN */}
        <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between text-xs font-mono uppercase text-slate-500 dark:text-slate-400">
            <span>Predicted Cost Overrun</span>
            <IndianRupee className="w-4 h-4 text-cyan-500" />
          </div>
          <div>
            <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
              {costOverrunPct}%
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-1">
              Budget Escalation Probability
            </div>
          </div>
          <div className="w-full bg-slate-200 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${costOverrunPct}%` }} />
          </div>
        </div>

        {/* Card 2: PREDICTED TIME OVERRUN */}
        <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between text-xs font-mono uppercase text-slate-500 dark:text-slate-400">
            <span>Predicted Time Overrun</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div>
            <div className="text-3xl font-extrabold font-mono text-amber-500">
              {timeOverrunPct}%
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-1">
              Schedule Delay Probability
            </div>
          </div>
          <div className="w-full bg-slate-200 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-amber-500 h-full rounded-full" style={{ width: `${timeOverrunPct}%` }} />
          </div>
        </div>

        {/* Card 3: OVERALL RISK */}
        <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between text-xs font-mono uppercase text-slate-500 dark:text-slate-400">
            <span>Overall Risk Score</span>
            <Cpu className="w-4 h-4 text-cyan-500" />
          </div>
          <div>
            <div className="text-3xl font-extrabold font-mono text-cyan-600 dark:text-cyan-400">
              {overallRiskPct}%
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-1">
              Evidence-Weighted Composite
            </div>
          </div>
          <div className="w-full bg-slate-200 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-cyan-400 h-full rounded-full" style={{ width: `${overallRiskPct}%` }} />
          </div>
        </div>

        {/* Card 4: RISK LEVEL */}
        <div className={`p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border ${currentTheme.border} ${currentTheme.glow} shadow-sm flex flex-col justify-between space-y-3`}>
          <div className="flex items-center justify-between text-xs font-mono uppercase text-slate-500 dark:text-slate-400">
            <span>Risk Classification</span>
            <ShieldAlert className="w-4 h-4 text-cyan-500" />
          </div>
          <div>
            <div className={`text-2xl sm:text-3xl font-extrabold font-mono ${currentTheme.text}`}>
              {result.risk_band} RISK
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-1">
              Dominant: {result.dominant_component}
            </div>
          </div>
          <span className={`inline-flex items-center justify-center text-[10px] font-mono font-bold py-1 px-2.5 rounded-full border ${currentTheme.bg} ${currentTheme.text} ${currentTheme.border}`}>
            OVERSIGHT TIER VALIDATED
          </span>
        </div>
      </div>

      {/* ANALYTICAL COMPARATIVE VISUALIZERS: OBSERVED VS PREDICTED */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visualizer 1: Financial Trajectory */}
        <div className="p-6 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Analytical Visualizer 01
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Capital Expenditure & Forecast Outlay
              </h3>
            </div>
            <div className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-white/5 text-slate-500">
              ₹ Crore
            </div>
          </div>

          <div className="space-y-4 pt-2">
            {/* Bar 1: Original Cost (Observed) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                  <span>Approved Cost</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-slate-400 font-semibold">
                    [OBSERVED DATA]
                  </span>
                </span>
                <span className="font-bold text-slate-900 dark:text-white">
                  ₹{formatIndianNumber(input.original_cost_crore)} Cr
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-white/10 h-2.5 rounded-full overflow-hidden">
                <div className="bg-slate-400 h-full rounded-full" style={{ width: '60%' }} />
              </div>
            </div>

            {/* Bar 2: Revised Cost (Observed) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                  <span>Revised Budget</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-semibold">
                    [OBSERVED DATA]
                  </span>
                </span>
                <span className="font-bold text-cyan-600 dark:text-cyan-400">
                  ₹{formatIndianNumber(input.revised_cost_crore)} Cr
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-white/10 h-2.5 rounded-full overflow-hidden">
                <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${Math.min(100, (input.revised_cost_crore / Math.max(1, result.predicted_cost_crore)) * 100)}%` }} />
              </div>
            </div>

            {/* Bar 3: Predicted Cost (Predicted) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                  <span>Anticipated Terminal Cost</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-semibold">
                    [PREDICTED DATA]
                  </span>
                </span>
                <span className="font-bold text-amber-500">
                  ₹{formatIndianNumber(result.predicted_cost_crore)} Cr
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-white/10 h-2.5 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 text-xs text-slate-600 dark:text-slate-400 font-mono">
            Model projects potential additional financial variance of <strong className="text-amber-500">+₹{(result.predicted_cost_crore - input.revised_cost_crore).toFixed(2)} Cr</strong> based on current execution trajectory.
          </div>
        </div>

        {/* Visualizer 2: Schedule Trajectory */}
        <div className="p-6 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Analytical Visualizer 02
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Schedule Milestones & Projected Slippage
              </h3>
            </div>
            <div className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-white/5 text-slate-500">
              Months
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <div className="grid grid-cols-3 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10">
                <div className="text-[9px] uppercase text-slate-400">Approved Target</div>
                <div className="font-bold text-slate-900 dark:text-white mt-1">{input.original_completion_date}</div>
                <div className="text-[9px] text-cyan-500 mt-0.5">[OBSERVED]</div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10">
                <div className="text-[9px] uppercase text-slate-400">Revised Target</div>
                <div className="font-bold text-slate-900 dark:text-white mt-1">
                  {input.revised_completion_date || 'None'}
                </div>
                <div className="text-[9px] text-cyan-500 mt-0.5">[OBSERVED]</div>
              </div>

              <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/30">
                <div className="text-[9px] uppercase text-amber-600 dark:text-amber-400 font-bold">Forecast Horizon</div>
                <div className="font-bold text-amber-500 mt-1">{result.predicted_completion_date}</div>
                <div className="text-[9px] text-amber-500 mt-0.5">[PREDICTED]</div>
              </div>
            </div>

            {/* Delay callout */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-500" />
                <span className="text-slate-600 dark:text-slate-400">Forecast Milestone Extension:</span>
              </div>
              <span className="font-bold text-amber-500">
                +{result.predicted_delay_months} Months Delay Debt
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* RISK DRIVERS PANEL */}
      <div className="p-6 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-white/10 pb-3">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              Root-Cause Attribution
            </span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Model-Generated Risk Drivers
            </h3>
          </div>
          <div className="text-xs font-mono text-slate-500">
            Engine: {result.model_version}
          </div>
        </div>

        <div className="space-y-3.5 pt-1">
          {result.risk_drivers.map((driver, index) => (
            <div
              key={driver.id}
              className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-white/10 text-[11px] font-mono font-bold flex items-center justify-center text-slate-700 dark:text-slate-300">
                    {index + 1}
                  </span>
                  <span className="font-bold text-sm text-slate-900 dark:text-white">
                    {driver.name}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                      driver.impact_level === 'High impact'
                        ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                        : driver.impact_level === 'Medium impact'
                        ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                        : 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                    }`}
                  >
                    {driver.impact_level}
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-900 dark:text-white min-w-[36px] text-right">
                    {driver.impact_pct}%
                  </span>
                </div>
              </div>

              {/* Bar */}
              <div className="w-full bg-slate-200 dark:bg-white/10 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    driver.impact_level === 'High impact'
                      ? 'bg-rose-500'
                      : driver.impact_level === 'Medium impact'
                      ? 'bg-amber-500'
                      : 'bg-cyan-500'
                  }`}
                  style={{ width: `${Math.max(4, driver.impact_pct)}%` }}
                />
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-400">
                {driver.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* FINAL ACTION BUTTONS */}
      <div className="p-6 rounded-2xl bg-white dark:bg-[#06131c]/80 border border-slate-200 dark:border-white/10 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onEdit}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-300 dark:border-white/10 text-xs font-mono font-bold text-slate-800 dark:text-slate-200 transition-colors"
          >
            <Edit3 className="w-4 h-4 text-cyan-500" />
            <span>EDIT PROJECT</span>
          </button>

          <button
            onClick={handleDownload}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-300 dark:border-white/10 text-xs font-mono font-bold text-slate-800 dark:text-slate-200 transition-colors"
          >
            <Download className="w-4 h-4 text-emerald-500" />
            <span>SAVE ASSESSMENT</span>
          </button>

          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 border border-slate-300 dark:border-white/10 text-xs font-mono font-bold text-slate-800 dark:text-slate-200 transition-colors"
          >
            <RotateCcw className="w-4 h-4 text-amber-500" />
            <span>RUN ANOTHER PROJECT</span>
          </button>
        </div>

        <div>
          <Link
            href="/projects"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-700 dark:text-cyan-400 text-xs font-mono font-bold tracking-wider transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>BACK TO PROJECT SEARCH</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
