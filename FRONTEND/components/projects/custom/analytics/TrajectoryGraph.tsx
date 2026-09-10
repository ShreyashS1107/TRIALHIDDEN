'use client';

import React from 'react';
import { CustomProjectPredictionResponse, CustomProjectInput } from '@/lib/api/predict';
import { formatIndianNumber } from '@/lib/utils/format';
import { TrendingUp, AlertTriangle, Calendar, IndianRupee, Compass, Layers } from 'lucide-react';

interface Props {
  input: CustomProjectInput;
  prediction: CustomProjectPredictionResponse;
}

export function TrajectoryGraph({ input, prediction }: Props) {
  const origCost = Number(prediction.original_cost_crore ?? input.original_cost_crore) || 1000;
  const revCost = Number(prediction.revised_cost_crore ?? input.revised_cost_crore) || origCost;
  const currSpend = prediction.cumulative_expenditure_crore !== undefined && prediction.cumulative_expenditure_crore !== null
    ? Number(prediction.cumulative_expenditure_crore)
    : (input.cumulative_expenditure_crore !== undefined && input.cumulative_expenditure_crore !== null ? Number(input.cumulative_expenditure_crore) : null);
  const predCost = Number(prediction.predicted_cost_crore) || revCost;

  const startDate = input.approval_start_date || '2023-01';
  const origDoc = input.original_completion_date || '2026-12';
  const revDoc = input.revised_completion_date || prediction.revised_completion_date || origDoc;
  const predDoc = prediction.predicted_completion_date || revDoc;
  const obsDate = '2026-09'; // Observation date anchor

  const hasSpend = currSpend !== null && currSpend >= 0;
  const displaySpend = hasSpend ? currSpend : origCost * 0.45;

  // Max scale bounds for SVG (width 600, height 260)
  const maxCost = Math.max(origCost, revCost, predCost, displaySpend, 1) * 1.15;
  const h = 220;
  const padLeft = 60;
  const padRight = 40;
  const padTop = 30;
  const padBottom = 40;
  const graphWidth = 500;
  const graphHeight = h - padTop - padBottom;

  // Normalized coordinates (X: timeline 0 to 1, Y: cost 0 to maxCost)
  // X anchors:
  // 0.00: Start Date
  // 0.45: Current Observation Date
  // 0.70: Planned Original DOC
  // 0.85: Revised DOC
  // 1.00: ML Predicted DOC
  const yVal = (c: number) => padTop + graphHeight - (c / maxCost) * graphHeight;

  const ptStart = { x: padLeft, y: yVal(0) };
  const ptObserved = { x: padLeft + graphWidth * 0.45, y: yVal(displaySpend) };
  const ptPlanned = { x: padLeft + graphWidth * 0.72, y: yVal(origCost) };
  const ptRevised = { x: padLeft + graphWidth * 0.86, y: yVal(revCost) };
  const ptPredicted = { x: padLeft + graphWidth * 1.0, y: yVal(predCost) };

  return (
    <section className="p-6 sm:p-7 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
              ANALYTICAL TRAJECTORY COMPARISON
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 font-bold">
              PLANNED • OBSERVED • PREDICTED
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white pt-1">
            CAPITAL EXPENDITURE & DELIVERY TRAJECTORY
          </h3>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 bg-slate-400 border-b border-dashed border-slate-400" />
            <span className="text-slate-600 dark:text-slate-400">Planned Baseline</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-1 bg-cyan-500 rounded" />
            <span className="text-slate-900 dark:text-white font-semibold">Solid = Observed</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 bg-amber-500 border-b-2 border-dashed border-amber-500" />
            <span className="text-amber-600 dark:text-amber-400 font-semibold">Dashed = Predicted</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="w-full overflow-x-auto">
        <svg viewBox="0 0 620 230" className="w-full min-w-[580px] h-56 select-none overflow-visible">
          {/* Background Grid Lines */}
          <line x1={padLeft} y1={padTop} x2={padLeft + graphWidth} y2={padTop} stroke="currentColor" strokeOpacity="0.08" />
          <line x1={padLeft} y1={padTop + graphHeight * 0.5} x2={padLeft + graphWidth} y2={padTop + graphHeight * 0.5} stroke="currentColor" strokeOpacity="0.08" />
          <line x1={padLeft} y1={padTop + graphHeight} x2={padLeft + graphWidth} y2={padTop + graphHeight} stroke="currentColor" strokeOpacity="0.15" />

          {/* Y Axis Cost Labels */}
          <text x={padLeft - 10} y={padTop + 4} textAnchor="end" className="text-[10px] font-mono fill-slate-400 font-bold">
            ₹{formatIndianNumber(Math.round(maxCost))} Cr
          </text>
          <text x={padLeft - 10} y={padTop + graphHeight * 0.5 + 4} textAnchor="end" className="text-[10px] font-mono fill-slate-400">
            ₹{formatIndianNumber(Math.round(maxCost * 0.5))} Cr
          </text>
          <text x={padLeft - 10} y={padTop + graphHeight + 4} textAnchor="end" className="text-[10px] font-mono fill-slate-400">
            ₹0 Cr
          </text>

          {/* Planned Trajectory (Dotted Gray line: Start -> Planned Target) */}
          <line
            x1={ptStart.x}
            y1={ptStart.y}
            x2={ptPlanned.x}
            y2={ptPlanned.y}
            stroke="#94a3b8"
            strokeWidth="2"
            strokeDasharray="4 4"
          />

          {/* Observed Trajectory (Solid Cyan Line: Start -> Observed Point) */}
          <line
            x1={ptStart.x}
            y1={ptStart.y}
            x2={ptObserved.x}
            y2={ptObserved.y}
            stroke="#06b6d4"
            strokeWidth="3.5"
            strokeLinecap="round"
          />

          {/* Forecasted Trajectory (Dashed Amber Line: Observed Point -> Predicted DOC) */}
          <line
            x1={ptObserved.x}
            y1={ptObserved.y}
            x2={ptPredicted.x}
            y2={ptPredicted.y}
            stroke="#f59e0b"
            strokeWidth="3.5"
            strokeDasharray="6 5"
            strokeLinecap="round"
          />

          {/* Node 1: Start Point */}
          <circle cx={ptStart.x} cy={ptStart.y} r="4.5" fill="#06b6d4" className="shadow" />
          <text x={ptStart.x} y={ptStart.y + 18} textAnchor="middle" className="text-[10px] font-mono fill-slate-500 font-semibold">
            {startDate} (Start)
          </text>

          {/* Node 2: Observed Point */}
          <circle cx={ptObserved.x} cy={ptObserved.y} r="6" fill="#06b6d4" stroke="#ffffff" strokeWidth="2" />
          <rect x={ptObserved.x - 55} y={ptObserved.y - 30} width="110" height="22" rx="6" fill="#0e7490" fillOpacity="0.9" />
          <text x={ptObserved.x} y={ptObserved.y - 16} textAnchor="middle" className="text-[10px] font-mono fill-white font-bold">
            {hasSpend ? `Observed: ₹${formatIndianNumber(currSpend!)} Cr` : 'Certified Progress'}
          </text>
          <text x={ptObserved.x} y={ptStart.y + 18} textAnchor="middle" className="text-[10px] font-mono fill-cyan-600 dark:fill-cyan-400 font-bold">
            {obsDate} (Current)
          </text>

          {/* Node 3: Planned Target */}
          <circle cx={ptPlanned.x} cy={ptPlanned.y} r="4.5" fill="#94a3b8" />
          <text x={ptPlanned.x} y={ptPlanned.y - 12} textAnchor="middle" className="text-[10px] font-mono fill-slate-400 font-bold">
            ₹{formatIndianNumber(origCost)} Cr
          </text>
          <text x={ptPlanned.x} y={ptStart.y + 18} textAnchor="middle" className="text-[10px] font-mono fill-slate-400">
            {origDoc} (Planned)
          </text>

          {/* Node 4: Predicted Target */}
          <circle cx={ptPredicted.x} cy={ptPredicted.y} r="6.5" fill="#f59e0b" stroke="#ffffff" strokeWidth="2" className="animate-pulse" />
          <rect x={ptPredicted.x - 65} y={ptPredicted.y - 32} width="130" height="24" rx="6" fill="#b45309" fillOpacity="0.95" />
          <text x={ptPredicted.x} y={ptPredicted.y - 17} textAnchor="middle" className="text-[10px] font-mono fill-white font-bold">
            Forecast: ₹{formatIndianNumber(predCost)} Cr
          </text>
          <text x={ptPredicted.x} y={ptStart.y + 18} textAnchor="middle" className="text-[10px] font-mono fill-amber-500 font-bold">
            {predDoc} (Forecast)
          </text>
        </svg>
      </div>

      {/* Trajectory Metrics Summary Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 text-xs font-mono">
          <span className="text-[10px] text-slate-500 uppercase block">1. Planned Baseline</span>
          <p className="font-bold text-slate-900 dark:text-white pt-0.5">
            ₹{formatIndianNumber(origCost)} Cr by {origDoc}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/20 text-xs font-mono">
          <span className="text-[10px] text-cyan-600 dark:text-cyan-400 uppercase font-bold block">2. Observed Execution</span>
          <p className="font-bold text-slate-900 dark:text-white pt-0.5">
            {hasSpend ? `₹${formatIndianNumber(currSpend!)} Cr cumulative spend` : 'Physical progress active'} ({input.physical_progress_percent}% progress)
          </p>
        </div>

        <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs font-mono">
          <span className="text-[10px] text-amber-600 dark:text-amber-400 uppercase font-bold block">3. ML Risk Forecast</span>
          <p className="font-bold text-amber-600 dark:text-amber-400 pt-0.5">
            ₹{formatIndianNumber(predCost)} Cr by {predDoc} (+{prediction.predicted_delay_months}m delay)
          </p>
        </div>
      </div>
    </section>
  );
}
