'use client';

import React, { useState } from 'react';
import { Calendar, Clock, AlertTriangle, CheckCircle, ArrowRight, ShieldAlert } from 'lucide-react';
import { ProjectDetail } from '@/lib/api/types';

interface Section06Props {
  projects?: ProjectDetail[];
}

export default function Section06_ScheduleIntelligence({ projects = [] }: Section06Props) {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const defaultProj: any = {
    project_id: '400178',
    project_name: 'Western Dedicated Freight Corridor (Phase-II)',
    agency_name: 'DFCCIL',
    state: 'Gujarat / Maharashtra',
    sector: 'Railways',
    approval_start_date: '2020-03',
    original_completion_date: '2024-03',
    revised_completion_date: '2025-12',
    execution_profile: {
      schedule_slippage_months: 21,
      total_cumulative_expenditure_cr: 42100,
      latest_revised_cost_cr: 51200,
      sanctioned_cost_cr: 38500
    }
  };
  const activeProj = projects[selectedIdx] || projects[0] || defaultProj;

  const approvalDate = activeProj.approval_start_date || '2021-06';
  const originalDoc = activeProj.original_completion_date || '2024-03';
  const revisedDoc = activeProj.revised_completion_date || activeProj.original_completion_date;
  
  const hasDelay = revisedDoc !== originalDoc;
  const slippageMonths = activeProj.execution_profile.schedule_slippage_months || (hasDelay ? 14 : 0);

  const timelineMilestones = [
    {
      label: 'APPROVAL & SANCTION',
      date: approvalDate,
      status: 'completed',
      desc: 'Cabinet approval & initial budgetary outlay chartered.',
      color: 'border-cyan text-cyan',
    },
    {
      label: 'PLANNED COMPLETION (DOC)',
      date: originalDoc,
      status: 'target',
      desc: 'Target commissioning milestone stipulated in contract.',
      color: 'border-slate-400 text-slate-200',
    },
    {
      label: 'REVISED COMPLETION',
      date: revisedDoc,
      status: hasDelay ? 'delayed' : 'on_track',
      desc: hasDelay ? `Anticipated commissioning extended (+${slippageMonths.toFixed(0)} months slip).` : 'On-schedule commissioning targets intact.',
      color: hasDelay ? 'border-amber text-amber' : 'border-healthy text-healthy',
    },
    {
      label: 'CURRENT TRAJECTORY',
      date: '2026-03 (Epoch)',
      status: hasDelay ? 'pressure' : 'stable',
      desc: hasDelay ? 'Schedule pressure detected by Platt-calibrated RF_02 model.' : 'Executing within operational baseline bounds.',
      color: hasDelay ? 'border-amber text-amber' : 'border-cyan text-cyan',
    },
  ];

  return (
    <section id="schedule-intelligence" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <Clock className="w-3.5 h-3.5" />
              <span>SECTION 06 • TEMPORAL SLIPPAGE AUDIT</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              SCHEDULE INTELLIGENCE
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Temporal milestone tracking identifying schedule slippage debt, critical path delays, and baseline completion extensions before formal covenant default.
          </p>
        </div>

        {/* Project Selector Mini Bar */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 no-scrollbar">
          {projects.slice(0, 6).map((p, idx) => (
            <button
              key={p.project_id}
              onClick={() => setSelectedIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap transition-all border ${
                selectedIdx === idx
                  ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                  : 'bg-navy-950 border-concrete-700/50 text-concrete-400 hover:text-white'
              }`}
            >
              {p.project_id}: {p.project_name.slice(0, 22)}...
            </button>
          ))}
        </div>

        {/* Timeline Visual Container */}
        <div className="glass-panel p-6 sm:p-10 rounded-2xl border-cyan-500/30 relative">
          <div className="flex items-center justify-between pb-6 border-b border-cyan-500/20 mb-10">
            <div>
              <span className="text-xs font-mono text-cyan-300">
                Project ID: {activeProj.project_id} • {activeProj.agency}
              </span>
              <h3 className="text-xl font-bold text-white mt-1">
                {activeProj.project_name}
              </h3>
            </div>

            {hasDelay ? (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber text-xs font-mono font-bold">
                <AlertTriangle className="w-4 h-4 animate-pulse" />
                <span>SCHEDULE PRESSURE: +{slippageMonths.toFixed(0)} MONTHS</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-healthy-500/15 border border-healthy/40 text-healthy text-xs font-mono font-bold">
                <CheckCircle className="w-4 h-4" />
                <span>ON-SCHEDULE TRAJECTORY</span>
              </div>
            )}
          </div>

          {/* Stepper Timeline Visual */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            {timelineMilestones.map((m, idx) => (
              <div key={m.label} className="relative space-y-3">
                {/* Step Connector Line */}
                {idx < timelineMilestones.length - 1 && (
                  <div className="hidden lg:block absolute top-5 left-10 right-0 h-0.5 bg-gradient-to-r from-cyan-500/40 to-cyan-500/10 z-0" />
                )}

                {/* Badge Number */}
                <div className="flex items-center gap-3 relative z-10">
                  <div
                    className={`w-10 h-10 rounded-xl bg-navy-950 border-2 flex items-center justify-center font-mono font-bold text-sm ${m.color} shadow-glow`}
                  >
                    0{idx + 1}
                  </div>
                  <span className="text-xs font-mono text-concrete-400 font-semibold">
                    {m.date}
                  </span>
                </div>

                <div className="glass-panel p-4 rounded-xl border-concrete-700/50 space-y-1">
                  <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                    {m.label}
                  </h4>
                  <p className="text-[11px] text-concrete-300 font-sans leading-relaxed">
                    {m.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Slippage Callout Footer */}
          {hasDelay && (
            <div className="mt-10 p-4 rounded-xl bg-navy-950/80 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
              <div className="flex items-center gap-2 text-amber">
                <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                <span>
                  Critical path slippage exceeds 12-month covenant threshold. Automated review directive assigned.
                </span>
              </div>
              <span className="text-concrete-400 text-right">
                Directive: <code className="text-amber">{activeProj.execution_profile?.suggested_action?.directive || 'FIELD_AUDIT_RECOMMENDED'}</code>
              </span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
