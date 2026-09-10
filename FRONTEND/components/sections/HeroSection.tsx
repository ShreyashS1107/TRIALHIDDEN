'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowRight, ShieldAlert, Cpu, BarChart3, Radio } from 'lucide-react';

export default function HeroSection() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section id="hero" className="relative w-full min-h-screen flex items-center justify-center overflow-hidden bg-navy-950">
      {/* 1. Cinematic Background Video */}
      <div className="absolute inset-0 w-full h-full z-0 overflow-hidden">
        <video
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          className="w-full h-full object-cover scale-105 transition-transform duration-1000 ease-out"
          src="/videos/SIH_VIDEO_1_final.mp4"
        >
          Your browser does not support the video tag.
        </video>

        {/* Subtle Dark Navy Gradient Overlay: Infrastructure remains fully visible */}
        <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-navy-900/40 to-navy-950/60 pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_30%,_rgba(6,19,28,0.75)_100%)] pointer-events-none" />
      </div>

      {/* 2. Digital Twin Intelligence Overlay: Subtle Cyan Connection Lines & Data Nodes */}
      <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
        <svg className="w-full h-full opacity-60">
          <defs>
            <linearGradient id="cyanLineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#39D9FF" stopOpacity="0.1" />
              <stop offset="50%" stopColor="#39D9FF" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#27C7B8" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          {/* Infrastructure Vector Vectors across bridge & river */}
          <line x1="20%" y1="65%" x2="45%" y2="58%" stroke="url(#cyanLineGrad)" strokeWidth="1" strokeDasharray="4 4" className="animate-pulse" />
          <line x1="45%" y1="58%" x2="72%" y2="52%" stroke="url(#cyanLineGrad)" strokeWidth="1.5" />
          <line x1="72%" y1="52%" x2="88%" y2="40%" stroke="url(#cyanLineGrad)" strokeWidth="1" strokeDasharray="3 3" />
          <line x1="45%" y1="58%" x2="52%" y2="78%" stroke="url(#cyanLineGrad)" strokeWidth="1" />

          {/* Traveling Data Packet Circles */}
          <circle cx="45%" cy="58%" r="4" fill="#39D9FF" className="animate-ping" opacity="0.75" />
          <circle cx="45%" cy="58%" r="2.5" fill="#FFFFFF" />
          
          <circle cx="72%" cy="52%" r="4" fill="#39D9FF" className="animate-ping" opacity="0.6" style={{ animationDelay: '1s' }} />
          <circle cx="72%" cy="52%" r="2.5" fill="#27C7B8" />

          <circle cx="20%" cy="65%" r="3.5" fill="#39D9FF" opacity="0.8" />
          <circle cx="52%" cy="78%" r="3.5" fill="#F4B942" className="animate-pulse" />
        </svg>

        {/* Floating miniature telemetry badges hovering over physical nodes */}
        <div className="absolute top-[55%] left-[46%] hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded bg-navy-950/80 border border-cyan-500/30 text-[10px] font-mono text-cyan-300 backdrop-blur-sm shadow-glow animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" />
          <span>BRIDGE VIADUCT PKG-IV • 74.2% BUILD</span>
        </div>
        <div className="absolute top-[49%] left-[73%] hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded bg-navy-950/80 border border-cyan-500/30 text-[10px] font-mono text-cyan-300 backdrop-blur-sm shadow-glow animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
          <span>TRANS-HARBOUR SPAN • SENSOR ACTIVE</span>
        </div>
        <div className="absolute top-[75%] left-[53%] hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded bg-navy-950/80 border border-amber-500/40 text-[10px] font-mono text-amber-300 backdrop-blur-sm shadow-glow-amber animate-fade-in">
          <span className="w-1.5 h-1.5 rounded-full bg-amber animate-ping" />
          <span>PIER FOUNDATION • STRESS WATCH (ESI 0.42)</span>
        </div>
      </div>

      {/* 3. Hero Content */}
      <div className="relative z-20 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center pt-24 pb-16">
        {/* Status Indicator */}
        <div className={`inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-navy-900/85 border border-cyan-500/30 backdrop-blur-md text-xs font-mono text-cyan-300 mb-8 shadow-glow transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <Radio className="w-3.5 h-3.5 text-cyan animate-pulse" />
          <span className="tracking-widest font-semibold uppercase text-[11px]">● LIVE INTELLIGENCE LAYER</span>
          <span className="text-concrete-500">|</span>
          <span className="text-concrete-300 font-sans text-[11px]">MoSPI / IPMD Surveillance Protocol</span>
        </div>

        {/* Brand Name */}
        <h1 className={`text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-extrabold tracking-tight text-white mb-4 transition-all duration-1000 ${mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
          PAIMANA
        </h1>

        {/* Tagline */}
        <div className={`space-y-1 mb-6 transition-all duration-1000 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <p className="text-xl sm:text-2xl md:text-3xl font-extrabold uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-200">
            INTELLIGENCE FOR A FLOWING FUTURE
          </p>
        </div>

        {/* Supporting Text */}
        <p className={`max-w-2xl mx-auto text-base sm:text-lg text-concrete-300 font-normal leading-relaxed mb-10 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          A predictive infrastructure intelligence platform for continuous monitoring, probabilistic risk detection, and prescriptive decision support.
        </p>

        {/* CTA Action Buttons */}
        <div className={`flex flex-col sm:flex-row items-center justify-center gap-4 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <Link
            href="/projects"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan to-teal text-navy-950 font-bold text-sm tracking-wide transition-all shadow-glow hover:shadow-cyan/50 hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>SEARCH 2,741 PROJECTS</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <Link
            href="/project-dossier"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-navy-850/90 hover:bg-navy-800 border border-cyan-500/40 text-cyan-300 font-semibold text-sm tracking-wide transition-all backdrop-blur-md hover:border-cyan-400 hover:scale-[1.02]"
          >
            <span>LIVE INTELLIGENCE DOSSIER</span>
          </Link>

          <Link
            href="/custom-project"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-navy-850/90 hover:bg-navy-800 border border-amber-500/40 text-amber font-semibold text-sm tracking-wide transition-all backdrop-blur-md hover:border-amber-400 hover:scale-[1.02]"
          >
            <ShieldAlert className="w-4 h-4 text-amber" />
            <span>CUSTOM ASSESSMENT</span>
          </Link>
        </div>

        {/* Quick Micro-Stats Bar */}
        <div className={`mt-14 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto text-left transition-all duration-1000 delay-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          <div className="glass-panel p-3 rounded-lg border-cyan-500/20">
            <span className="block text-[10px] uppercase font-mono text-concrete-400">Total Portfolio</span>
            <span className="text-lg font-bold font-mono text-white">21,555</span>
            <span className="block text-[10px] text-cyan-300">Project-Months</span>
          </div>
          <div className="glass-panel p-3 rounded-lg border-cyan-500/20">
            <span className="block text-[10px] uppercase font-mono text-concrete-400">Monitored Assets</span>
            <span className="text-lg font-bold font-mono text-white">2,741</span>
            <span className="block text-[10px] text-cyan-300">Central Projects</span>
          </div>
          <div className="glass-panel p-3 rounded-lg border-cyan-500/20">
            <span className="block text-[10px] uppercase font-mono text-concrete-400">Time-Series Depth</span>
            <span className="text-lg font-bold font-mono text-white">15 Months</span>
            <span className="block text-[10px] text-teal-300">Apr 2025 → Jun 2026</span>
          </div>
          <div className="glass-panel p-3 rounded-lg border-amber-500/30">
            <span className="block text-[10px] uppercase font-mono text-concrete-400">Capital Value</span>
            <span className="text-lg font-bold font-mono text-amber">₹53.64 L Cr</span>
            <span className="block text-[10px] text-amber-300/80">Revised Budget</span>
          </div>
        </div>
      </div>

      {/* Bottom Subtle Scroll Indicator */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-1.5 pointer-events-none opacity-60">
        <span className="text-[10px] font-mono tracking-widest uppercase text-concrete-400">Scroll to Explore</span>
        <div className="w-5 h-8 rounded-full border border-cyan-500/40 flex items-start justify-center p-1">
          <div className="w-1 h-2 rounded-full bg-cyan animate-bounce" />
        </div>
      </div>
    </section>
  );
}
