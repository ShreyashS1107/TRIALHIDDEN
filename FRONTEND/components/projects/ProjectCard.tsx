'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, ShieldAlert, CheckCircle2, AlertTriangle, Calendar, Building2, MapPin, IndianRupee, Tag } from 'lucide-react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';
import { getSectorFromAgency } from '@/lib/utils/sector';

interface ProjectCardProps {
  project: ProjectSearchRecord;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  const isHighRisk = project.risk_band === 'HIGH' || project.risk_band === 'VERY_HIGH';
  const isMediumRisk = project.risk_band === 'MEDIUM' || project.risk_band === 'MODERATE';

  const riskBadgeStyles = isHighRisk
    ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30'
    : isMediumRisk
    ? 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30'
    : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30';

  const progressColor = isHighRisk
    ? 'bg-rose-500'
    : isMediumRisk
    ? 'bg-amber-500'
    : 'bg-gradient-to-r from-teal-500 to-cyan-500';

  const costEscalation = project.revised_cost_crore - project.original_cost_crore;
  const hasCostEscalation = costEscalation > 0.01;
  const sector = getSectorFromAgency(project.agency, project.project_name);

  return (
    <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between transition-all duration-200 hover:-translate-y-1 hover:border-cyan-500/40 dark:hover:border-cyan-500/40 hover:shadow-lg dark:hover:shadow-glow group">
      <div>
        {/* Header: Project ID & Risk Badge */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-concrete-400 font-bold">
              PROJECT ID
            </span>
            <span className="px-2.5 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-700 dark:text-cyan-300 font-mono font-bold text-xs tracking-wider">
              {project.project_id}
            </span>
            {project.legacy_ocms_code && (
              <span className="hidden sm:inline text-[10px] font-mono text-slate-400 dark:text-concrete-500">
                ({project.legacy_ocms_code})
              </span>
            )}
          </div>

          <div className={`px-2.5 py-0.5 rounded-full border text-[10px] font-mono font-bold uppercase tracking-wider flex items-center gap-1 ${riskBadgeStyles}`}>
            {isHighRisk ? (
              <ShieldAlert className="w-3 h-3" />
            ) : isMediumRisk ? (
              <AlertTriangle className="w-3 h-3" />
            ) : (
              <CheckCircle2 className="w-3 h-3" />
            )}
            <span>{project.risk_band} RISK</span>
          </div>
        </div>

        {/* Project Name */}
        <h3 className="text-base sm:text-lg font-extrabold text-slate-900 dark:text-white line-clamp-2 leading-snug mb-3 group-hover:text-cyan-600 dark:group-hover:text-cyan-300 transition-colors">
          {project.project_name}
        </h3>

        {/* Agency & State Metadata */}
        <div className="grid grid-cols-2 gap-2 text-xs mb-2">
          <div>
            <span className="text-[9px] font-mono uppercase tracking-wider text-slate-500 dark:text-concrete-400 block mb-0.5">
              AGENCY
            </span>
            <span className="font-semibold text-slate-800 dark:text-concrete-200 flex items-center gap-1 truncate" title={project.agency}>
              <Building2 className="w-3 h-3 text-cyan-600 dark:text-cyan shrink-0" />
              <span className="truncate">{project.agency}</span>
            </span>
          </div>

          <div>
            <span className="text-[9px] font-mono uppercase tracking-wider text-slate-500 dark:text-concrete-400 block mb-0.5">
              STATE
            </span>
            <span className="font-semibold text-slate-800 dark:text-concrete-200 flex items-center gap-1 truncate" title={project.state}>
              <MapPin className="w-3 h-3 text-teal-600 dark:text-teal shrink-0" />
              <span className="truncate">{project.state}</span>
            </span>
          </div>
        </div>

        {/* Sector Badge */}
        <div className="flex items-center gap-1.5 mb-3 pb-2.5 border-b border-slate-200/80 dark:border-slate-800 text-[11px] font-mono">
          <Tag className="w-3 h-3 text-cyan-500 shrink-0" />
          <span className="text-slate-500 dark:text-concrete-400 text-[10px] uppercase font-bold">SECTOR:</span>
          <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/20 font-semibold truncate">
            {sector}
          </span>
        </div>


        {/* Cost Comparison: Original -> Revised */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 dark:text-concrete-400 mb-1">
            <span className="uppercase">COST TRAJECTORY</span>
            {hasCostEscalation && (
              <span className="text-amber-600 dark:text-amber font-bold">
                +₹{formatIndianNumber(costEscalation)} Cr
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-600 dark:text-concrete-300">
              ₹{formatIndianNumber(project.original_cost_crore)} Cr
            </span>
            <ArrowRight className="w-3 h-3 text-slate-400" />
            <span className={`font-bold ${hasCostEscalation ? 'text-amber-700 dark:text-amber' : 'text-slate-900 dark:text-white'}`}>
              ₹{formatIndianNumber(project.revised_cost_crore)} Cr
            </span>
          </div>
        </div>

        {/* Schedule DOC: Original -> Revised */}
        <div className="mb-4">
          <span className="text-[10px] font-mono uppercase text-slate-500 dark:text-concrete-400 block mb-1">
            SCHEDULE (TARGET COMPLETION)
          </span>
          <div className="flex items-center gap-2 font-mono text-xs text-slate-700 dark:text-concrete-300">
            <Calendar className="w-3 h-3 text-cyan-600 dark:text-cyan shrink-0" />
            <span>{project.original_completion_date || 'N/A'}</span>
            {project.revised_completion_date && project.revised_completion_date !== project.original_completion_date && (
              <>
                <ArrowRight className="w-3 h-3 text-slate-400" />
                <span className="text-rose-600 dark:text-rose-400 font-bold">
                  {project.revised_completion_date}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-5">
          <div className="flex items-center justify-between text-[10px] font-mono mb-1">
            <span className="text-slate-500 dark:text-concrete-400 uppercase">PHYSICAL PROGRESS</span>
            <span className="font-bold text-slate-900 dark:text-white">
              {Math.round(project.physical_progress_percent)}%
            </span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-navy-950 h-2 rounded-full overflow-hidden p-0.5 border border-slate-300/60 dark:border-concrete-700/50">
            <div
              className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
              style={{ width: `${Math.min(100, Math.max(0, project.physical_progress_percent))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Action CTA */}
      <Link
        href={`/projects/${project.project_id}`}
        className="w-full py-2.5 px-4 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-700 dark:text-cyan font-mono font-bold text-xs tracking-wider flex items-center justify-center gap-2 transition-all group-hover:border-cyan-500/50 group-hover:shadow-sm"
      >
        <span>OPEN PROJECT DOSSIER</span>
        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
      </Link>
    </div>
  );
}
