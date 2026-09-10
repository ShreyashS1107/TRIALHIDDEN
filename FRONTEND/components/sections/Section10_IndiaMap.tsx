'use client';

import React, { useState, useEffect } from 'react';
import { MapPin, Filter, Search, ShieldAlert, ArrowUpRight, CheckCircle2, Layers } from 'lucide-react';
import { IndiaNode, ProjectDetail } from '@/lib/api/types';
import { formatIndianNumber } from '@/lib/utils/format';

interface Section10Props {
  nodes?: IndiaNode[];
  onSelectProjectId?: (id: string) => void;
}

export default function Section10_IndiaMap({ nodes = [], onSelectProjectId }: Section10Props) {
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [filterSector, setFilterSector] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<IndiaNode | null>(null);

  // Geographic bounds for India: lat [8.0, 36.0], lng [68.0, 97.0]
  const projectCoords = (lat: number, lng: number) => {
    const minLat = 7.0;
    const maxLat = 37.0;
    const minLng = 67.0;
    const maxLng = 98.0;

    const x = ((lng - minLng) / (maxLng - minLng)) * 100;
    const y = (1 - (lat - minLat) / (maxLat - minLat)) * 100;
    return { x: Math.max(5, Math.min(95, x)), y: Math.max(5, Math.min(95, y)) };
  };

  const filteredNodes = nodes.filter((n) => {
    if (filterRisk !== 'ALL') {
      if (filterRisk === 'CRITICAL' && n.status !== 'critical') return false;
      if (filterRisk === 'ATTENTION' && n.status !== 'attention') return false;
      if (filterRisk === 'HEALTHY' && n.status !== 'healthy') return false;
    }
    if (filterSector !== 'ALL' && n.sector !== filterSector) return false;
    return true;
  });

  return (
    <section id="india-map" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <MapPin className="w-3.5 h-3.5" />
              <span>SECTION 10 • GEOGRAPHIC TWIN SURVEILLANCE</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              INDIA INFRASTRUCTURE MAP
            </h2>
          </div>
          <p className="max-w-md text-xs sm:text-sm text-concrete-300">
            2.5D interactive geographic distribution tracking central ongoing projects across state corridors. Filter by Sector or Risk Status to inspect regional clusters.
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8 bg-navy-950 p-4 rounded-xl border border-cyan-500/20 text-xs font-mono">
          <div className="flex items-center gap-3">
            <span className="text-concrete-400">Risk Filter:</span>
            {['ALL', 'CRITICAL', 'ATTENTION', 'HEALTHY'].map((rf) => (
              <button
                key={rf}
                onClick={() => setFilterRisk(rf)}
                className={`px-3 py-1 rounded-lg font-bold transition-all ${
                  filterRisk === rf
                    ? 'bg-cyan-500/20 border border-cyan text-white shadow-glow'
                    : 'text-concrete-400 hover:text-white'
                }`}
              >
                {rf}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-concrete-400">Sector:</span>
            <select
              value={filterSector}
              onChange={(e) => setFilterSector(e.target.value)}
              className="bg-navy-900 border border-concrete-700 text-white rounded-lg px-2.5 py-1 text-xs outline-none focus:border-cyan"
            >
              <option value="ALL">All Sectors</option>
              <option value="Roads & Highways">Roads & Highways</option>
              <option value="Railways & Metro">Railways & Metro</option>
              <option value="Petroleum & Natural Gas">Petroleum & Natural Gas</option>
              <option value="Power & Energy">Power & Energy</option>
              <option value="Coal & Mines">Coal & Mines</option>
            </select>
          </div>
        </div>

        {/* Map Canvas Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* 2.5D Map Container (8 cols) */}
          <div className="lg:col-span-8 glass-panel p-6 sm:p-8 rounded-2xl border-cyan-500/30 relative min-h-[500px] flex items-center justify-center overflow-hidden">
            {/* Background Grid & Subcontinent Contour */}
            <div className="absolute inset-0 bg-[radial-gradient(#0f2a38_1px,_transparent_1px)] [background-size:24px_24px] opacity-60 pointer-events-none" />

            {/* Stylized India Geography Vector Backdrop */}
            <svg
              className="w-full h-full max-h-[480px] opacity-35 pointer-events-none"
              viewBox="0 0 100 100"
              preserveAspectRatio="xMidYMid meet"
            >
              <path
                d="M 32,15 Q 38,10 44,14 Q 50,18 48,25 Q 60,26 68,32 Q 74,38 78,35 Q 84,40 76,46 Q 66,48 60,52 Q 54,60 52,70 Q 48,82 45,92 Q 42,92 38,82 Q 32,70 30,60 Q 25,50 20,44 Q 18,36 24,30 Q 30,22 32,15 Z"
                fill="none"
                stroke="#39D9FF"
                strokeWidth="0.8"
                strokeDasharray="2 2"
              />
            </svg>

            {/* Render Map Nodes */}
            <div className="absolute inset-0 p-8">
              {filteredNodes.map((node) => {
                const { x, y } = projectCoords(node.lat, node.lng);
                const isSelected = selectedNode?.project_id === node.project_id;

                const nodeColor =
                  node.status === 'critical'
                    ? 'bg-critical'
                    : node.status === 'attention'
                    ? 'bg-amber'
                    : 'bg-cyan';

                return (
                  <div
                    key={node.project_id}
                    onClick={() => setSelectedNode(node)}
                    className="absolute cursor-pointer -translate-x-1/2 -translate-y-1/2 group z-20"
                    style={{ left: `${x}%`, top: `${y}%` }}
                  >
                    <div className="relative flex items-center justify-center">
                      {/* Pulse Ring */}
                      <span className={`absolute w-6 h-6 rounded-full opacity-40 animate-ping-slow ${nodeColor}`} />
                      {/* Core Dot */}
                      <span
                        className={`w-3.5 h-3.5 rounded-full border-2 border-navy-950 transition-all ${nodeColor} ${
                          isSelected ? 'scale-150 ring-2 ring-white' : 'group-hover:scale-125'
                        }`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Map Legend Footer */}
            <div className="absolute bottom-4 left-4 z-10 flex items-center gap-4 text-[11px] font-mono glass-panel p-2.5 rounded-lg border-concrete-800">
              <span className="flex items-center gap-1.5 text-cyan">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan" /> Healthy
              </span>
              <span className="flex items-center gap-1.5 text-amber">
                <span className="w-2.5 h-2.5 rounded-full bg-amber" /> Attention
              </span>
              <span className="flex items-center gap-1.5 text-critical">
                <span className="w-2.5 h-2.5 rounded-full bg-critical" /> Critical
              </span>
            </div>
          </div>

          {/* Right Selected Project Details Panel (4 cols) */}
          <div className="lg:col-span-4">
            {selectedNode ? (
              <div className="glass-panel p-6 rounded-2xl border-cyan-500/40 text-left space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-cyan-300">
                    ID: {selectedNode.project_id}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                      selectedNode.status === 'critical'
                        ? 'bg-critical/20 text-critical border border-critical/40'
                        : selectedNode.status === 'attention'
                        ? 'bg-amber/20 text-amber border border-amber/40'
                        : 'bg-cyan-500/20 text-cyan border border-cyan-500/40'
                    }`}
                  >
                    {selectedNode.status.toUpperCase()}
                  </span>
                </div>

                <h4 className="text-base font-extrabold text-white">
                  {selectedNode.project_name}
                </h4>

                <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2 border-t border-cyan-500/20">
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase font-sans">Agency</span>
                    <span className="text-white font-semibold">{selectedNode.agency}</span>
                  </div>
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase font-sans">State</span>
                    <span className="text-teal font-semibold">{selectedNode.state}</span>
                  </div>
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase font-sans">Sector</span>
                    <span className="text-white">{selectedNode.sector}</span>
                  </div>
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase font-sans">Physical Progress</span>
                    <span className="text-cyan font-bold">{selectedNode.physical_progress}%</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-navy-950/80 border border-concrete-800 text-xs font-mono">
                  <span className="text-concrete-400 block text-[9px] uppercase font-sans">Anticipated Cost</span>
                  <span className="text-white font-bold text-sm">
                    ₹{formatIndianNumber(selectedNode.revised_cost_crore)} Cr
                  </span>
                </div>

                {onSelectProjectId && (
                  <button
                    onClick={() => onSelectProjectId(selectedNode.project_id)}
                    className="w-full py-2.5 rounded-xl bg-cyan text-navy-950 font-bold text-xs font-mono tracking-wider flex items-center justify-center gap-1.5 hover:bg-cyan-300 transition-colors shadow-glow"
                  >
                    <span>OPEN PROJECT DOSSIER</span>
                    <ArrowUpRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            ) : (
              <div className="glass-panel p-8 rounded-2xl border-cyan-500/20 text-center space-y-3">
                <MapPin className="w-8 h-8 text-cyan mx-auto opacity-50" />
                <h4 className="text-sm font-bold text-white">Select a Geographic Node</h4>
                <p className="text-xs text-concrete-400">
                  Click on any infrastructure point on the map to inspect location telemetry, sector classification, and live risk status.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
