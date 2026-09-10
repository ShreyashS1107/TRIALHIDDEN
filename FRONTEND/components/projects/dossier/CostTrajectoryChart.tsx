'use client';

import React, { useState } from 'react';
import { ProjectHistoricalRecord } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';

interface Props {
  timeline: ProjectHistoricalRecord[];
  originalCost: number;
  revisedCost: number;
}

export function CostTrajectoryChart({ timeline, originalCost, revisedCost }: Props) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // If no longitudinal snapshots, construct minimal 2-point fallback
  const points = timeline.length > 0 ? timeline : [
    {
      report_month: '2025-04',
      original_cost_crore: originalCost,
      revised_cost_crore: revisedCost,
      cumulative_expenditure_crore: 0,
      physical_progress_percent: 0
    },
    {
      report_month: '2026-06',
      original_cost_crore: originalCost,
      revised_cost_crore: revisedCost,
      cumulative_expenditure_crore: 0,
      physical_progress_percent: 0
    }
  ];

  // Calculate bounds
  let maxCost = Math.max(
    originalCost,
    revisedCost,
    ...points.map(p => Math.max(p.original_cost_crore || 0, p.revised_cost_crore || 0, p.cumulative_expenditure_crore || 0))
  );
  if (maxCost <= 0) maxCost = 100;
  // Give 15% headroom
  const yMax = maxCost * 1.15;

  // Dimensions
  const width = 800;
  const height = 320;
  const padLeft = 70;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 45;
  const graphWidth = width - padLeft - padRight;
  const graphHeight = height - padTop - padBottom;

  const n = points.length;
  const getX = (idx: number) => padLeft + (idx / Math.max(1, n - 1)) * graphWidth;
  const getY = (val: number) => padTop + graphHeight - (val / yMax) * graphHeight;

  // Path generators
  const origPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.original_cost_crore || originalCost)}`).join(' ');
  const revPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.revised_cost_crore || revisedCost)}`).join(' ');
  const spendLine = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.cumulative_expenditure_crore || 0)}`).join(' ');
  const spendArea = `${spendLine} L ${getX(n - 1)} ${getY(0)} L ${getX(0)} ${getY(0)} Z`;

  // Ticks
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(pct => ({
    val: Math.round(yMax * pct),
    y: getY(yMax * pct)
  }));

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 02 — Financial Velocity
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            COST TRAJECTORY
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Longitudinal comparison of sanctioned baseline, revised commitments, and cumulative capital expenditure.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 border-t border-dashed border-slate-400 dark:border-slate-500" />
            <span className="text-slate-500 dark:text-slate-400">Original Baseline</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-cyan-500" />
            <span className="text-cyan-600 dark:text-cyan-400 font-medium">Revised Budget</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/30 border border-emerald-500" />
            <span className="text-emerald-600 dark:text-emerald-400 font-medium">Cumulative Spend</span>
          </div>
        </div>
      </div>

      {/* SVG Container */}
      <div className="relative w-full overflow-x-auto">
        <div className="min-w-[650px]">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-auto overflow-visible select-none"
            onMouseLeave={() => setHoverIndex(null)}
          >
            <defs>
              <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            {/* Y Grid lines & Labels */}
            {yTicks.map((tick, i) => (
              <g key={i} className="text-slate-400 dark:text-slate-600">
                <line
                  x1={padLeft}
                  y1={tick.y}
                  x2={width - padRight}
                  y2={tick.y}
                  stroke="currentColor"
                  strokeOpacity={0.15}
                  strokeDasharray="3 3"
                />
                <text
                  x={padLeft - 10}
                  y={tick.y + 4}
                  textAnchor="end"
                  className="fill-slate-400 dark:fill-slate-500 text-[10px] font-mono"
                >
                  ₹{formatIndianNumber(tick.val)}
                </text>
              </g>
            ))}

            {/* Y-axis title */}
            <text
              x={padLeft - 10}
              y={padTop - 12}
              textAnchor="end"
              className="fill-slate-400 dark:fill-slate-500 text-[9px] font-mono uppercase tracking-wider"
            >
              (₹ Crore)
            </text>

            {/* Spend Area & Line */}
            <path d={spendArea} fill="url(#spendGrad)" />
            <path d={spendLine} fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

            {/* Original Cost Line (Dashed) */}
            <path
              d={origPath}
              fill="none"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="4 4"
              strokeOpacity={0.8}
            />

            {/* Revised Cost Line (Solid Cyan) */}
            <path
              d={revPath}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* X-axis ticks & labels */}
            {points.map((p, i) => {
              const x = getX(i);
              // Show label every few ticks if there are many
              const showLabel = n <= 8 || i === 0 || i === n - 1 || i % Math.ceil(n / 6) === 0;
              return (
                <g key={i}>
                  {showLabel && (
                    <text
                      x={x}
                      y={height - padBottom + 18}
                      textAnchor="middle"
                      className="fill-slate-400 dark:fill-slate-500 text-[10px] font-mono"
                    >
                      {p.report_month}
                    </text>
                  )}
                  {/* Data Points */}
                  <circle
                    cx={x}
                    cy={getY(p.cumulative_expenditure_crore || 0)}
                    r={hoverIndex === i ? 5 : 3}
                    className="fill-emerald-500 transition-all duration-150"
                  />
                  <circle
                    cx={x}
                    cy={getY(p.revised_cost_crore || revisedCost)}
                    r={hoverIndex === i ? 5 : 3}
                    className="fill-cyan-500 transition-all duration-150"
                  />
                </g>
              );
            })}

            {/* Hover vertical crosshair & interactive overlay columns */}
            {hoverIndex !== null && (
              <line
                x1={getX(hoverIndex)}
                y1={padTop}
                x2={getX(hoverIndex)}
                y2={height - padBottom}
                stroke="#06b6d4"
                strokeWidth="1.5"
                strokeDasharray="3 3"
                className="opacity-70"
              />
            )}

            {points.map((_, i) => (
              <rect
                key={i}
                x={getX(i) - graphWidth / (2 * n)}
                y={padTop}
                width={graphWidth / n}
                height={graphHeight}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={() => setHoverIndex(i)}
              />
            ))}
          </svg>
        </div>

        {/* Floating Tooltip */}
        {activePoint && (
          <div className="mt-3 p-3 rounded-xl bg-slate-900/95 dark:bg-black/90 text-white border border-cyan-500/30 shadow-xl max-w-sm font-mono text-xs space-y-1.5 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-white/10 pb-1">
              <span className="text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                Report Epoch:
              </span>
              <span className="text-cyan-400 font-bold">
                {activePoint.report_month}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-0.5 text-[11px]">
              <div className="text-slate-400">Original Cost:</div>
              <div className="text-right text-slate-200">₹{formatIndianNumber(activePoint.original_cost_crore || originalCost)} Cr</div>
              <div className="text-slate-400">Revised Cost:</div>
              <div className="text-right text-cyan-300 font-bold">₹{formatIndianNumber(activePoint.revised_cost_crore || revisedCost)} Cr</div>
              <div className="text-slate-400">Expenditure:</div>
              <div className="text-right text-emerald-400 font-bold">₹{formatIndianNumber(activePoint.cumulative_expenditure_crore || 0)} Cr</div>
              <div className="text-slate-400">Physical Progress:</div>
              <div className="text-right text-white font-bold">{activePoint.physical_progress_percent}%</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
