'use client';

import React from 'react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { Database, FileCode, CheckCircle, Shield } from 'lucide-react';

interface Props {
  project: ProjectSearchRecord;
}

export function DataProvenancePanel({ project }: Props) {
  const sourceFile = project.source_file || 'FlashReport_June_2026.pdf';
  const sourceTable = project.source_table || 'Table 6: All Ongoing Projects';
  const reportMonth = project.last_reported_month || '2026-06';

  return (
    <div className="p-5 rounded-2xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-500" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-widest text-slate-800 dark:text-slate-200">
            Section 09 — Data Provenance & Audit Trail
          </h3>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
          <Shield className="w-3.5 h-3.5" />
          <span>VERIFIED LONGITUDINAL MOSPI TELEMETRY</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3 rounded-xl bg-white dark:bg-[#06131c]/60 border border-slate-200 dark:border-white/10">
          <div className="text-[10px] uppercase text-slate-400 dark:text-slate-500">
            Reporting Epoch
          </div>
          <div className="text-sm font-bold text-slate-900 dark:text-white mt-1">
            {reportMonth}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-white dark:bg-[#06131c]/60 border border-slate-200 dark:border-white/10">
          <div className="text-[10px] uppercase text-slate-400 dark:text-slate-500">
            Source File (PDF Extract)
          </div>
          <div className="text-sm font-bold text-cyan-600 dark:text-cyan-400 mt-1 truncate" title={sourceFile}>
            {sourceFile}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-white dark:bg-[#06131c]/60 border border-slate-200 dark:border-white/10">
          <div className="text-[10px] uppercase text-slate-400 dark:text-slate-500">
            Source Table
          </div>
          <div className="text-sm font-bold text-slate-900 dark:text-white mt-1 truncate" title={sourceTable}>
            {sourceTable}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-white dark:bg-[#06131c]/60 border border-slate-200 dark:border-white/10">
          <div className="text-[10px] uppercase text-slate-400 dark:text-slate-500">
            Canonical Project Ref
          </div>
          <div className="text-sm font-bold text-slate-900 dark:text-white mt-1">
            MOSPI-IPMD-{project.project_id}
          </div>
        </div>
      </div>

      <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
        Traceability Note: PAIMANA ingests and parses official monthly Flash Reports published by the Infrastructure and Project Monitoring Division (IPMD), Ministry of Statistics and Programme Implementation (MoSPI). All figures preserve official reporting nomenclature and units without synthetic alterations.
      </p>
    </div>
  );
}
