'use client';

import React, { useState } from 'react';
import { AlertTriangle, TrendingDown, ArrowDownRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { AnomalyItem } from '@/lib/api/types';

interface Section13Props {
  anomalies?: AnomalyItem[];
}

export default function Section13_AnomalyDetection({ anomalies = [] }: Section13Props) {
  const anomalyCases = [
    {
      id: 'ANOM-01',
      title: 'Cumulative Expenditure Drop',
      project: 'Project 102000 (Akhnoor-Poonch Tunnel NH-144A)',
      epoch: '2026-01',
      type: 'EXPENDITURE_DROP',
      severity: 'HIGH',
      description: 'Cumulative spend dropped from ₹345.14 Cr (2025-06) to ₹0.00 Cr (2026-01) due to nodal contractor dispute reporting omission.',
      normalTrajectory: 'Steady capital absorption curve [300 Cr → 345 Cr → 380 Cr]',
      anomalyTrajectory: 'Sudden collapse [345 Cr ───────↘ ₹0 Cr]',
    },
    {
      id: 'ANOM-02',
      title: 'Physical Progress Regression',
      project: 'Project 400178 (Dinesh Makardhokra-III OCP)',
      epoch: '2025-08',
      type: 'PROGRESS_REGRESSION',
      severity: 'CRITICAL',
      description: 'Physical progress reported 42.1% previously, followed by non-monotonic regression or missing physical update while expenditure continued to disburse.',
      normalTrajectory: 'Expected continuous construction build [38% → 42% → 48%]',
      anomalyTrajectory: 'Progress stall & backward adjustment [42% ────↘ 0%]',
    },
    {
      id: 'ANOM-03',
      title: 'Massive Sudden Cost Revision',
      project: 'Project 060100093 (Gevra Expansion Coal Mining OCP)',
      epoch: '2025-04',
      type: 'COST_REVISION_JUMP',
      severity: 'MEDIUM',
      description: 'Anticipated cost escalated from original ₹11,816 Cr baseline with substantial multi-year schedule slippage debt.',
      normalTrajectory: 'Sanctioned baseline charter [₹11,816 Cr]',
      anomalyTrajectory: 'Anticipated budget divergence escalation [₹11,816 Cr ───────↗]',
    },
  ];

  const [activeTab, setActiveTab] = useState(0);
  const activeCase = anomalyCases[activeTab];

  return (
    <section id="anomaly-detection" className="relative w-full py-24 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-critical/10 border border-critical/30 text-xs font-mono text-critical mb-3">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>SECTION 13 • TRAJECTORY SANITY AUDIT</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              ANOMALY DETECTION
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Automated detection of illogical and suspicious reporting patterns: physical progress regressions, expenditure collapses, and sudden milestone leaps.
          </p>
        </div>

        {/* Anomaly Case Selector Tabs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {anomalyCases.map((c, idx) => (
            <button
              key={c.id}
              onClick={() => setActiveTab(idx)}
              className={`p-4 rounded-xl text-left transition-all border ${
                activeTab === idx
                  ? 'glass-panel-critical border-critical/50 shadow-glow-critical'
                  : 'glass-panel border-concrete-700/50 hover:border-cyan-500/40'
              }`}
            >
              <div className="flex items-center justify-between text-xs font-mono mb-2">
                <span className="text-critical font-bold">{c.id}</span>
                <span className="text-[10px] text-concrete-400">{c.epoch}</span>
              </div>
              <h4 className="text-sm font-bold text-white mb-1">{c.title}</h4>
              <span className="text-xs text-concrete-400 font-mono truncate block">
                {c.project}
              </span>
            </button>
          ))}
        </div>

        {/* Visual Trajectory Divergence Display Card */}
        <div className="glass-panel p-6 sm:p-10 rounded-2xl border-critical/40 relative">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-critical/20 mb-8">
            <div>
              <span className="text-xs font-mono text-critical uppercase tracking-widest font-bold">
                AUDITED ANOMALY EVENT: {activeCase.type}
              </span>
              <h3 className="text-2xl font-extrabold text-white mt-1">
                {activeCase.title}
              </h3>
              <p className="text-xs text-concrete-400 font-mono mt-1">
                {activeCase.project} • Epoch: {activeCase.epoch}
              </p>
            </div>

            {/* Warning Callout Box */}
            <div className="px-4 py-2 rounded-xl bg-critical/20 border border-critical/50 text-right">
              <span className="text-xs font-mono font-bold text-critical block animate-pulse">
                ANOMALY DETECTED
              </span>
              <span className="text-[10px] font-mono text-white tracking-wider">
                REQUIRES DOMAIN REVIEW
              </span>
            </div>
          </div>

          <p className="text-sm text-concrete-300 leading-relaxed mb-8 max-w-3xl">
            {activeCase.description}
          </p>

          {/* Graphical Trajectory Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Normal Trajectory Curve */}
            <div className="glass-panel p-5 rounded-xl border-cyan-500/20 space-y-2">
              <span className="text-[10px] font-mono text-concrete-400 uppercase block font-bold">
                Expected Normal Trajectory (Monotonic Growth)
              </span>
              <div className="font-mono text-sm text-cyan font-bold py-2">
                ───────────────↗
              </div>
              <p className="text-xs text-concrete-300">
                {activeCase.normalTrajectory}
              </p>
            </div>

            {/* Anomalous Trajectory Curve */}
            <div className="glass-panel-critical p-5 rounded-xl border-critical/40 space-y-2">
              <span className="text-[10px] font-mono text-critical uppercase block font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                Detected Anomalous Curve (Regression / Collapse)
              </span>
              <div className="font-mono text-sm text-critical font-bold py-2 animate-pulse">
                ───────────↗ ↘ (Abrupt Drop)
              </div>
              <p className="text-xs text-concrete-300">
                {activeCase.anomalyTrajectory}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
