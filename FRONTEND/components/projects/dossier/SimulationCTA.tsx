'use client';

import React from 'react';
import Link from 'next/link';
import { Play, Sparkles, ArrowRight } from 'lucide-react';

interface Props {
  projectId: string;
}

export function SimulationCTA({ projectId }: Props) {
  return (
    <div className="p-7 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-slate-900/60 to-cyan-950/40 border border-cyan-500/30 shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
      {/* Glow effect */}
      <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="space-y-2 relative z-10 max-w-2xl">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[11px] font-mono font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          Predictive Decision Sandbox
        </div>
        <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          Simulate Alternative Execution Scenarios
        </h3>
        <p className="text-xs sm:text-sm text-slate-300">
          Stress-test monthly capital outlay velocity, contractor cashflow disruptions, and supply-chain bottleneck shocks against PAIMANA&apos;s machine learning risk models.
        </p>
      </div>

      <div className="relative z-10 flex-shrink-0">
        <Link
          href={`/simulation?project=${encodeURIComponent(projectId)}`}
          className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-sm tracking-wide shadow-md shadow-cyan-500/20 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>RUN WHAT-IF SIMULATION</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
