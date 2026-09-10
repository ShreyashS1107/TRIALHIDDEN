import React, { useState, useEffect, useRef } from 'react';
import { Search, X, ChevronRight, Building2, MapPin, Layers, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { ProjectSearchRecord } from '@/lib/api/types';
import { getSectorFromAgency } from '@/lib/utils/sector';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface ProjectSearchNavProps {
  placeholder?: string;
  selectedProjectId?: string;
  onSelectProject?: (project: ProjectSearchRecord) => void;
  directNavigateToDossier?: boolean;
  contextBadge?: string;
}

export default function ProjectSearchNav({
  placeholder = 'Search 2,741 projects by ID, name, agency, state or sector...',
  selectedProjectId,
  onSelectProject,
  directNavigateToDossier = false,
  contextBadge = 'PROJECT SEARCH & SURVEILLANCE'
}: ProjectSearchNavProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [index, setIndex] = useState<ProjectSearchRecord[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<ProjectSearchRecord | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/data/projects_search_index.json')
      .then((res) => res.json())
      .then((data: ProjectSearchRecord[]) => {
        setIndex(data);
        if (selectedProjectId && selectedProjectId !== 'ALL') {
          const match = data.find((p) => p.project_id === selectedProjectId);
          if (match) setSelectedRecord(match);
        }
      })
      .catch((err) => console.error('Failed to load search index:', err));
  }, [selectedProjectId]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const suggestions = React.useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase().trim();
    return index
      .filter((p) => {
        const sec = getSectorFromAgency(p.agency || '').toLowerCase();
        return (
          p.project_id.toLowerCase().includes(q) ||
          p.project_name.toLowerCase().includes(q) ||
          (p.agency && p.agency.toLowerCase().includes(q)) ||
          (p.state && p.state.toLowerCase().includes(q)) ||
          sec.includes(q)
        );
      })
      .slice(0, 8);
  }, [query, index]);

  const handleSelect = (p: ProjectSearchRecord) => {
    setSelectedRecord(p);
    setIsOpen(false);
    setQuery('');

    if (directNavigateToDossier) {
      router.push(`/projects/${p.project_id}`);
    } else if (onSelectProject) {
      onSelectProject(p);
    }
  };

  const featuredPills = [
    { id: '612786', label: '612786 (Kadapa Airport)' },
    { id: '400178', label: '400178 (Western DFC)' },
    { id: '400244', label: '400244 (Bullet Train)' },
    { id: '613768', label: '613768 (Rishikesh Rail)' },
  ];

  return (
    <div ref={wrapperRef} className="relative w-full max-w-4xl mx-auto space-y-3">
      {/* Search Bar Input Container */}
      <div className="relative flex items-center">
        <div className="absolute left-4 sm:left-5 text-cyan-500 pointer-events-none flex items-center gap-2">
          <Search className="w-5 h-5" />
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && suggestions.length > 0) {
              e.preventDefault();
              handleSelect(suggestions[0]);
            } else if (e.key === 'Escape') {
              setIsOpen(false);
            }
          }}
          placeholder={placeholder}
          className="w-full pl-12 sm:pl-14 pr-12 py-3.5 sm:py-4 rounded-2xl bg-navy-900/90 border border-cyan-500/30 text-white placeholder-concrete-500 text-sm sm:text-base font-medium shadow-glow focus:outline-none focus:border-cyan-400 transition-all backdrop-blur-xl"
        />

        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setIsOpen(false);
            }}
            className="absolute right-4 p-1 rounded-full text-concrete-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Autocomplete Dropdown List */}
      {isOpen && query.trim().length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 rounded-2xl bg-navy-950/95 border border-cyan-500/30 shadow-2xl backdrop-blur-2xl overflow-hidden max-h-96 overflow-y-auto divide-y divide-slate-800/60">
          <div className="px-4 py-2 bg-navy-900/80 text-[10px] font-mono uppercase tracking-wider text-concrete-400 flex items-center justify-between border-b border-cyan-500/10">
            <span>SUGGESTED INFRASTRUCTURE ASSETS</span>
            <span>{suggestions.length} MATCHES</span>
          </div>

          {suggestions.length > 0 ? (
            suggestions.map((p) => (
              <button
                key={p.project_id}
                type="button"
                onClick={() => handleSelect(p)}
                className="w-full px-4 py-3 text-left hover:bg-cyan-500/10 transition-colors flex items-center justify-between gap-3 group"
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-cyan px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                      ID: {p.project_id}
                    </span>
                    <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-navy-800 text-concrete-300 border border-white/10">
                      {getSectorFromAgency(p.agency || '')}
                    </span>
                    {(p.revised_cost_crore || p.original_cost_crore) && (
                      <span className="text-[11px] font-mono text-amber">
                        ₹{Math.round(p.revised_cost_crore || p.original_cost_crore).toLocaleString('en-IN')} Cr
                      </span>
                    )}
                  </div>

                  <h4 className="text-xs sm:text-sm font-semibold text-white group-hover:text-cyan transition-colors truncate">
                    {p.project_name}
                  </h4>

                  <div className="flex items-center gap-3 text-[11px] text-concrete-400">
                    <span className="flex items-center gap-1">
                      <Building2 className="w-3 h-3 text-cyan" />
                      {p.agency}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-cyan" />
                      {p.state}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs font-mono text-cyan opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <span>{directNavigateToDossier ? 'Open Dossier' : 'Select'}</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </button>
            ))
          ) : (
            <div className="px-4 py-6 text-center text-xs font-mono text-concrete-400">
              No matching monitored assets found for &ldquo;{query}&rdquo;.
            </div>
          )}
        </div>
      )}

      {/* Context Status Bar & Quick Pills */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-concrete-400 px-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] uppercase tracking-wider font-semibold text-concrete-500">Quick Select:</span>
          {featuredPills.map((pill) => (
            <button
              key={pill.id}
              type="button"
              onClick={() => {
                const match = index.find((p) => p.project_id === pill.id);
                if (match) handleSelect(match);
              }}
              className="px-2.5 py-1 rounded-lg bg-navy-900 hover:bg-navy-850 border border-cyan-500/20 text-concrete-300 hover:text-cyan transition-colors text-[11px]"
            >
              {pill.label}
            </button>
          ))}
        </div>

        <Link
          href="/projects"
          className="inline-flex items-center gap-1 text-[11px] text-cyan hover:underline ml-auto"
        >
          <span>All 2,741 Projects</span>
          <ArrowUpRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Selected Project Notification Badge if active */}
      {selectedRecord && (
        <div className="flex items-center justify-between p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-xs font-mono">
          <div className="flex items-center gap-2 truncate mr-2">
            <CheckCircle2 className="w-4 h-4 text-cyan flex-shrink-0" />
            <span className="text-white font-bold truncate">
              Active Focus: [{selectedRecord.project_id}] {selectedRecord.project_name}
            </span>
          </div>
          <Link
            href={`/projects/${selectedRecord.project_id}`}
            className="flex items-center gap-1 text-cyan hover:text-white font-bold flex-shrink-0 text-[11px]"
          >
            <span>Full Dossier</span>
            <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      )}
    </div>
  );
}
