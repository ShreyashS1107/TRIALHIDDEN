'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Navbar from '@/components/layout/Navbar';
import ProjectSearchBar from '@/components/projects/ProjectSearchBar';
import ProjectFilters from '@/components/projects/ProjectFilters';
import ProjectCard from '@/components/projects/ProjectCard';
import ProjectTable from '@/components/projects/ProjectTable';
import { ProjectSearchRecord } from '@/lib/api/types';
import { Search, Database, AlertCircle, Shield, CheckCircle2, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { getSectorFromAgency, ALL_SECTORS } from '@/lib/utils/sector';

export default function ProjectsSearchPage() {
  const [projects, setProjects] = useState<ProjectSearchRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [displayCount, setDisplayCount] = useState(12);

  const [filters, setFilters] = useState({
    state: 'ALL',
    agency: 'ALL',
    sector: 'ALL',
    status: 'ALL',
    risk: 'ALL',
  });

  // Load search index
  useEffect(() => {
    fetch('/data/projects_search_index.json')
      .then((res) => res.json())
      .then((data: ProjectSearchRecord[]) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load projects search index:', err);
        setLoading(false);
      });
  }, []);

  // Compute unique filter options
  const availableStates = useMemo(() => {
    const set = new Set<string>();
    projects.forEach((p) => {
      if (p.state && p.state !== 'Central / Multi-State') set.add(p.state);
    });
    return Array.from(set).sort();
  }, [projects]);

  const availableAgencies = useMemo(() => {
    const set = new Set<string>();
    projects.forEach((p) => {
      if (p.agency) set.add(p.agency);
    });
    return Array.from(set).sort().slice(0, 40); // Top 40 clean agencies
  }, [projects]);

  // Autocomplete suggestions based on query
  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    return projects
      .filter((p) => {
        const sec = getSectorFromAgency(p.agency, p.project_name);
        return (
          p.project_id.toLowerCase().includes(q) ||
          p.legacy_ocms_code.toLowerCase().includes(q) ||
          p.project_name.toLowerCase().includes(q) ||
          p.agency.toLowerCase().includes(q) ||
          p.state.toLowerCase().includes(q) ||
          sec.toLowerCase().includes(q)
        );
      })
      .slice(0, 8);
  }, [projects, query]);

  // Filtered results
  const filteredProjects = useMemo(() => {
    const q = query.trim().toLowerCase();

    return projects.filter((p) => {
      // Search matching: project_id, legacy_ocms_code, project_name, agency, state, or sector
      if (q) {
        const matchesId = p.project_id.toLowerCase().includes(q);
        const matchesLegacy = p.legacy_ocms_code.toLowerCase().includes(q);
        const matchesName = p.project_name.toLowerCase().includes(q);
        const matchesAgency = p.agency.toLowerCase().includes(q);
        const matchesState = p.state.toLowerCase().includes(q);
        const sec = getSectorFromAgency(p.agency, p.project_name);
        const matchesSector = sec.toLowerCase().includes(q);
        if (!matchesId && !matchesLegacy && !matchesName && !matchesAgency && !matchesState && !matchesSector) return false;
      }

      // Sector filter
      if (filters.sector !== 'ALL') {
        const sec = getSectorFromAgency(p.agency, p.project_name);
        if (sec !== filters.sector) return false;
      }

      // State filter
      if (filters.state !== 'ALL' && p.state !== filters.state) return false;

      // Agency filter
      if (filters.agency !== 'ALL' && p.agency !== filters.agency) return false;

      // Risk level filter
      if (filters.risk !== 'ALL') {
        if (filters.risk === 'MEDIUM' && p.risk_band !== 'MEDIUM' && p.risk_band !== 'MODERATE') return false;
        if (filters.risk !== 'MEDIUM' && p.risk_band !== filters.risk) return false;
      }

      // Status / progress filter
      if (filters.status !== 'ALL') {
        if (filters.status === 'COMPLETED' && p.physical_progress_percent < 100) return false;
        if (filters.status === 'ADVANCED' && (p.physical_progress_percent < 75 || p.physical_progress_percent >= 100)) return false;
        if (filters.status === 'MIDWAY' && (p.physical_progress_percent < 25 || p.physical_progress_percent >= 75)) return false;
        if (filters.status === 'EARLY' && p.physical_progress_percent >= 25) return false;
      }

      return true;
    });
  }, [projects, query, filters]);

  // Visible page slice
  const visibleProjects = useMemo(() => {
    return filteredProjects.slice(0, displayCount);
  }, [filteredProjects, displayCount]);

  const handleSelectSuggestion = (project: ProjectSearchRecord) => {
    setQuery(project.project_id);
  };

  const handleResetFilters = () => {
    setFilters({
      state: 'ALL',
      agency: 'ALL',
      sector: 'ALL',
      status: 'ALL',
      risk: 'ALL',
    });
  };

  return (
    <main className="relative min-h-screen bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 overflow-x-hidden pt-28 pb-24">
      {/* Global Navbar */}
      <Navbar />

      {/* Subtle Government Geometric Grid Accent */}
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-cyan-500/10 via-transparent to-transparent pointer-events-none" />
      <div
        className="absolute top-20 inset-x-0 h-72 opacity-15 dark:opacity-20 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(rgba(57, 217, 255, 0.4) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Hero Header */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-700 dark:text-cyan-300 text-xs font-mono font-bold tracking-wider mb-4 shadow-sm">
            <Database className="w-3.5 h-3.5" />
            <span>NATIONAL INFRASTRUCTURE SURVEILLANCE REGISTER</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black text-slate-900 dark:text-white tracking-tight uppercase mb-4">
            PROJECT INTELLIGENCE
          </h1>

          <p className="text-sm sm:text-base text-slate-600 dark:text-concrete-300 leading-relaxed">
            Search a monitored infrastructure project to uncover its cost, schedule and predicted risk trajectory.
          </p>
        </div>

        {/* Search Bar with Autocomplete */}
        <div className="mb-10">
          <ProjectSearchBar
            query={query}
            onQueryChange={(newQ) => {
              setQuery(newQ);
              setDisplayCount(12); // reset display limit on new search
            }}
            suggestions={suggestions}
            onSelectSuggestion={handleSelectSuggestion}
          />

          {/* Quick Demo Pill Suggestions */}
          <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-xs font-mono text-slate-500 dark:text-concrete-400">
            <span className="text-[11px] uppercase tracking-wider font-semibold">Try searching:</span>
            {[
              { id: '612786', label: '612786 (Kadapa Airport)' },
              { id: '400178', label: '400178 (Western DFC)' },
              { id: '400244', label: '400244 (Bullet Train)' },
              { id: 'N04000106', label: 'N04000106 (Legacy Code)' },
              { id: 'Metro', label: 'Metro Rail' },
            ].map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => setQuery(tag.id)}
                className="px-2.5 py-1 rounded-lg bg-slate-200/70 hover:bg-slate-300 dark:bg-navy-900/80 dark:hover:bg-navy-800 border border-slate-300/60 dark:border-cyan-500/20 text-slate-700 dark:text-concrete-300 hover:text-cyan-600 dark:hover:text-cyan transition-colors"
              >
                {tag.label}
              </button>
            ))}
          </div>
        </div>

        {/* Non-dominant Filter Bar */}
        <ProjectFilters
          filters={filters}
          onFilterChange={(f) => {
            setFilters(f);
            setDisplayCount(12);
          }}
          onReset={handleResetFilters}
          availableStates={availableStates}
          availableAgencies={availableAgencies}
          availableSectors={ALL_SECTORS}
          totalResults={filteredProjects.length}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
        />

        {/* Results Container */}
        {loading ? (
          <div className="py-20 text-center">
            <div className="w-10 h-10 border-3 border-cyan border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-concrete-400">
              Loading national registry (2,741 infrastructure assets)...
            </p>
          </div>
        ) : filteredProjects.length === 0 ? (
          /* Empty State */
          <div className="max-w-xl mx-auto py-16 px-6 rounded-3xl glass-panel text-center border border-slate-200 dark:border-cyan-500/20 shadow-xl">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mx-auto mb-4 text-amber-600 dark:text-amber">
              <AlertCircle className="w-7 h-7" />
            </div>

            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              No project matched your search.
            </h3>

            <p className="text-xs sm:text-sm text-slate-600 dark:text-concrete-300 mb-6 leading-relaxed">
              We couldn’t find an infrastructure asset matching <strong className="text-slate-900 dark:text-white">&ldquo;{query}&rdquo;</strong>.
            </p>

            <div className="p-4 rounded-xl bg-slate-100 dark:bg-navy-900/80 border border-slate-200 dark:border-slate-800 text-left text-xs font-mono space-y-2 mb-6">
              <span className="font-bold text-slate-700 dark:text-concrete-300 block uppercase tracking-wider text-[10px]">
                SUGGESTED RECOVERY ACTIONS:
              </span>
              <div className="flex items-center gap-2 text-slate-600 dark:text-concrete-400">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-600 dark:bg-cyan shrink-0" />
                <span>Check project ID digits (e.g. <strong>612786</strong>, <strong>400178</strong>, <strong>105236</strong>)</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 dark:text-concrete-400">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-600 dark:bg-cyan shrink-0" />
                <span>Search by project name keywords (e.g. <strong>Airport</strong>, <strong>Highway</strong>, <strong>Rail</strong>)</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 dark:text-concrete-400">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-600 dark:bg-cyan shrink-0" />
                <span>Search by legacy OCMS alphanumeric code (e.g. <strong>N04000106</strong>)</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                setQuery('');
                handleResetFilters();
              }}
              className="px-5 py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-700 dark:text-cyan font-mono font-bold text-xs tracking-wider transition-colors"
            >
              Clear Search &amp; Show All Projects
            </button>
          </div>
        ) : viewMode === 'grid' ? (
          /* Cards Grid */
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {visibleProjects.map((project) => (
                <ProjectCard key={project.project_id} project={project} />
              ))}
            </div>

            {/* Load More Button */}
            {displayCount < filteredProjects.length && (
              <div className="text-center pt-4">
                <button
                  type="button"
                  onClick={() => setDisplayCount((prev) => prev + 12)}
                  className="px-6 py-3 rounded-xl bg-slate-200 hover:bg-slate-300 dark:bg-navy-900 dark:hover:bg-navy-800 border border-slate-300 dark:border-cyan-500/30 font-mono text-xs font-bold tracking-wider text-slate-800 dark:text-cyan transition-all shadow-sm hover:shadow-md"
                >
                  LOAD MORE ASSETS ({filteredProjects.length - displayCount} REMAINING)
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Table View */
          <div className="space-y-8">
            <ProjectTable projects={visibleProjects} />

            {displayCount < filteredProjects.length && (
              <div className="text-center pt-4">
                <button
                  type="button"
                  onClick={() => setDisplayCount((prev) => prev + 24)}
                  className="px-6 py-3 rounded-xl bg-slate-200 hover:bg-slate-300 dark:bg-navy-900 dark:hover:bg-navy-800 border border-slate-300 dark:border-cyan-500/30 font-mono text-xs font-bold tracking-wider text-slate-800 dark:text-cyan transition-all shadow-sm hover:shadow-md"
                >
                  LOAD MORE ASSETS ({filteredProjects.length - displayCount} REMAINING)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
