'use client';

import React, { useState } from 'react';
import { IndianRupee, TrendingUp, AlertCircle, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { ProjectDetail, NationalSummary } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';

interface Section05Props {
  summary?: NationalSummary | null;
  projects?: ProjectDetail[];
}

export default function Section05_CostIntelligence({ summary, projects = [] }: Section05Props) {
  const [selectedProjectId, setSelectedProjectId] = useState<string>('ALL');

  const activeProject = selectedProjectId === 'ALL'
    ? null
    : projects.find((p) => p.project_id === selectedProjectId);

  const sanctionedCr = activeProject
    ? activeProject.original_cost_crore
    : (summary?.dataset_scale.total_sanctioned_cost_crore || 4553276.37);

  const revisedCr = activeProject
    ? activeProject.revised_cost_crore
    : (summary?.dataset_scale.total_revised_cost_crore || 5363628.44);

  const spentCr = activeProject
    ? activeProject.cumulative_expenditure_crore
    : (summary?.dataset_scale.total_expenditure_crore || 3108849.01);

  const deltaCr = Math.max(0, revisedCr - sanctionedCr);
  const deltaPct = sanctionedCr > 0 ? (deltaCr / sanctionedCr) * 100 : 0;
  const isDivergent = deltaCr > 0;

  // Monthly Trajectory Curve Points
  const months = ['Apr 25', 'Jun 25', 'Aug 25', 'Oct 25', 'Dec 25', 'Feb 26', 'Apr 26', 'Jun 26'];
  const sanctionedPoints = [100, 100, 100, 100, 100, 100, 100, 100];
  const spentPoints = [54, 57, 60, 62, 65, 67, 68, 69];
  const revisedPoints = [100, 103, 106, 110, 114, 116, 117.8, 117.8];

  return (
    <section id="cost-intelligence" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>SECTION 05 • FINANCIAL DIVERGENCE SURVEILLANCE</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              SEE COST PRESSURE
              <span className="block text-amber">BEFORE IT BECOMES A CRISIS.</span>
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Real-time longitudinal audit tracking Sanctioned Outlays, Anticipated Cost Revisions, and Cumulative Outflows across all 21,555 infrastructure reporting cycles.
          </p>
        </div>

        {/* Portfolio vs Individual Project Selector */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          <button
            onClick={() => setSelectedProjectId('ALL')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap transition-all border ${
              selectedProjectId === 'ALL'
                ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                : 'bg-navy-900 border-concrete-700/50 text-concrete-400 hover:text-white'
            }`}
          >
            ★ COMPLETE NATIONAL PORTFOLIO (2,741 PROJECTS)
          </button>
          {projects.slice(0, 6).map((p) => (
            <button
              key={p.project_id}
              onClick={() => setSelectedProjectId(p.project_id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap transition-all border ${
                selectedProjectId === p.project_id
                  ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                  : 'bg-navy-900 border-concrete-700/50 text-concrete-400 hover:text-white'
              }`}
            >
              {p.project_id}: {p.project_name.slice(0, 20)}...
            </button>
          ))}
        </div>

        {/* 3 Core Financial KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Sanctioned */}
          <div className="glass-panel p-6 rounded-2xl border-cyan-500/30 relative">
            <span className="text-xs uppercase font-mono font-bold tracking-wider text-concrete-400 block mb-1">
              SANCTIONED OUTLAY
            </span>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-white mb-2">
              ₹{formatIndianNumber(sanctionedCr)} <span className="text-sm font-sans font-normal text-cyan">Cr</span>
            </div>
            <span className="text-xs text-concrete-400 font-sans">
              Cabinet Committee on Economic Affairs (CCEA) approved base allocation.
            </span>
          </div>

          {/* Revised */}
          <div className={`glass-panel p-6 rounded-2xl relative ${isDivergent ? 'glass-panel-amber border-amber-500/40 shadow-glow-amber' : 'border-cyan-500/30'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs uppercase font-mono font-bold tracking-wider text-amber block">
                REVISED ANTICIPATED COST
              </span>
              {isDivergent && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber border border-amber-500/40 font-bold">
                  +{deltaPct.toFixed(1)}% DIVERGENCE
                </span>
              )}
            </div>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-white mb-2">
              ₹{formatIndianNumber(revisedCr)} <span className="text-sm font-sans font-normal text-amber">Cr</span>
            </div>
            <span className="text-xs text-concrete-400 font-sans">
              Escalation incurred: <strong className="text-amber font-mono">+₹{formatIndianNumber(deltaCr)} Cr</strong> over baseline charter.
            </span>
          </div>

          {/* Cumulative Expenditure */}
          <div className="glass-panel p-6 rounded-2xl border-teal-500/30 relative">
            <span className="text-xs uppercase font-mono font-bold tracking-wider text-teal block mb-1">
              CUMULATIVE EXPENDITURE (SPENT)
            </span>
            <div className="text-3xl sm:text-4xl font-extrabold font-mono text-white mb-2">
              ₹{formatIndianNumber(spentCr)} <span className="text-sm font-sans font-normal text-teal">Cr</span>
            </div>
            <span className="text-xs text-concrete-400 font-sans">
              Disbursed outlays ({Math.round((spentCr / revisedCr) * 100)}% of anticipated budget utilized).
            </span>
          </div>
        </div>

        {/* Flowing Trajectory Visualization */}
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 relative">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-sm font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan animate-pulse" />
              <span>FLOWING FINANCIAL TRAJECTORY (APR 2025 – JUN 2026)</span>
            </h4>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-concrete-400">
                <span className="w-3 h-0.5 bg-cyan inline-block" /> Sanctioned (100% Base)
              </span>
              <span className="flex items-center gap-1.5 text-amber">
                <span className="w-3 h-0.5 bg-amber inline-block" /> Revised Anticipated
              </span>
              <span className="flex items-center gap-1.5 text-teal">
                <span className="w-3 h-0.5 bg-teal inline-block" /> Cumulative Spend
              </span>
            </div>
          </div>

          {/* SVG Flowing Wave Graph */}
          <div className="relative w-full h-56 sm:h-64">
            <svg className="w-full h-full" viewBox="0 0 800 200" preserveAspectRatio="none">
              <defs>
                <linearGradient id="amberDivergenceGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#F4B942" stopOpacity="0.35" />
                  <stop offset="100%" stopColor="#F4B942" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="tealSpendGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#27C7B8" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#27C7B8" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Horizontal Grid lines */}
              <line x1="0" y1="50" x2="800" y2="50" stroke="#0F2A38" strokeWidth="1" strokeDasharray="4 4" />
              <line x1="0" y1="100" x2="800" y2="100" stroke="#0F2A38" strokeWidth="1" />
              <line x1="0" y1="150" x2="800" y2="150" stroke="#0F2A38" strokeWidth="1" strokeDasharray="4 4" />

              {/* Amber Area Divergence between Sanctioned and Revised */}
              <path
                d="M 0,100 L 114,94 L 228,88 L 342,80 L 456,72 L 570,68 L 684,65 L 800,65 L 800,100 L 0,100 Z"
                fill="url(#amberDivergenceGrad)"
              />

              {/* Teal Area Under Spend */}
              <path
                d="M 0,146 L 114,143 L 228,140 L 342,138 L 456,135 L 570,133 L 684,132 L 800,131 L 800,200 L 0,200 Z"
                fill="url(#tealSpendGrad)"
              />

              {/* Sanctioned Baseline Line (Flat at 100) */}
              <line x1="0" y1="100" x2="800" y2="100" stroke="#39D9FF" strokeWidth="2" />

              {/* Revised Line (Rising to 65 in amber) */}
              <path
                d="M 0,100 Q 228,90 456,72 T 800,65"
                fill="none"
                stroke="#F4B942"
                strokeWidth="2.5"
              />

              {/* Spend Line (Rising smoothly in teal) */}
              <path
                d="M 0,146 Q 300,140 600,133 T 800,131"
                fill="none"
                stroke="#27C7B8"
                strokeWidth="2"
              />

              {/* Data points */}
              <circle cx="800" cy="65" r="4" fill="#F4B942" />
              <circle cx="800" cy="100" r="4" fill="#39D9FF" />
              <circle cx="800" cy="131" r="4" fill="#27C7B8" />
            </svg>

            {/* X-Axis labels */}
            <div className="flex justify-between text-[10px] font-mono text-concrete-500 pt-2 border-t border-concrete-800">
              {months.map((m) => (
                <span key={m}>{m}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
