import React from 'react';
import Navbar from '@/components/layout/Navbar';
import Section14_WhatIfSimulation from '@/components/sections/Section14_WhatIfSimulation';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

interface Props {
  searchParams?: {
    project?: string;
  };
}

export default function SimulationPage({ searchParams }: Props) {
  const projectId = searchParams?.project || '612786';

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-[#040d13] text-slate-900 dark:text-slate-100 flex flex-col justify-between">
      <Navbar />

      <main className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
          <Link
            href={`/projects/${encodeURIComponent(projectId)}`}
            className="inline-flex items-center gap-2 text-xs font-mono font-semibold tracking-wider text-slate-600 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors uppercase py-1 px-2.5 rounded-lg border border-slate-200 dark:border-white/10 hover:border-cyan-500/30 bg-white dark:bg-white/[0.02]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Project Intelligence ({projectId})
          </Link>
        </div>

        <Section14_WhatIfSimulation />
      </main>

      <footer className="border-t border-slate-200 dark:border-white/10 py-6 text-center text-xs font-mono text-slate-500">
        PAIMANA Infrastructure Intelligence • What-If Simulation Sandbox
      </footer>
    </div>
  );
}
