'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Search, X, ChevronRight, Building2, MapPin } from 'lucide-react';
import { ProjectSearchRecord } from '@/lib/api/types';

interface ProjectSearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  suggestions: ProjectSearchRecord[];
  onSelectSuggestion: (project: ProjectSearchRecord) => void;
}

export default function ProjectSearchBar({
  query,
  onQueryChange,
  suggestions,
  onSelectSuggestion,
}: ProjectSearchBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onQueryChange(e.target.value);
    setIsOpen(true);
  };

  const handleSelect = (p: ProjectSearchRecord) => {
    onSelectSuggestion(p);
    setIsOpen(false);
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-3xl mx-auto">
      {/* Search Input Box */}
      <div className="relative flex items-center">
        <div className="absolute left-4 sm:left-5 text-cyan-600 dark:text-cyan pointer-events-none">
          <Search className="w-5 h-5 sm:w-6 sm:h-6" />
        </div>

        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          placeholder="Enter Project ID or project code (e.g., 612786, N04000106, Kadapa)"
          className="w-full pl-12 sm:pl-14 pr-12 py-4 sm:py-4.5 rounded-2xl bg-white/90 dark:bg-navy-900/90 border-2 border-slate-200 dark:border-cyan-500/30 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-concrete-500 text-sm sm:text-base font-medium shadow-lg dark:shadow-glow focus:outline-none focus:border-cyan-500 transition-all backdrop-blur-xl"
        />

        {query && (
          <button
            type="button"
            onClick={() => {
              onQueryChange('');
              setIsOpen(false);
            }}
            className="absolute right-4 p-1 rounded-full text-slate-400 hover:text-slate-700 dark:text-concrete-400 dark:hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Autocomplete Suggestions Dropdown */}
      {isOpen && query.trim().length > 0 && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 rounded-2xl bg-white/95 dark:bg-navy-950/95 border border-slate-200 dark:border-cyan-500/30 shadow-2xl backdrop-blur-2xl overflow-hidden max-h-96 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60">
          <div className="px-4 py-2 bg-slate-50 dark:bg-navy-900/80 text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-concrete-400 flex items-center justify-between">
            <span>SUGGESTED INFRASTRUCTURE ASSETS</span>
            <span>{suggestions.length} MATCHES</span>
          </div>

          {suggestions.slice(0, 6).map((p) => (
            <button
              key={p.project_id}
              type="button"
              onClick={() => handleSelect(p)}
              className="w-full px-4 py-3 text-left hover:bg-cyan-500/10 transition-colors flex items-center justify-between gap-3 group"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-xs font-bold text-cyan-700 dark:text-cyan px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                    ID: {p.project_id}
                  </span>
                  {p.legacy_ocms_code && (
                    <span className="text-[11px] font-mono text-slate-500 dark:text-concrete-400">
                      • {p.legacy_ocms_code}
                    </span>
                  )}
                  <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                    p.risk_band === 'HIGH' || p.risk_band === 'VERY_HIGH'
                      ? 'text-rose-600 bg-rose-500/10'
                      : p.risk_band === 'MEDIUM' || p.risk_band === 'MODERATE'
                      ? 'text-amber-600 bg-amber-500/10'
                      : 'text-emerald-600 bg-emerald-500/10'
                  }`}>
                    {p.risk_band}
                  </span>
                </div>

                <div className="text-sm font-bold text-slate-900 dark:text-white truncate group-hover:text-cyan-600 dark:group-hover:text-cyan-300">
                  {p.project_name}
                </div>

                <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-concrete-400 mt-1 font-mono">
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3 text-cyan-600 dark:text-cyan" />
                    {p.agency}
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-teal-600 dark:text-teal" />
                    {p.state}
                  </span>
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-cyan-600 dark:group-hover:text-cyan group-hover:translate-x-1 transition-all shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
