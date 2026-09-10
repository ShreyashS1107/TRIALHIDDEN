'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import { CustomProjectForm } from '@/components/projects/custom/CustomProjectForm';
import { AnalyticalLoadingModal } from '@/components/projects/custom/AnalyticalLoadingModal';
import { CustomProjectInput, predictCustomProject } from '@/lib/api/predict';
import { Sparkles, ShieldAlert, RotateCcw } from 'lucide-react';

export default function CustomProjectPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSubmitted, setLastSubmitted] = useState<CustomProjectInput | null>(null);
  const [initialData, setInitialData] = useState<Partial<CustomProjectInput> | undefined>(undefined);

  useEffect(() => {
    // Check if user came back from edit
    if (typeof window !== 'undefined') {
      try {
        const stored = sessionStorage.getItem('paimana_custom_assessment') || localStorage.getItem('paimana_custom_assessment');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed?.input) {
            setInitialData(parsed.input);
          }
        }
      } catch (e) {}
    }
  }, []);

  const handleFormSubmit = async (data: CustomProjectInput) => {
    setIsLoading(true);
    setError(null);
    setLastSubmitted(data);

    try {
      // Step through minimum scanning interval for full analytical telemetry visibility
      const [res] = await Promise.all([
        predictCustomProject(data),
        new Promise((r) => setTimeout(r, 1600))
      ]);

      if (typeof window !== 'undefined') {
        const payload = JSON.stringify({ input: data, result: res });
        sessionStorage.setItem('paimana_custom_assessment', payload);
        localStorage.setItem('paimana_custom_assessment', payload);
      }

      router.push(`/custom-project/result?id=${encodeURIComponent(data.project_id)}`);
    } catch (err: any) {
      setError(err.message || 'PAIMANA ML INFERENCE ENGINE UNAVAILABLE');
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-[#040d13] text-slate-900 dark:text-slate-100 flex flex-col justify-between">
      <Navbar />

      {/* Analytical Telemetry Modal */}
      <AnalyticalLoadingModal
        isOpen={isLoading}
        projectName={lastSubmitted?.project_name || initialData?.project_name || 'Custom Infrastructure Asset'}
      />

      <div className="pt-28 pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          {/* Page Hero Header */}
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-600 dark:text-cyan-400 font-semibold tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>PAIMANA PREDICTIVE INTAKE PIPELINE</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              CUSTOM PROJECT ASSESSMENT
            </h1>

            <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
              &ldquo;Evaluate infrastructure project risk before delays and cost escalation become critical.&rdquo;
            </p>
          </div>

          {/* Explicit Error State */}
          {error && (
            <div className="max-w-3xl mx-auto p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-slate-900 dark:text-white space-y-4 shadow-lg animate-in fade-in duration-200">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0 mt-0.5">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div className="space-y-1 flex-1">
                  <h3 className="text-sm font-bold text-rose-600 dark:text-rose-400 font-mono uppercase tracking-wider">
                    PAIMANA ML INFERENCE ENGINE UNAVAILABLE
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Start the ML service and try again. The trained ML pipeline is the sole source of truth; client-side approximation is disabled.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-rose-500/20">
                <button
                  type="button"
                  onClick={() => {
                    setError(null);
                    if (lastSubmitted) {
                      handleFormSubmit(lastSubmitted);
                    }
                  }}
                  className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-mono font-bold text-xs uppercase tracking-wider flex items-center gap-2 transition-colors shadow-sm"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>TRY AGAIN</span>
                </button>
              </div>
            </div>
          )}

          {/* Progressive 5-Step Form */}
          <CustomProjectForm
            initialValues={initialData}
            onSubmit={handleFormSubmit}
            isLoading={isLoading}
          />
        </div>
      </div>

      <footer className="border-t border-slate-200 dark:border-white/10 py-8 bg-slate-100 dark:bg-[#03090e] text-center text-xs font-mono text-slate-500 space-y-1">
        <p>PAIMANA • Custom Infrastructure Assessment Portal • MoSPI Surveillance Interface</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500">Authoritative RF_02 Holdout Calibrated ML Inference Engine</p>
      </footer>
    </main>
  );
}
