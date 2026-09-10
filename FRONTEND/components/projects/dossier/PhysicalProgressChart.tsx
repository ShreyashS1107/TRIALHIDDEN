'use client';

import React, { useState } from 'react';
import { ProjectHistoricalRecord } from '@/lib/api/types';

interface Props {
  timeline: ProjectHistoricalRecord[];
  currentProgress: number;
}

export function PhysicalProgressChart({ timeline, currentProgress }: Props) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const points = timeline.length > 0 ? timeline : [
    {
      report_month: '2025-04',
      original_cost_crore: 0,
      revised_cost_crore: 0,
      cumulative_expenditure_crore: 0,
      physical_progress_percent: 0
    },
    {
      report_month: '2026-06',
      original_cost_crore: 0,
      revised_cost_crore: 0,
      cumulative_expenditure_crore: 0,
      physical_progress_percent: currentProgress
    }
  ];

  // SVG Chart Dimensions
  const width = 800;
  const height = 280;
  const padLeft = 60;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 45;
  const graphWidth = width - padLeft - padRight;
  const graphHeight = height - padTop - padBottom;

  const n = points.length;
  const getX = (idx: number) => padLeft + (idx / Math.max(1, n - 1)) * graphWidth;
  const getY = (val: number) => padTop + graphHeight - (Math.min(100, Math.max(0, val)) / 100) * graphHeight;

  // Path
  const progressLine = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.physical_progress_percent || 0)}`).join(' ');
  const progressArea = `${progressLine} L ${getX(n - 1)} ${getY(0)} L ${getX(0)} ${getY(0)} Z`;

  // Detect unusual progress shifts (stagnations or rapid leaps)
  const anomalies: { index: number; type: 'leap' | 'stagnation'; text: string }[] = [];
  for (let i = 1; i < points.length; i++) {
    const diff = (points[i].physical_progress_percent || 0) - (points[i - 1].physical_progress_percent || 0);
    if (diff >= 12) {
      anomalies.push({ index: i, type: 'leap', text: `Accelerated Progress (+${diff.toFixed(1)}%)` });
    } else if (diff === 0 && i >= 2 && (points[i - 1].physical_progress_percent || 0) === (points[i - 2].physical_progress_percent || 0)) {
      anomalies.push({ index: i, type: 'stagnation', text: 'Telemetry Stagnation Plateau' });
    }
  }

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 04 — Execution Velocity
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            PHYSICAL PROGRESS OVER TIME
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Historical trajectory of verified physical milestones completed across reporting epochs.
          </p>
        </div>

        {/* Current status pill */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Latest Verified Progress:</span>
          <span className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-mono font-bold text-sm border border-cyan-500/20">
            {currentProgress}%
          </span>
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
              <linearGradient id="progressGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            {/* Y Grid lines: 0%, 25%, 50%, 75%, 100% */}
            {[0, 25, 50, 75, 100].map(pct => {
              const y = getY(pct);
              return (
                <g key={pct}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={width - padRight}
                    y2={y}
                    stroke="currentColor"
                    className="text-slate-200 dark:text-white/10"
                    strokeDasharray="3 3"
                  />
                  <text
                    x={padLeft - 10}
                    y={y + 4}
                    textAnchor="end"
                    className="fill-slate-400 dark:fill-slate-500 text-[10px] font-mono"
                  >
                    {pct}%
                  </text>
                </g>
              );
            })}

            {/* 100% Target reference line */}
            <line
              x1={padLeft}
              y1={getY(100)}
              x2={width - padRight}
              y2={getY(100)}
              stroke="#10b981"
              strokeWidth="1"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />
            <text
              x={width - padRight}
              y={getY(100) - 6}
              textAnchor="end"
              className="fill-emerald-500 text-[9px] font-mono font-semibold"
            >
              100% COMPLETION TARGET
            </text>

            {/* Progress Area & Line */}
            <path d={progressArea} fill="url(#progressGrad)" />
            <path
              d={progressLine}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* X-axis ticks & labels */}
            {points.map((p, i) => {
              const x = getX(i);
              const y = getY(p.physical_progress_percent || 0);
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
                  {/* Point circle */}
                  <circle
                    cx={x}
                    cy={y}
                    r={hoverIndex === i ? 5.5 : 3.5}
                    className="fill-cyan-500 stroke-2 stroke-white dark:stroke-[#06131c] transition-all duration-150"
                  />
                </g>
              );
            })}

            {/* Anomaly Callout Badges */}
            {anomalies.map((anom, idx) => {
              const x = getX(anom.index);
              const y = getY(points[anom.index].physical_progress_percent || 0);
              return (
                <g key={idx}>
                  <circle cx={x} cy={y} r={6} fill="none" stroke={anom.type === 'leap' ? '#10b981' : '#f59e0b'} strokeWidth="2" className="animate-ping opacity-60" />
                </g>
              );
            })}

            {/* Hover crosshair */}
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

            {/* Interactive hit areas */}
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

        {/* Hover summary card */}
        {activePoint && (
          <div className="mt-3 p-3 rounded-xl bg-slate-900/95 dark:bg-black/90 text-white border border-cyan-500/30 shadow-xl max-w-sm font-mono text-xs space-y-1 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-white/10 pb-1">
              <span className="text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                Month: {activePoint.report_month}
              </span>
              <span className="text-cyan-400 font-bold">
                Progress: {activePoint.physical_progress_percent}%
              </span>
            </div>
            <div className="text-[11px] text-slate-300">
              Cumulative Spend: ₹{(activePoint.cumulative_expenditure_crore || 0).toFixed(2)} Cr
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
