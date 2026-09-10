'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Shield, Activity, Radio } from 'lucide-react';

export default function Section18_FinalCTA() {
  return (
    <section id="final-cta" className="relative w-full py-32 flex items-center justify-center overflow-hidden bg-navy-950 border-t border-cyan-500/20">
      {/* Background Video Subtle Loop */}
      <div className="absolute inset-0 w-full h-full z-0 overflow-hidden opacity-30">
        <video
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          className="w-full h-full object-cover scale-105"
          src="/videos/SIH_VIDEO_1_final.mp4"
        />
        <div className="absolute inset-0 bg-navy-950/80 pointer-events-none" />
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Emblem */}
        <div className="w-14 h-14 rounded-2xl bg-navy-900 border border-cyan-500/40 mx-auto mb-6 flex items-center justify-center shadow-glow">
          <Shield className="w-8 h-8 text-cyan" />
        </div>

        {/* Brand */}
        <h2 className="text-5xl sm:text-6xl md:text-7xl font-extrabold text-white tracking-tight mb-4">
          PAIMANA
        </h2>

        <p className="text-lg sm:text-2xl font-extrabold uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-200 mb-8">
          INTELLIGENCE FOR A FLOWING FUTURE
        </p>

        {/* Core Pillars Mantra */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs sm:text-sm font-mono font-bold tracking-widest text-concrete-300 uppercase mb-12">
          <span className="text-cyan">MONITOR.</span>
          <span className="text-concrete-600">•</span>
          <span className="text-white">PREDICT.</span>
          <span className="text-concrete-600">•</span>
          <span className="text-amber">PRIORITIZE.</span>
          <span className="text-concrete-600">•</span>
          <span className="text-teal">PREVENT.</span>
        </div>

        {/* Final CTA Button */}
        <Link
          href="/project-dossier"
          className="inline-flex items-center justify-center gap-3 px-9 py-4 rounded-xl bg-gradient-to-r from-cyan to-teal text-navy-950 font-extrabold text-sm tracking-wide shadow-glow hover:shadow-cyan/50 hover:scale-105 transition-all"
        >
          <span>ENTER PROJECT INTELLIGENCE</span>
          <ArrowRight className="w-4 h-4" />
        </Link>

        {/* Footer info */}
        <div className="mt-16 pt-8 border-t border-concrete-800/80 text-xs font-mono text-concrete-500 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span>MoSPI / IPMD Strategic Platform • SIH 2026 Problem Statement SIH26103</span>
          <span>© 2026 PAIMANA • High-Fidelity Infrastructure Surveillance</span>
        </div>
      </div>
    </section>
  );
}
