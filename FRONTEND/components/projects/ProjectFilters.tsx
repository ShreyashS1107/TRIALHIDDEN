'use client';

import React from 'react';
import { Filter, RotateCcw, LayoutGrid, List } from 'lucide-react';

interface FilterState {
  state: string;
  agency: string;
  sector: string;
  status: string;
  risk: string;
}

interface ProjectFiltersProps {
  filters: FilterState;
  onFilterChange: (newFilters: FilterState) => void;
  onReset: () => void;
  availableStates: string[];
  availableAgencies: string[];
  availableSectors: string[];
  totalResults: number;
  viewMode: 'grid' | 'table';
  onViewModeChange: (mode: 'grid' | 'table') => void;
}

export default function ProjectFilters({
  filters,
  onFilterChange,
  onReset,
  availableStates,
  availableAgencies,
  availableSectors,
  totalResults,
  viewMode,
  onViewModeChange,
}: ProjectFiltersProps) {
  const hasActiveFilters =
    filters.state !== 'ALL' ||
    filters.agency !== 'ALL' ||
    filters.sector !== 'ALL' ||
    filters.status !== 'ALL' ||
    filters.risk !== 'ALL';

  return (
    <div className="w-full max-w-6xl mx-auto mb-8">
      <div className="flex flex-wrap items-center justify-between gap-4 py-3 px-4 sm:px-6 rounded-2xl bg-white/70 dark:bg-navy-900/60 border border-slate-200 dark:border-cyan-500/20 backdrop-blur-md">
        {/* Left: Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-slate-500 dark:text-concrete-400 font-mono font-bold mr-1">
            <Filter className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan" />
            <span className="text-[11px] uppercase tracking-wider">FILTERS</span>
          </div>

          {/* Sector Filter */}
          <select
            value={filters.sector}
            onChange={(e) => onFilterChange({ ...filters, sector: e.target.value })}
            className="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-concrete-200 text-xs font-mono focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="ALL">Sector: All</option>
            {availableSectors.map((sec) => (
              <option key={sec} value={sec}>
                {sec}
              </option>
            ))}
          </select>

          {/* State Filter */}
          <select
            value={filters.state}
            onChange={(e) => onFilterChange({ ...filters, state: e.target.value })}
            className="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-concrete-200 text-xs font-mono focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="ALL">State: All</option>
            {availableStates.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          {/* Agency Filter */}
          <select
            value={filters.agency}
            onChange={(e) => onFilterChange({ ...filters, agency: e.target.value })}
            className="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-concrete-200 text-xs font-mono focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="ALL">Agency: All</option>
            {availableAgencies.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>

          {/* Risk Level Filter */}
          <select
            value={filters.risk}
            onChange={(e) => onFilterChange({ ...filters, risk: e.target.value })}
            className="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-concrete-200 text-xs font-mono focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="ALL">Risk: All</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium / Moderate</option>
            <option value="HIGH">High Risk</option>
            <option value="VERY_HIGH">Very High Risk</option>
          </select>

          {/* Project Status Filter */}
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            className="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-concrete-200 text-xs font-mono focus:outline-none focus:border-cyan-500 transition-colors"
          >
            <option value="ALL">Status: All</option>
            <option value="COMPLETED">Completed (100%)</option>
            <option value="ADVANCED">Advanced (&gt;75%)</option>
            <option value="MIDWAY">Midway (25% - 75%)</option>
            <option value="EARLY">Early Stage (&lt;25%)</option>
          </select>

          {/* Reset button */}
          {hasActiveFilters && (
            <button
              type="button"
              onClick={onReset}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>


        {/* Right: Results Count & View Toggle */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-500 dark:text-concrete-400">
            <strong className="text-slate-900 dark:text-white">{totalResults}</strong> projects
          </span>

          <div className="flex items-center p-0.5 rounded-lg bg-slate-100 dark:bg-navy-950 border border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={() => onViewModeChange('grid')}
              title="Grid Card View"
              className={`p-1.5 rounded-md transition-colors ${
                viewMode === 'grid'
                  ? 'bg-white dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan shadow-sm'
                  : 'text-slate-400 hover:text-slate-800 dark:text-concrete-400 dark:hover:text-white'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => onViewModeChange('table')}
              title="Compact Table View"
              className={`p-1.5 rounded-md transition-colors ${
                viewMode === 'table'
                  ? 'bg-white dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan shadow-sm'
                  : 'text-slate-400 hover:text-slate-800 dark:text-concrete-400 dark:hover:text-white'
              }`}
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
