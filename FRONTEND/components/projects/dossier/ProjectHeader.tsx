'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Building2, MapPin, ShieldAlert, CheckCircle2, Clock, Tag } from 'lucide-react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { getSectorFromAgency } from '@/lib/utils/sector';

interface Props {
  project: ProjectSearchRecord;
}

export function ProjectHeader({ project }: Props) {
  // Determine status badge
  let status: 'COMPLETED' | 'DELAYED' | 'ONGOING' = 'ONGOING';
  if (project.physical_progress_percent >= 100) {
    status = 'COMPLETED';
  } else if (project.has_revision || (project.schedule_delay_risk && project.schedule_delay_risk > 0.5)) {
    status = 'DELAYED';
  }

  const statusStyles = {
    COMPLETED: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
    DELAYED: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30',
    ONGOING: 'bg-sky-500/10 text-sky-600 dark:text-cyan-400 border-sky-500/30'
  };

  const statusIcons = {
    COMPLETED: <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />,
    DELAYED: <Clock className="w-3.5 h-3.5 mr-1.5" />,
    ONGOING: <ShieldAlert className="w-3.5 h-3.5 mr-1.5" />
  };

  const sector = getSectorFromAgency(project.agency, project.project_name);

  return (
    <div className="border-b border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-[#03090e]/60 backdrop-blur-md pb-8 pt-4">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back navigation */}
        <div className="mb-6">
          <Link
            href="/projects"
            className="inline-flex items-center gap-2 text-xs font-mono font-semibold tracking-wider text-slate-600 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors uppercase py-1 px-2.5 rounded-lg border border-slate-200 dark:border-white/10 hover:border-cyan-500/30 bg-white dark:bg-white/[0.02]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Projects
          </Link>
        </div>

        {/* Header Metadata */}
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          <div className="space-y-3 max-w-4xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-[11px] font-mono font-bold tracking-widest px-2.5 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20">
                PROJECT INTELLIGENCE
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-white/5 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-white/10">
                ID: {project.project_id}
              </span>
              {project.legacy_ocms_code && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-white/5 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-white/10">
                  OCMS: {project.legacy_ocms_code}
                </span>
              )}
              <span
                className={`inline-flex items-center text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${statusStyles[status]}`}
              >
                {statusIcons[status]}
                {status}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white leading-snug">
              {project.project_name}
            </h1>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-400 pt-1">
              <div className="flex items-center gap-1.5 font-medium">
                <Building2 className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <span>{project.agency}</span>
              </div>
              <span className="text-slate-300 dark:text-white/20">•</span>
              <div className="flex items-center gap-1.5 font-medium">
                <MapPin className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <span>{project.state}</span>
              </div>
              <span className="text-slate-300 dark:text-white/20">•</span>
              <div className="flex items-center gap-1.5 font-medium">
                <Tag className="w-3.5 h-3.5 text-cyan-500 flex-shrink-0" />
                <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/20 font-mono text-[11px] font-semibold">
                  {sector}
                </span>
              </div>
              {project.approval_start_date && (
                <>
                  <span className="text-slate-300 dark:text-white/20">•</span>
                  <div className="flex items-center gap-1.5 font-mono text-[11px]">
                    <span className="text-slate-400 dark:text-slate-500">Sanctioned:</span>
                    <span>{project.approval_start_date}</span>
                  </div>
                </>
              )}
            </div>
          </div>


          {/* Quick Action Badge */}
          <div className="flex items-center gap-3 self-start lg:self-center">
            <div className="p-3 rounded-xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 text-right">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Oversight Tier
              </div>
              <div className="text-sm font-bold font-mono text-cyan-600 dark:text-cyan-400">
                {project.risk_band === 'NOT_ASSESSED' ? 'STANDARD MONITORING' : `${project.risk_band} RISK PRIORITY`}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
