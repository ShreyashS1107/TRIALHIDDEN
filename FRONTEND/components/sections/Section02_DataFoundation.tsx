'use client';

import React, { useState } from 'react';
import { Database, FileSpreadsheet, GitMerge, CheckCircle, ArrowDown, Cpu, ShieldCheck } from 'lucide-react';
import { NationalSummary } from '@/lib/api/types';

interface Section02Props {
  summary?: NationalSummary | null;
}

export default function Section02_DataFoundation({ summary }: Section02Props) {
  const [activeLayer, setActiveLayer] = useState<number | null>(null);

  const months = [
    { code: 'APR 2025', desc: 'FRApril2025.pdf • OCMS Legacy Format', count: '1,627 projects' },
    { code: 'MAY 2025', desc: 'FR_May2025.pdf • OCMS Legacy Format', count: '1,606 projects' },
    { code: 'JUN 2025', desc: 'FR_JUNE_2025.pdf • Transition Layout', count: '1,552 projects' },
    { code: 'JUL 2025', desc: 'FlashReport_July_2025.pdf • Early PAIMANA', count: '791 projects' },
    { code: 'AUG 2025', desc: 'FlashReport_August_2025.pdf • Standard Layout', count: '800 projects' },
    { code: 'SEP 2025', desc: 'FlashReport_September_2025.pdf • Table 6 Extracted', count: '794 projects' },
    { code: 'OCT 2025', desc: 'FlashReport_October_2025.pdf • Ongoing Register', count: '820 projects' },
    { code: 'NOV 2025', desc: 'FlashReport_November_2025.pdf • Nodal Submissions', count: '824 projects' },
    { code: 'DEC 2025', desc: 'FlashReport_December_2025.pdf • Mid-Year Audit', count: '1,388 projects' },
    { code: 'JAN 2026', desc: 'FlashReport_January_2026.pdf • New Year Epoch', count: '1,696 projects' },
    { code: 'FEB 2026', desc: 'FlashReport_February_2026.pdf • Pre-Budget Sync', count: '1,939 projects' },
    { code: 'MAR 2026', desc: 'FlashReport_March_2026.pdf • Q4 Milestone Close', count: '1,932 projects' },
    { code: 'APR 2026', desc: 'FlashReport_April2026.pdf • FY26-27 Intake', count: '1,862 projects' },
    { code: 'MAY 2026', desc: 'FlashReport_May2026.pdf • High-Fidelity Capture', count: '1,862 projects' },
    { code: 'JUN 2026', desc: 'FlashReport_June_2026.pdf • Consolidated Epoch', count: '1,862 projects' },
  ];

  const pipelineFlow = [
    { title: 'MONTHLY REPORTS', desc: '15 PDF Flash Reports published by MoSPI/IPMD', icon: FileSpreadsheet, color: 'text-slate-300' },
    { title: 'EXTRACTION', desc: 'Multi-layout PyMuPDF table parsing & regex headers', icon: Database, color: 'text-cyan' },
    { title: 'NORMALIZATION', desc: 'Canonical ID resolution & ISO-8601 timeline mapping', icon: GitMerge, color: 'text-teal' },
    { title: 'VALIDATION', desc: 'Progress bounding [0-100%] & 1,868 rows anomaly log', icon: ShieldCheck, color: 'text-amber' },
    { title: 'LONGITUDINAL DATA', desc: '21,555 immutable snapshots without future overwrite', icon: CheckCircle, color: 'text-healthy' },
    { title: 'INTELLIGENCE', desc: 'Dual-pillar predictive risk & prescriptive directives', icon: Cpu, color: 'text-cyan' },
  ];

  return (
    <section id="data-foundation" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20 overflow-hidden">
      {/* Background data particles */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,_rgba(57,217,255,0.04),_transparent_70%)] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-4">
            <Database className="w-3.5 h-3.5" />
            <span>SECTION 02 • LONGITUDINAL ARCHITECTURE</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            FROM MONTHLY REPORTS
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan to-teal">
              TO LONGITUDINAL INTELLIGENCE
            </span>
          </h2>
          <p className="text-sm sm:text-base text-concrete-300 leading-relaxed">
            Conventional systems overwrite monthly reports, erasing historical decay. PAIMANA preserves every monthly snapshot as an immutable point-in-time datum, assembling 15 continuous observation epochs into a unified longitudinal intelligence fabric.
          </p>
        </div>

        {/* 3 Large KPI Scale Counters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20 max-w-5xl mx-auto">
          <div className="glass-panel p-6 rounded-2xl border-cyan-500/30 text-center relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan to-transparent" />
            <span className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-mono text-white tracking-tight block mb-2 group-hover:scale-105 transition-transform">
              21,555
            </span>
            <span className="text-xs uppercase font-mono font-bold tracking-widest text-cyan block mb-1">
              PROJECT-MONTH RECORDS
            </span>
            <span className="text-xs text-concrete-400">
              Granular time-series records from 15 consecutive MoSPI Flash Reports
            </span>
          </div>

          <div className="glass-panel p-6 rounded-2xl border-teal-500/30 text-center relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-teal to-transparent" />
            <span className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-mono text-white tracking-tight block mb-2 group-hover:scale-105 transition-transform">
              2,741
            </span>
            <span className="text-xs uppercase font-mono font-bold tracking-widest text-teal block mb-1">
              UNIQUE PROJECTS
            </span>
            <span className="text-xs text-concrete-400">
              350 completed projects + 743 newly intake infrastructure assets tracked
            </span>
          </div>

          <div className="glass-panel p-6 rounded-2xl border-amber-500/30 text-center relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-amber to-transparent" />
            <span className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-mono text-white tracking-tight block mb-2 group-hover:scale-105 transition-transform">
              15
            </span>
            <span className="text-xs uppercase font-mono font-bold tracking-widest text-amber block mb-1">
              MONTHS OF COVERAGE
            </span>
            <span className="text-xs text-concrete-400">
              Unbroken temporal trajectory from April 2025 through June 2026
            </span>
          </div>
        </div>

        {/* 15 Monthly Data Layers Stacking Visualization */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center mb-20">
          <div className="lg:col-span-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan animate-pulse" />
                <span>15 MONTHLY DATA LAYERS</span>
              </h3>
              <span className="text-xs font-mono text-concrete-400">Hover epoch to inspect</span>
            </div>

            <div className="relative pl-4 space-y-2 border-l border-cyan-500/30">
              {months.map((m, idx) => (
                <div
                  key={m.code}
                  onMouseEnter={() => setActiveLayer(idx)}
                  className={`p-2.5 rounded-lg transition-all duration-200 cursor-pointer flex items-center justify-between ${
                    activeLayer === idx
                      ? 'bg-cyan-500/20 border border-cyan-500/50 translate-x-2 shadow-glow'
                      : 'bg-navy-850/60 hover:bg-navy-800/80 border border-concrete-700/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-bold text-cyan-300 w-20">
                      {m.code}
                    </span>
                    <span className="text-xs text-concrete-300 font-sans truncate max-w-[220px]">
                      {m.desc}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-concrete-400">
                    {m.count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Merging into Master Dataset Card */}
          <div className="lg:col-span-6">
            <div className="glass-panel p-8 rounded-2xl border-cyan-500/40 relative overflow-hidden shadow-2xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center">
                  <Database className="w-6 h-6 text-cyan" />
                </div>
                <div>
                  <h4 className="text-xl font-extrabold text-white">
                    PAIMANA MASTER DATASET
                  </h4>
                  <span className="text-xs font-mono text-cyan-300">
                    Canonical Schema • 1 Record per Project-Month
                  </span>
                </div>
              </div>

              <p className="text-xs sm:text-sm text-concrete-300 leading-relaxed mb-6">
                Every record is indexed by <code className="text-cyan font-mono font-semibold">project_id + report_month</code>. Bidirectional lookups resolve legacy 8-character OCMS codes into modern 6-digit PAIMANA identifiers while enforcing physical progress boundaries and financial traceability.
              </p>

              {/* Data Schema Badges */}
              <div className="space-y-3 font-mono text-xs">
                <div className="p-2.5 rounded-lg bg-navy-950/80 border border-cyan-500/20 flex items-center justify-between">
                  <span className="text-concrete-400">Canonical Identifiers:</span>
                  <span className="text-white font-semibold">project_id • legacy_ocms_code</span>
                </div>
                <div className="p-2.5 rounded-lg bg-navy-950/80 border border-cyan-500/20 flex items-center justify-between">
                  <span className="text-concrete-400">Financial Ledger:</span>
                  <span className="text-white font-semibold">original_cost • revised_cost • cumulative_exp</span>
                </div>
                <div className="p-2.5 rounded-lg bg-navy-950/80 border border-cyan-500/20 flex items-center justify-between">
                  <span className="text-concrete-400">Physical Milestone:</span>
                  <span className="text-white font-semibold">physical_progress_percent [0.0 - 100.0%]</span>
                </div>
                <div className="p-2.5 rounded-lg bg-navy-950/80 border border-cyan-500/20 flex items-center justify-between">
                  <span className="text-concrete-400">Traceability Guarantee:</span>
                  <span className="text-teal font-semibold">source_file • source_table • report_month</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Visual Pipeline Flow: Extraction -> Normalization -> Validation -> Longitudinal -> Intelligence */}
        <div>
          <div className="text-center mb-8">
            <span className="text-xs font-mono uppercase tracking-widest text-concrete-400">
              DATA INGESTION &amp; SURVEILLANCE PIPELINE
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
            {pipelineFlow.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.title}
                  className="glass-panel p-4 rounded-xl border-cyan-500/20 text-center relative group hover:border-cyan-500/40 transition-all"
                >
                  <div className="w-10 h-10 rounded-lg bg-navy-950 border border-cyan-500/30 mx-auto mb-3 flex items-center justify-center">
                    <Icon className={`w-5 h-5 ${step.color}`} />
                  </div>
                  <h5 className="text-xs font-bold font-mono text-white mb-1">
                    {step.title}
                  </h5>
                  <p className="text-[11px] text-concrete-400 font-sans leading-tight">
                    {step.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
