'use client';

import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../providers/ThemeProvider';

export default function ThemeToggle() {
  const { theme, toggleTheme, setTheme, mounted } = useTheme();

  // Deterministic SSR state: default to 'dark' until mounted
  const currentTheme = mounted ? theme : 'dark';

  return (
    <div
      role="group"
      aria-label="Theme switcher"
      className="inline-flex items-center p-1 rounded-xl bg-navy-850/90 dark:bg-navy-850/90 light:bg-slate-150 border border-cyan-500/25 dark:border-cyan-500/25 transition-all shadow-inner"
      style={{
        backgroundColor: currentTheme === 'light' ? '#E2E8F0' : '#081A24',
        borderColor: currentTheme === 'light' ? '#CBD5E1' : 'rgba(57, 217, 255, 0.25)',
      }}
    >
      <button
        type="button"
        onClick={() => setTheme('light')}
        aria-pressed={currentTheme === 'light'}
        title="Switch to Light Theme"
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-semibold transition-all duration-200 ${
          currentTheme === 'light'
            ? 'bg-white text-navy-950 shadow-sm border border-slate-200'
            : 'text-concrete-400 hover:text-white'
        }`}
      >
        <Sun className={`w-3.5 h-3.5 ${currentTheme === 'light' ? 'text-amber-500' : 'text-concrete-400'}`} />
        <span className="text-[11px] font-bold">LIGHT</span>
      </button>

      <button
        type="button"
        onClick={() => setTheme('dark')}
        aria-pressed={currentTheme === 'dark'}
        title="Switch to Dark Theme"
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-semibold transition-all duration-200 ${
          currentTheme === 'dark'
            ? 'bg-cyan-500/20 text-cyan border border-cyan-500/40 shadow-glow'
            : 'text-slate-500 hover:text-slate-900'
        }`}
      >
        <Moon className={`w-3.5 h-3.5 ${currentTheme === 'dark' ? 'text-cyan' : 'text-slate-500'}`} />
        <span className="text-[11px] font-bold">DARK</span>
      </button>
    </div>
  );
}
