'use client';

import React from 'react';
import { ShieldCheck, CheckCircle2, FileCode, Database, Search, Lock } from 'lucide-react';
import { NationalSummary } from '@/lib/api/types';

interface Section12Props {
  summary?: NationalSummary | null;
}

export default function Section12_DataTrust({ summary }: Section12Props) {
  const trustDimensions = [
    {
      title: 'KEY UNIQUENESS',
      rule: 'Composite Primary Key (project_id + report_month)',
      guarantee: 'Zero duplicate snapshots allowed across all 21,555 longitudinal rows.',
      status: '100% ENFORCED',
    },
    {
      title: 'VALUE BOUNDS',
      rule: 'Physical Progress strictly [0.00% to 100.00%]',
      guarantee: 'Progress bounded as non-negative percentage; invalid characters and sentinels purged.',
      status: '100% ENFORCED',
    },
    {
      title: 'TRAJECTORY AUDIT',
      rule: 'Monotonic Expenditure & Progress Tracking',
      guarantee: 'Detects artificial regressions and reporting skips for administrative inquiry.',
      status: 'AUDIT ACTIVE',
    },
    {
      title: 'COST CONSISTENCY',
      rule: 'Original Cost > 0 & Revised Cost ≥ Cumulative Spend',
      guarantee: 'Disallows illogical capital states before feature generation pipelines.',
      status: 'VERIFIED',
    },
    {
      title: 'SOURCE TRACEABILITY',
      rule: 'Every row links to source_file, source_table & report_month',
      guarantee: 'Judicial audit trail back to original MoSPI Flash Report PDF and page bounds.',
      status: 'AUDIT PROVEN',
    },
  ];

  return (
    <section id="data-trust" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-4">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>SECTION 12 • GOVERNANCE & DATA INTEGRITY</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            DATA TRUST LAYER
          </h2>
          <p className="text-sm sm:text-base text-concrete-300 leading-relaxed">
            PAIMANA never feeds raw, dirty data into machine learning models. Every record is rigorously screened against a mathematical validation policy that isolates and logs anomalies without corrupting inference features.
          </p>
        </div>

        {/* The Longitudinal Record Structure Equation */}
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 text-center max-w-4xl mx-auto mb-16 shadow-glow">
          <span className="text-xs font-mono uppercase tracking-widest text-concrete-400 block mb-4">
            LONGITUDINAL POINT-IN-TIME MATHEMATICAL ARCHITECTURE
          </span>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 text-lg sm:text-xl font-mono font-extrabold text-white">
            <div className="px-4 py-2 rounded-xl bg-navy-950 border border-cyan-500/40 text-cyan">
              PROJECT IDENTITY
            </div>
            <span className="text-cyan text-2xl">+</span>
            <div className="px-4 py-2 rounded-xl bg-navy-950 border border-teal-500/40 text-teal">
              REPORT MONTH (EPOCH)
            </div>
            <span className="text-cyan text-2xl">=</span>
            <div className="px-4 py-2 rounded-xl bg-cyan text-navy-950 shadow-glow">
              TRACEABLE SNAPSHOT
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 mt-6 text-xs font-mono text-concrete-300 pt-4 border-t border-concrete-800">
            <span>• source_file: <strong className="text-white">FlashReport_April2026.pdf</strong></span>
            <span>• source_table: <strong className="text-white">Table 6: All Ongoing Projects</strong></span>
            <span>• status: <strong className="text-healthy">VERIFIED POINT-IN-TIME RECORD</strong></span>
          </div>
        </div>

        {/* 5 Data Trust Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {trustDimensions.map((dim) => (
            <div
              key={dim.title}
              className="glass-panel p-6 rounded-2xl border-cyan-500/20 flex flex-col justify-between hover:border-cyan-500/40 transition-all"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    {dim.title}
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-healthy-500/20 text-healthy border border-healthy/40 font-bold">
                    {dim.status}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-navy-950/80 border border-concrete-800 text-xs font-mono text-cyan-300 mb-3">
                  {dim.rule}
                </div>
                <p className="text-xs text-concrete-300 leading-relaxed">
                  {dim.guarantee}
                </p>
              </div>
              <div className="pt-4 border-t border-concrete-800 mt-4 flex items-center gap-1.5 text-[11px] text-concrete-400 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-healthy" />
                <span>Audited under 1,868 rows policy</span>
              </div>
            </div>
          ))}

          {/* Anomaly Log Summary Card */}
          <div className="glass-panel p-6 rounded-2xl border-amber-500/30 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-amber">
                  ANOMALY SURVEILLANCE LOG
                </h4>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber border border-amber-500/40 font-bold">
                  1,868 ROWS LOGGED
                </span>
              </div>
              <p className="text-xs text-concrete-300 leading-relaxed mb-3">
                Suspect reporting entries (e.g. expenditure drops or progress regression) are flagged for human domain verification, preventing synthetic errors from corrupting downstream inference.
              </p>
            </div>
            <div className="pt-4 border-t border-amber-500/20 text-xs font-mono text-amber">
              Zero synthetic hallucinations permitted.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
