'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/layout/Navbar';
import Section03_ProjectIntelligence from '@/components/sections/Section03_ProjectIntelligence';
import ProjectSearchNav from '@/components/navigation/ProjectSearchNav';
import { ProjectDetail } from '@/lib/api/types';
import { Database, Search, ArrowRight, ShieldCheck, IndianRupee, Clock, ChevronRight } from 'lucide-react';
import Link from 'next/link';

export default function ProjectDossierPage() {
  const [projects, setProjects] = useState<ProjectDetail[]>([]);
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null);

  useEffect(() => {
    fetch('/data/featured_projects.json')
      .then((res) => res.json())
      .then((data: ProjectDetail[]) => {
        setProjects(data);
        if (data.length > 0) setSelectedProject(data[0]);
      })
      .catch((err) => console.error('Error loading projects:', err));
  }, []);

  return (
    <main className="relative min-h-screen bg-navy-950 text-slate-100 overflow-x-hidden flex flex-col justify-between">
      <Navbar />

      {/* Hero Breadcrumb & Context Banner */}
      <div className="pt-28 pb-8 border-b border-cyan-500/20 bg-gradient-to-b from-navy-900 to-navy-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-4">
            <Database className="w-3.5 h-3.5" />
            <span>NATIONAL INFRASTRUCTURE SURVEILLANCE DOSSIER</span>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div>
              <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight uppercase">
                PROJECT DOSSIER
              </h1>
              <p className="mt-3 max-w-2xl text-sm sm:text-base text-concrete-300 leading-relaxed">
                Authoritative ground-truth project intelligence dossiers grounded in monthly MoSPI Flash Reports. Search across the complete national registry or select a monitored asset below.
              </p>
            </div>

            <Link
              href="/projects"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 text-navy-950 font-bold text-xs tracking-wider uppercase font-mono shadow-glow hover:scale-[1.02] transition-transform flex-shrink-0"
            >
              <Search className="w-4 h-4" />
              <span>SEARCH ALL 2,741 PROJECTS</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Prominent Search & Navigation Control */}
          <div className="mt-8 mb-4">
            <ProjectSearchNav
              placeholder="Search 2,741 projects to open dossier by ID, Name, Agency, State or Sector..."
              directNavigateToDossier={true}
            />
          </div>

          {/* Quick Direct Links to Key Monitored Projects */}
          <div className="mt-6 pt-6 border-t border-cyan-500/15">
            <div className="text-[11px] font-mono text-concrete-400 uppercase tracking-wider mb-3">
              Direct Access to Comprehensive Dynamic Dossiers:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
              {[
                { id: '612786', name: 'Kadapa Airport', agency: 'AAI', sector: 'Civil Aviation' },
                { id: '400178', name: 'Western DFC (Phase-II)', agency: 'DFCCIL', sector: 'Railways' },
                { id: '400244', name: 'Mumbai-Ahmedabad HSR', agency: 'NHSRCL', sector: 'Railways' },
                { id: '613768', name: 'Rishikesh-Karanprayag', agency: 'RVNL', sector: 'Railways' },
              ].map((proj) => (
                <Link
                  key={proj.id}
                  href={`/projects/${proj.id}`}
                  className="p-3 rounded-xl bg-navy-850 hover:bg-navy-800 border border-cyan-500/25 hover:border-cyan-400 transition-all flex items-center justify-between group"
                >
                  <div className="truncate">
                    <div className="text-white font-bold truncate group-hover:text-cyan transition-colors">
                      {proj.name}
                    </div>
                    <div className="text-[10px] text-concrete-400">
                      ID: {proj.id} • {proj.agency}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-cyan-500/50 group-hover:text-cyan group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-2" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Core Project Dossier Component */}
      <div className="flex-1">
        <Section03_ProjectIntelligence
          projects={projects}
          selectedProject={selectedProject}
          onSelectProject={(p: ProjectDetail) => setSelectedProject(p)}
        />
      </div>

      {/* Footer */}
      <footer className="border-t border-cyan-500/20 py-8 bg-navy-950 text-center text-xs font-mono text-concrete-400 space-y-1">
        <p>PAIMANA • Infrastructure Intelligence &amp; Surveillance Dossier • MoSPI IPMD Protocol</p>
        <p className="text-[11px] text-concrete-500">Authoritative Ground Truth • 15 Consecutive Audit Snapshots</p>
      </footer>
    </main>
  );
}
