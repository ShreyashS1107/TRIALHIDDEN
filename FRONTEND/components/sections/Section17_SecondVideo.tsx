'use client';

import React from 'react';
import { ArrowDown, Radio } from 'lucide-react';

export default function Section17_SecondVideo() {
  return (
    <section className="relative w-full h-[70vh] min-h-[500px] flex items-center justify-center overflow-hidden bg-navy-950 border-t border-cyan-500/20">
      {/* Cinematic Background Video (SIH_VIDEO_2_final.mp4) */}
      <div className="absolute inset-0 w-full h-full z-0 overflow-hidden">
        <video
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          className="w-full h-full object-cover scale-105"
          src="/videos/SIH_VIDEO_2_final.mp4"
        >
          Your browser does not support the video tag.
        </video>

        {/* Subtle Dark Navy Gradient Overlay: Infrastructure remains fully visible */}
        <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-navy-950/40 to-navy-950 pointer-events-none" />
        <div className="absolute inset-0 bg-navy-950/25 pointer-events-none" />
      </div>

      {/* Storytelling Text Overlay */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-navy-900/80 border border-cyan-500/30 text-xs font-mono text-cyan-300 mb-6 backdrop-blur-md">
          <Radio className="w-3 h-3 text-cyan animate-pulse" />
          <span>NATIONAL SURVEILLANCE CONTINUUM</span>
        </div>

        <div className="space-y-4">
          <span className="block text-sm sm:text-base md:text-lg font-mono tracking-widest text-concrete-300 uppercase">
            FROM PROJECT DATA
          </span>

          <span className="block text-xs font-mono text-cyan tracking-widest uppercase">
            ↓
          </span>

          <span className="block text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan via-white to-teal tracking-tight uppercase">
            TO EARLY INTELLIGENCE
          </span>

          <span className="block text-xs font-mono text-cyan tracking-widest uppercase">
            ↓
          </span>

          <span className="block text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-extrabold text-amber tracking-tight uppercase">
            TO EARLY ACTION
          </span>
        </div>
      </div>
    </section>
  );
}
