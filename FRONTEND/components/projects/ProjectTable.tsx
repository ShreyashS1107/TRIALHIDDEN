'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, ShieldAlert, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';

interface ProjectTableProps {
  projects: ProjectSearchRecord[];
}

export default function ProjectTable({ projects }: ProjectTableProps) {
  return (
    <div className="w-full max-w-6xl mx-auto overflow-hidden rounded-2xl glass-panel border border-slate-200 dark:border-cyan-500/20 shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-100/90 dark:bg-navy-950/90 font-mono text-[11px] uppercase tracking-wider text-slate-500 dark:text-concrete-400 border-b border-slate-200 dark:border-cyan-500/20">
            <tr>
              <th className="py-3.5 px-4">Project ID</th>
              <th className="py-3.5 px-4 min-w-[240px]">Project Name</th>
              <th className="py-3.5 px-4">Agency</th>
              <th className="py-3.5 px-4">State</th>
              <th className="py-3.5 px-4 text-right">Sanctioned</th>
              <th className="py-3.5 px-4 text-right">Revised</th>
              <th className="py-3.5 px-4 text-center">DOC</th>
              <th className="py-3.5 px-4 text-center">Progress</th>
              <th className="py-3.5 px-4 text-center">Risk</th>
              <th className="py-3.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800/60 font-mono">
            {projects.map((p) => {
              const isHigh = p.risk_band === 'HIGH' || p.risk_band === 'VERY_HIGH';
              const isMed = p.risk_band === 'MEDIUM' || p.risk_band === 'MODERATE';

              return (
                <tr
                  key={p.project_id}
                  className="hover:bg-cyan-500/5 dark:hover:bg-cyan-500/10 transition-colors group"
                >
                  <td className="py-3 px-4 font-bold text-cyan-700 dark:text-cyan whitespace-nowrap">
                    {p.project_id}
                  </td>
                  <td className="py-3 px-4 font-sans font-bold text-slate-900 dark:text-white line-clamp-1 max-w-[280px]">
                    <Link
                      href={`/projects/${p.project_id}`}
                      className="hover:text-cyan-600 dark:hover:text-cyan transition-colors"
                      title={p.project_name}
                    >
                      {p.project_name}
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-slate-600 dark:text-concrete-300 whitespace-nowrap">
                    {p.agency}
                  </td>
                  <td className="py-3 px-4 text-slate-600 dark:text-concrete-300 whitespace-nowrap">
                    {p.state}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-700 dark:text-concrete-300 whitespace-nowrap">
                    ₹{formatIndianNumber(p.original_cost_crore)} Cr
                  </td>
                  <td className="py-3 px-4 text-right font-bold whitespace-nowrap text-slate-900 dark:text-white">
                    ₹{formatIndianNumber(p.revised_cost_crore)} Cr
                  </td>
                  <td className="py-3 px-4 text-center text-slate-600 dark:text-concrete-300 whitespace-nowrap">
                    {p.revised_completion_date || p.original_completion_date || 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-center whitespace-nowrap font-bold text-slate-900 dark:text-white">
                    {Math.round(p.physical_progress_percent)}%
                  </td>
                  <td className="py-3 px-4 text-center whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        isHigh
                          ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400'
                          : isMed
                          ? 'bg-amber-500/15 text-amber-700 dark:text-amber-400'
                          : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'
                      }`}
                    >
                      {isHigh ? (
                        <ShieldAlert className="w-2.5 h-2.5" />
                      ) : isMed ? (
                        <AlertTriangle className="w-2.5 h-2.5" />
                      ) : (
                        <CheckCircle2 className="w-2.5 h-2.5" />
                      )}
                      {p.risk_band}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <Link
                      href={`/projects/${p.project_id}`}
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-600 dark:text-cyan hover:underline"
                    >
                      <span>Open Dossier</span>
                      <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
