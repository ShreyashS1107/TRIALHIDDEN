'use client';

import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, ShieldAlert, CheckCircle, Info, Filter, ArrowUpRight } from 'lucide-react';
import { SystemAlert } from '@/lib/api/types';

interface Section08Props {
  alerts?: SystemAlert[];
  onSelectProjectId?: (id: string) => void;
}

export default function Section08_EarlyWarningCenter({ alerts = [], onSelectProjectId }: Section08Props) {
  const [filterSource, setFilterSource] = useState<string>('ALL');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');

  const filteredAlerts = alerts.filter((a) => {
    if (filterSource !== 'ALL' && a.source !== filterSource) return false;
    if (filterSeverity !== 'ALL' && a.severity !== filterSeverity) return false;
    return true;
  });

  return (
    <section id="early-warning" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-xs font-mono text-amber mb-3">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>SECTION 08 • TRI-SOURCE SURVEILLANCE FEED</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              EARLY WARNING CENTER
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            Tri-source alert registry aggregating calibrated predictive outcomes, operational execution friction, and data quality anomaly flags from the 1,868 rows audit.
          </p>
        </div>

        {/* Filter Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8 bg-navy-950 p-4 rounded-xl border border-cyan-500/20">
          {/* Source Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar text-xs font-mono">
            {['ALL', 'PREDICTIVE_ML', 'EXECUTION_SURVEILLANCE', 'RULE_ENGINE'].map((src) => (
              <button
                key={src}
                onClick={() => setFilterSource(src)}
                className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all border ${
                  filterSource === src
                    ? 'bg-cyan-500/20 border-cyan text-white shadow-glow'
                    : 'border-transparent text-concrete-400 hover:text-white'
                }`}
              >
                {src.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Severity Dropdown / Buttons */}
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-concrete-400 hidden sm:inline">Severity:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-bold uppercase transition-all ${
                  filterSeverity === sev
                    ? 'bg-white/10 text-white border border-white/30'
                    : 'text-concrete-400 hover:text-concrete-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* Warning Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAlerts.slice(0, 9).map((alert) => {
            const isCritical = alert.severity === 'CRITICAL';
            const isHigh = alert.severity === 'HIGH';
            const isMedium = alert.severity === 'MEDIUM';

            const cardBorder = isCritical
              ? 'border-critical/50 shadow-glow-critical'
              : isHigh
              ? 'border-amber/50 shadow-glow-amber'
              : 'border-cyan-500/30';

            const badgeBg = isCritical
              ? 'bg-critical/20 text-critical border-critical/40'
              : isHigh
              ? 'bg-amber/20 text-amber border-amber/40'
              : 'bg-cyan-500/20 text-cyan border-cyan-500/40';

            return (
              <div
                key={alert.id}
                className={`glass-panel p-6 rounded-2xl border ${cardBorder} flex flex-col justify-between transition-all hover:-translate-y-1`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase border ${badgeBg}`}>
                      {alert.severity} • {alert.source.replace('_', ' ')}
                    </span>
                    <span className="text-[11px] font-mono text-concrete-400">
                      {alert.timestamp}
                    </span>
                  </div>

                  <span className="text-xs font-mono font-bold text-cyan-300 block mb-1">
                    ID: {alert.project_id}
                  </span>

                  <h4 className="text-sm font-extrabold text-white line-clamp-2 mb-3">
                    {alert.project_name}
                  </h4>

                  <div className="p-3 rounded-lg bg-navy-950/80 border border-concrete-800 text-xs text-concrete-300 mb-4 font-sans leading-relaxed">
                    {alert.condition}
                  </div>
                </div>

                <div className="pt-3 border-t border-concrete-800/80 space-y-2">
                  <div className="text-[11px]">
                    <span className="text-concrete-400 font-mono text-[9px] uppercase block">
                      Recommended Attention
                    </span>
                    <span className="text-white font-medium">
                      {alert.recommended_action}
                    </span>
                  </div>

                  {onSelectProjectId && (
                    <button
                      onClick={() => onSelectProjectId(alert.project_id)}
                      className="text-[11px] font-mono text-cyan flex items-center gap-1 hover:underline pt-1 font-semibold"
                    >
                      <span>Examine in Project Dossier</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
