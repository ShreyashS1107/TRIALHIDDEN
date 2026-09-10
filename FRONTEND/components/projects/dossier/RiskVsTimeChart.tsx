'use client';

import React, { useState } from 'react';
import { ProjectRiskSnapshot } from '@/lib/api/types';
import { TrendingUp, TrendingDown, Minus, Activity, ShieldCheck } from 'lucide-react';

interface Props {
  riskTrajectory: ProjectRiskSnapshot[];
  currentRisk: number | null;
  previousRisk: number | null;
  riskTrend: 'increasing' | 'stable' | 'decreasing';
}

export function RiskVsTimeChart({
  riskTrajectory,
  currentRisk,
  previousRisk,
  riskTrend
}: Props) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const hasData = riskTrajectory && riskTrajectory.length > 0;

  // Form points
  const points = hasData ? riskTrajectory : [];

  // Dimensions
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
  const getY = (val: number) => padTop + graphHeight - (Math.min(1, Math.max(0, val))) * graphHeight;

  const riskLine = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.selected_integrated_risk)}`).join(' ');
  const riskArea = points.length > 0
    ? `${riskLine} L ${getX(n - 1)} ${getY(0)} L ${getX(0)} ${getY(0)} Z`
    : '';

  const activePoint = hoverIndex !== null && points[hoverIndex] ? points[hoverIndex] : null;

  const trendConfig = {
    increasing: {
      icon: <TrendingUp className="w-4 h-4 text-rose-500" />,
      text: '↑ Increasing Risk Trajectory',
      style: 'text-rose-600 dark:text-rose-400 bg-rose-500/10 border-rose-500/20'
    },
    stable: {
      icon: <Minus className="w-4 h-4 text-cyan-500" />,
      text: '→ Stable Risk Profile',
      style: 'text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 border-cyan-500/20'
    },
    decreasing: {
      icon: <TrendingDown className="w-4 h-4 text-emerald-500" />,
      text: '↓ Decreasing Risk Trajectory',
      style: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    }
  };

  const trendBadge = trendConfig[riskTrend] || trendConfig.stable;

  const currRiskPct = currentRisk !== null ? `${Math.round(currentRisk * 100)}%` : 'N/A';
  const prevRiskPct = previousRisk !== null ? `${Math.round(previousRisk * 100)}%` : 'N/A';

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-semibold">
            Section 07 — Longitudinal Vulnerability
          </span>
          <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            RISK TRAJECTORY OVER TIME
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Temporal evolution of multi-target integrated risk probability across monthly model epochs.
          </p>
        </div>

        {/* Current Trend Badge */}
        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-mono font-bold ${trendBadge.style}`}>
          {trendBadge.icon}
          <span>{trendBadge.text}</span>
        </div>
      </div>

      {/* Metric Highlights */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10">
          <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase">
            Current Risk Score
          </div>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-1">
            {currRiskPct}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10">
          <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase">
            Previous Month Risk
          </div>
          <div className="text-xl font-bold font-mono text-slate-600 dark:text-slate-300 mt-1">
            {prevRiskPct}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 col-span-2 sm:col-span-1">
          <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase">
            Trajectory Trend
          </div>
          <div className="text-sm font-bold font-mono text-cyan-600 dark:text-cyan-400 mt-1 uppercase">
            {riskTrend}
          </div>
        </div>
      </div>

      {/* SVG Chart or Empty State */}
      {hasData ? (
        <div className="relative w-full overflow-x-auto">
          <div className="min-w-[650px]">
            <svg
              viewBox={`0 0 ${width} ${height}`}
              className="w-full h-auto overflow-visible select-none"
              onMouseLeave={() => setHoverIndex(null)}
            >
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.01" />
                </linearGradient>
              </defs>

              {/* Y Grid lines (0% to 100%) */}
              {[0, 0.25, 0.5, 0.75, 1].map(val => {
                const y = getY(val);
                return (
                  <g key={val}>
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
                      {Math.round(val * 100)}%
                    </text>
                  </g>
                );
              })}

              {/* Moderate & High Risk Threshold Bands */}
              <line
                x1={padLeft}
                y1={getY(0.5)}
                x2={width - padRight}
                y2={getY(0.5)}
                stroke="#f59e0b"
                strokeWidth="1"
                strokeDasharray="2 2"
                strokeOpacity={0.6}
              />
              <text
                x={width - padRight}
                y={getY(0.5) - 4}
                textAnchor="end"
                className="fill-amber-500 text-[9px] font-mono"
              >
                MODERATE RISK THRESHOLD (50%)
              </text>

              {/* Area & Line */}
              <path d={riskArea} fill="url(#riskGrad)" />
              <path
                d={riskLine}
                fill="none"
                stroke="#f43f5e"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Ticks and Dots */}
              {points.map((p, i) => {
                const x = getX(i);
                const y = getY(p.selected_integrated_risk);
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
                        {p.month}
                      </text>
                    )}
                    <circle
                      cx={x}
                      cy={y}
                      r={hoverIndex === i ? 5.5 : 3.5}
                      className="fill-rose-500 stroke-2 stroke-white dark:stroke-[#06131c] transition-all duration-150"
                    />
                  </g>
                );
              })}

              {/* Hover Crosshair */}
              {hoverIndex !== null && (
                <line
                  x1={getX(hoverIndex)}
                  y1={padTop}
                  x2={getX(hoverIndex)}
                  y2={height - padBottom}
                  stroke="#f43f5e"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                  className="opacity-70"
                />
              )}

              {/* Hit areas */}
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

          {/* Hover Tooltip */}
          {activePoint && (
            <div className="mt-3 p-3 rounded-xl bg-slate-900/95 dark:bg-black/90 text-white border border-rose-500/30 shadow-xl max-w-sm font-mono text-xs space-y-1 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-white/10 pb-1">
                <span className="text-slate-400 font-bold uppercase tracking-wider text-[11px]">
                  Epoch: {activePoint.month}
                </span>
                <span className="text-rose-400 font-bold">
                  {Math.round(activePoint.selected_integrated_risk * 100)}% ({activePoint.risk_band})
                </span>
              </div>
              <div className="text-[11px] text-slate-300">
                Dominant Risk Driver: <strong className="text-cyan-300">{activePoint.dominant_component}</strong>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 pt-1">
                <div>Sched Delay: {Math.round(activePoint.schedule_delay_risk * 100)}%</div>
                <div>Cost Overrun: {Math.round(activePoint.cost_overrun_risk * 100)}%</div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-8 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-dashed border-slate-300 dark:border-white/10 text-center space-y-2">
          <Activity className="w-8 h-8 text-slate-400 mx-auto" />
          <div className="font-mono text-sm font-semibold text-slate-700 dark:text-slate-300">
            Historical ML Risk Telemetry Ingestion in Progress
          </div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Longitudinal monthly risk scores are computed as quarterly telemetry epochs are ingested and cross-validated.
          </p>
        </div>
      )}
    </div>
  );
}
