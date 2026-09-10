'use client';

import React, { useState, useEffect } from 'react';
import { Shield, Activity, Search, Menu, X, Cpu, ChevronRight } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

interface NavbarProps {
  onOpenAssistant?: () => void;
  activeSection?: string;
}

export default function Navbar({ onOpenAssistant, activeSection }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { label: 'Overview', href: '/#hero' },
    { label: 'Search Projects', href: '/projects' },
    { label: 'Custom Project', href: '/custom-project' },
    { label: 'Infrastructure 3D', href: '/#landscape' },
    { label: 'Data Foundation', href: '/#data-foundation' },
    { label: 'Dossier', href: '/#project-intelligence' },
    { label: 'Risk Prediction', href: '/#risk-prediction' },
    { label: 'Cost & Schedule', href: '/#cost-intelligence' },
    { label: 'Explainable AI', href: '/#explainable-ai' },
    { label: 'Alerts', href: '/#early-warning' },
    { label: 'India Map', href: '/#india-map' },
    { label: 'What-If', href: '/#what-if' },
    { label: 'Compare', href: '/#comparison' },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/90 dark:bg-navy-950/85 backdrop-blur-md border-b border-slate-200 dark:border-cyan-500/20 py-2.5 shadow-md dark:shadow-2xl'
          : 'bg-gradient-to-b from-white/95 via-white/50 dark:from-navy-950/90 dark:via-navy-950/40 to-transparent py-4'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Brand Logo & Tagline */}
          <a href="#hero" className="flex items-center gap-3 group">
            <div className="relative w-9 h-9 rounded-lg bg-slate-100 dark:bg-navy-800 border border-cyan-600/30 dark:border-cyan-500/40 flex items-center justify-center overflow-hidden shadow-sm dark:shadow-glow">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 to-teal-500/10" />
              <Shield className="w-5 h-5 text-cyan-600 dark:text-cyan relative z-10 group-hover:scale-110 transition-transform" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-widest text-lg text-slate-900 dark:text-white">
                  PAIMANA
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-700 dark:text-cyan-300 font-semibold tracking-wider">
                  SIH26103
                </span>
              </div>
              <span className="text-[9px] uppercase tracking-wider text-slate-500 dark:text-concrete-400 font-medium hidden sm:block">
                Intelligence for a Flowing Future
              </span>
            </div>
          </a>

          {/* Desktop Nav Items */}
          <nav className="hidden xl:flex items-center gap-1.5 text-xs font-medium text-slate-600 dark:text-concrete-300">
            {navLinks.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="px-2.5 py-1.5 rounded-md hover:text-cyan-600 dark:hover:text-cyan hover:bg-cyan-500/10 transition-colors tracking-wide"
              >
                {item.label}
              </a>
            ))}
          </nav>

          {/* Right Status & Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Live Intelligence Indicator */}
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-navy-850 border border-slate-200 dark:border-cyan-500/25 text-[11px] font-mono text-cyan-700 dark:text-cyan-300">
              <span className="w-2 h-2 rounded-full bg-cyan animate-ping-slow" />
              <span className="font-semibold tracking-wide">LIVE INTELLIGENCE</span>
            </div>

            {/* AI Assistant Quick Toggle */}
            <button
              onClick={onOpenAssistant}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 text-cyan-700 dark:text-cyan text-xs font-semibold tracking-wide transition-all shadow-sm dark:shadow-glow hover:shadow-cyan/40"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span className="hidden md:inline">AI ASSISTANT</span>
            </button>

            {/* Global Theme Toggle: ☀ LIGHT / 🌙 DARK */}
            <ThemeToggle />

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="xl:hidden p-2 rounded-lg bg-slate-100 dark:bg-navy-800 border border-slate-200 dark:border-cyan-500/20 text-slate-700 dark:text-concrete-200 hover:text-black dark:hover:text-white"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="xl:hidden mt-3 pt-3 border-t border-slate-200 dark:border-cyan-500/20 grid grid-cols-2 gap-2 bg-white/95 dark:bg-navy-950/95 p-4 rounded-xl backdrop-blur-xl border border-slate-200 dark:border-cyan-500/30 shadow-xl">
            {navLinks.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 text-xs rounded-lg text-slate-700 dark:text-concrete-300 hover:text-cyan-600 dark:hover:text-cyan hover:bg-cyan-500/10 transition-colors flex items-center justify-between"
              >
                <span>{item.label}</span>
                <ChevronRight className="w-3 h-3 text-cyan-500/50" />
              </a>
            ))}
            <div className="col-span-2 pt-3 mt-1 border-t border-slate-200 dark:border-cyan-500/20 flex justify-between items-center">
              <span className="text-xs text-slate-500 dark:text-concrete-400 font-mono font-bold">THEME</span>
              <ThemeToggle />
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
