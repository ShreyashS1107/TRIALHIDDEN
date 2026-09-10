'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/layout/Navbar';
import Section05_CostIntelligence from '@/components/sections/Section05_CostIntelligence';
import { ProjectDetail, NationalSummary } from '@/lib/api/types';
import { IndianRupee, TrendingUp, ArrowRight, ShieldCheck, Clock, FileText } from 'lucide-react';
import Link from 'next/link';

export default function CostIntelligencePage() {
  const [projects, setProjects] = useState<ProjectDetail[]>([]);
  const [summary, setSummary] = useState<NationalSummary | null>(null);

  useEffect(() => {
    fetch('/data/featured_projects.json')
      .then((res) => res.json())
      .then((data: ProjectDetail[]) => setProjects(data))
      .catch((err) => console.error('Error loading projects:', err));

    fetch('/data/paimana_summary.json')
      .then((res) => res.json())
      .then((data: NationalSummary) => setSummary(data))
      .catch((err) => console.error('Error loading summary:', err));
  }, []);

  return (
    <main className="relative min-h-screen bg-navy-950 text-slate-100 overflow-x-hidden flex flex-col justify-between">
      <Navbar />

      {/* Hero Breadcrumb & Context Banner */}
      <div className="pt-28 pb-8 border-b border-cyan-500/20 bg-gradient-to-b from-navy-900 to-navy-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-4">
            <IndianRupee className="w-3.5 h-3.5" />
            <span>EXPENDITURE & ESCALATION INTELLIGENCE</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight uppercase">
            COST INTELLIGENCE
          </h1>
          <p className="mt-3 max-w-2xl text-sm sm:text-base text-concrete-300 leading-relaxed">
            Continuous longitudinal tracking of Sanctioned Outlays, Anticipated Cost Revisions, and Cumulative Capital Outflows across India&apos;s monitored mega-infrastructure portfolio.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-6 text-xs font-mono">
            <Link
              href="/schedule-intelligence"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-850 hover:bg-navy-800 border border-cyan-500/30 text-cyan-300 transition-colors"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Schedule Intelligence</span>
              <ArrowRight className="w-3 h-3 ml-0.5" />
            </Link>

            <Link
              href="/project-dossier"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-850 hover:bg-navy-800 border border-cyan-500/30 text-cyan-300 transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Project Dossier</span>
              <ArrowRight className="w-3 h-3 ml-0.5" />
            </Link>

            <Link
              href="/custom-project"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/40 text-amber transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Assess Custom Project</span>
              <ArrowRight className="w-3 h-3 ml-0.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Core Cost Intelligence Component */}
      <div className="flex-1">
        <Section05_CostIntelligence summary={summary} projects={projects} />
      </div>

      {/* Footer */}
      <footer className="border-t border-cyan-500/20 py-8 bg-navy-950 text-center text-xs font-mono text-concrete-400 space-y-1">
        <p>PAIMANA • Cost Intelligence &amp; Capital Divergence Surveillance System • MoSPI IPMD Protocol</p>
        <p className="text-[11px] text-concrete-500">Longitudinal Financial Analysis • 21,555 Project Cycles Audited</p>
      </footer>
    </main>
  );
}
