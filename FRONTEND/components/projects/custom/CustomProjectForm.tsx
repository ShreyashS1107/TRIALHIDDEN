'use client';

import React, { useState } from 'react';
import { CustomProjectInput } from '@/lib/api/predict';
import {
  Building2,
  Calendar,
  IndianRupee,
  Activity,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Loader2,
  ShieldAlert,
  FileCheck
} from 'lucide-react';

interface Props {
  initialValues?: Partial<CustomProjectInput>;
  onSubmit: (data: CustomProjectInput) => Promise<void>;
  isLoading: boolean;
}

const COMMON_AGENCIES = [
  'Airport Authority of India [AAI]',
  'National Highways Authority of India [NHAI]',
  'Power Grid Corporation of India [PGCIL]',
  'Ministry of Railways [MOR]',
  'South Eastern Coalfields Limited [SECL]',
  'Eastern Coalfields Limited [ECL]',
  'Western Coalfields Limited [WCL]',
  'NTPC Limited',
  'National Highways & Infrastructure Development Corp [NHIDCL]',
  'Delhi Metro Rail Corporation [DMRC]'
];

const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan',
  'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
  'Uttarakhand', 'West Bengal', 'Central / Multi-State'
];

export function CustomProjectForm({ initialValues, onSubmit, isLoading }: Props) {
  const [step, setStep] = useState<number>(1);

  const [formData, setFormData] = useState<CustomProjectInput>({
    project_name: initialValues?.project_name || '',
    project_id: initialValues?.project_id || '',
    agency: initialValues?.agency || 'National Highways Authority of India [NHAI]',
    state: initialValues?.state || 'Maharashtra',
    original_cost_crore: initialValues?.original_cost_crore || 1250.0,
    revised_cost_crore: initialValues?.revised_cost_crore || 1420.0,
    approval_start_date: initialValues?.approval_start_date || '2023-06',
    original_completion_date: initialValues?.original_completion_date || '2026-12',
    revised_completion_date: initialValues?.revised_completion_date || '2027-06',
    physical_progress_percent: initialValues?.physical_progress_percent !== undefined ? initialValues.physical_progress_percent : 45.0,
    is_completed: initialValues?.is_completed || false,
    cumulative_expenditure_crore: initialValues?.cumulative_expenditure_crore || 620.0,
    sector: initialValues?.sector || 'Road Transport & Highways'
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateStep = (currentStep: number): boolean => {
    const errs: Record<string, string> = {};

    if (currentStep === 1) {
      if (!formData.project_name.trim()) errs.project_name = 'Project name is required';
      if (!formData.project_id.trim()) errs.project_id = 'Project ID or reference code is required';
      if (!formData.agency.trim()) errs.agency = 'Implementing agency is required';
      if (!formData.state.trim()) errs.state = 'State is required';
      if (!formData.sector || !formData.sector.trim()) errs.sector = 'Infrastructure sector is required';
    }

    if (currentStep === 2) {
      const orig = Number(formData.original_cost_crore);
      const rev = Number(formData.revised_cost_crore);
      if (!orig || orig <= 0) {
        errs.original_cost_crore = 'Approved cost must be a positive number greater than 0';
      }
      if (rev < 0) {
        errs.revised_cost_crore = 'Revised cost cannot be negative';
      } else if (rev > 0 && orig > 0 && rev < orig) {
        errs.revised_cost_crore = 'Revised cost cannot be less than original sanctioned cost';
      }
    }

    if (currentStep === 3) {
      if (!formData.approval_start_date || !/^\d{4}-\d{2}$/.test(formData.approval_start_date)) {
        errs.approval_start_date = 'Enter a valid approval month in YYYY-MM format';
      }
      if (!formData.original_completion_date || !/^\d{4}-\d{2}$/.test(formData.original_completion_date)) {
        errs.original_completion_date = 'Enter a valid target completion month in YYYY-MM format';
      }
      if (formData.approval_start_date && formData.original_completion_date) {
        if (formData.original_completion_date < formData.approval_start_date) {
          errs.original_completion_date = 'Target completion date must be after approval date';
        }
      }
      if (formData.revised_completion_date && formData.revised_completion_date.trim()) {
        if (!/^\d{4}-\d{2}$/.test(formData.revised_completion_date)) {
          errs.revised_completion_date = 'Enter a valid revised month in YYYY-MM format';
        } else if (formData.revised_completion_date < formData.approval_start_date) {
          errs.revised_completion_date = 'Revised completion date must be after approval date';
        }
      }
    }

    if (currentStep === 4) {
      const p = Number(formData.physical_progress_percent);
      if (isNaN(p) || p < 0 || p > 100) {
        errs.physical_progress_percent = 'Physical progress must be between 0% and 100%';
      }
      if (formData.cumulative_expenditure_crore !== undefined && Number(formData.cumulative_expenditure_crore) < 0) {
        errs.cumulative_expenditure_crore = 'Expenditure cannot be negative';
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep((prev) => Math.min(5, prev + 1));
    }
  };

  const handlePrev = () => {
    setStep((prev) => Math.max(1, prev - 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Validate all steps
    for (let s = 1; s <= 5; s++) {
      if (!validateStep(s)) {
        setStep(s);
        return;
      }
    }
    await onSubmit(formData);
  };

  const stepsList = [
    { num: 1, label: 'PROJECT', desc: 'Identity & Agency' },
    { num: 2, label: 'COST', desc: 'Approved & Revised' },
    { num: 3, label: 'SCHEDULE', desc: 'Timeline & DOC' },
    { num: 4, label: 'PROGRESS', desc: 'Physical Milestones' },
    { num: 5, label: 'STATUS', desc: 'Review & Verify' }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Progressive Step Tracker */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-[#06131c]/80 border border-slate-200 dark:border-white/10 shadow-sm">
        <div className="grid grid-cols-5 gap-2">
          {stepsList.map((s) => {
            const isActive = step === s.num;
            const isCompleted = step > s.num;

            return (
              <button
                key={s.num}
                type="button"
                onClick={() => {
                  if (s.num < step || validateStep(step)) setStep(s.num);
                }}
                className={`flex flex-col items-center text-center p-2 rounded-xl transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-600 dark:text-cyan-400 font-bold'
                    : isCompleted
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-slate-400 dark:text-slate-600'
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold mb-1 transition-colors ${
                    isActive
                      ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                      : isCompleted
                      ? 'bg-emerald-500 text-slate-950'
                      : 'bg-slate-200 dark:bg-white/10 text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {isCompleted ? '✓' : `0${s.num}`}
                </div>
                <span className="text-[11px] font-mono tracking-wider uppercase hidden sm:block">
                  {s.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Linear progress bar */}
        <div className="w-full bg-slate-200 dark:bg-white/10 h-1.5 rounded-full mt-3 overflow-hidden">
          <div
            className="bg-cyan-500 h-full rounded-full transition-all duration-300"
            style={{ width: `${(step / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Form Card */}
      <form onSubmit={handleSubmit} className="p-6 sm:p-8 rounded-2xl bg-white dark:bg-[#06131c]/70 border border-slate-200 dark:border-white/10 shadow-sm space-y-6">
        {/* Step 1: PROJECT INFORMATION */}
        {step === 1 && (
          <div className="space-y-5 animate-in fade-in duration-200">
            <div className="border-b border-slate-200 dark:border-white/10 pb-3">
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Phase 01
              </span>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Project Information & Authority
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Identify the asset and implementing ministry under MoSPI longitudinal surveillance.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2 space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Project Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.project_name}
                  onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                  placeholder="e.g. Construction of 4-Lane Greenfield Highway Corridor"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm focus:outline-none focus:border-cyan-500"
                />
                {errors.project_name && <p className="text-xs text-rose-500 font-mono">{errors.project_name}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Project ID / Reference Code <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  placeholder="e.g. NHAI-CORR-2026"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                {errors.project_id && <p className="text-xs text-rose-500 font-mono">{errors.project_id}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  State / Territory <span className="text-rose-500">*</span>
                </label>
                <select
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#06131c] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm focus:outline-none focus:border-cyan-500"
                >
                  {INDIAN_STATES.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
                {errors.state && <p className="text-xs text-rose-500 font-mono">{errors.state}</p>}
              </div>

              <div className="sm:col-span-2 space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Implementing Agency <span className="text-rose-500">*</span>
                </label>
                <input
                  list="agencies-list"
                  type="text"
                  value={formData.agency}
                  onChange={(e) => setFormData({ ...formData, agency: e.target.value })}
                  placeholder="Select or type agency..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm focus:outline-none focus:border-cyan-500"
                />
                <datalist id="agencies-list">
                  {COMMON_AGENCIES.map((ag) => (
                    <option key={ag} value={ag} />
                  ))}
                </datalist>
                {errors.agency && <p className="text-xs text-rose-500 font-mono">{errors.agency}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: COST INFORMATION */}
        {step === 2 && (
          <div className="space-y-5 animate-in fade-in duration-200">
            <div className="border-b border-slate-200 dark:border-white/10 pb-3">
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Phase 02
              </span>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Cost & Capital Outlay
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Preserve the standard unit of ₹ Crore (Crores of Indian Rupees).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Original / Approved Cost (₹ Crore) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm font-mono font-bold">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={formData.original_cost_crore}
                    onChange={(e) => setFormData({ ...formData, original_cost_crore: parseFloat(e.target.value) || 0 })}
                    placeholder="e.g. 1250.00"
                    className="w-full pl-8 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                {errors.original_cost_crore && <p className="text-xs text-rose-500 font-mono">{errors.original_cost_crore}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Revised Anticipated Cost (₹ Crore) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm font-mono font-bold">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.revised_cost_crore}
                    onChange={(e) => setFormData({ ...formData, revised_cost_crore: parseFloat(e.target.value) || 0 })}
                    placeholder="e.g. 1420.00"
                    className="w-full pl-8 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                {errors.revised_cost_crore && <p className="text-xs text-rose-500 font-mono">{errors.revised_cost_crore}</p>}
              </div>

              <div className="sm:col-span-2 p-3.5 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-500 dark:text-slate-400">Calculated Cost Escalation Delta:</span>
                <span className={`font-bold ${formData.revised_cost_crore > formData.original_cost_crore ? 'text-amber-500' : 'text-emerald-500'}`}>
                  {formData.revised_cost_crore > formData.original_cost_crore
                    ? `+₹${(formData.revised_cost_crore - formData.original_cost_crore).toFixed(2)} Cr (+${(((formData.revised_cost_crore - formData.original_cost_crore) / formData.original_cost_crore) * 100).toFixed(1)}%)`
                    : 'Nominal Baseline (0.0%)'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: SCHEDULE INFORMATION */}
        {step === 3 && (
          <div className="space-y-5 animate-in fade-in duration-200">
            <div className="border-b border-slate-200 dark:border-white/10 pb-3">
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Phase 03
              </span>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Schedule & Commissioning Milestones
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Specify project sanction and target Date of Commissioning (DOC) in YYYY-MM format.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Approval / Start Date <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM (e.g. 2023-06)"
                  value={formData.approval_start_date}
                  onChange={(e) => setFormData({ ...formData, approval_start_date: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                {errors.approval_start_date && <p className="text-xs text-rose-500 font-mono">{errors.approval_start_date}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Original Target DOC <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM (e.g. 2026-12)"
                  value={formData.original_completion_date}
                  onChange={(e) => setFormData({ ...formData, original_completion_date: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                {errors.original_completion_date && <p className="text-xs text-rose-500 font-mono">{errors.original_completion_date}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Revised DOC (Optional)
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM (or leave empty)"
                  value={formData.revised_completion_date || ''}
                  onChange={(e) => setFormData({ ...formData, revised_completion_date: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                {errors.revised_completion_date && <p className="text-xs text-rose-500 font-mono">{errors.revised_completion_date}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: PROGRESS INFORMATION */}
        {step === 4 && (
          <div className="space-y-5 animate-in fade-in duration-200">
            <div className="border-b border-slate-200 dark:border-white/10 pb-3">
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Phase 04
              </span>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Physical Progress & Capital Burn
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Execution telemetry required to evaluate progress velocity drag and divergence stress.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                    Physical Progress (%) <span className="text-rose-500">*</span>
                  </label>
                  <span className="text-xs font-mono font-bold text-cyan-600 dark:text-cyan-400">
                    {formData.physical_progress_percent}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="0.5"
                  value={formData.physical_progress_percent}
                  onChange={(e) => setFormData({ ...formData, physical_progress_percent: parseFloat(e.target.value) || 0 })}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={formData.physical_progress_percent}
                  onChange={(e) => setFormData({ ...formData, physical_progress_percent: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                {errors.physical_progress_percent && <p className="text-xs text-rose-500 font-mono">{errors.physical_progress_percent}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-300">
                  Cumulative Expenditure (₹ Crore)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm font-mono font-bold">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.cumulative_expenditure_crore || ''}
                    onChange={(e) => setFormData({ ...formData, cumulative_expenditure_crore: parseFloat(e.target.value) || 0 })}
                    placeholder="e.g. 620.00"
                    className="w-full pl-8 pr-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-300 dark:border-white/10 text-slate-900 dark:text-white text-sm font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                {errors.cumulative_expenditure_crore && <p className="text-xs text-rose-500 font-mono">{errors.cumulative_expenditure_crore}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Step 5: STATUS & CONFIRMATION */}
        {step === 5 && (
          <div className="space-y-5 animate-in fade-in duration-200">
            <div className="border-b border-slate-200 dark:border-white/10 pb-3">
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-600 dark:text-cyan-400 font-bold">
                Phase 05
              </span>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Execution Status & Final Review
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Confirm telemetry parameters before dispatching to the PAIMANA ML Risk Inference Engine.
              </p>
            </div>

            {/* Completed Toggle */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-slate-900 dark:text-white block">
                  Has this project achieved 100% completion?
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Select &lsquo;Yes&rsquo; if terminal commissioning handover has formally concluded.
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, is_completed: false })}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                    !formData.is_completed
                      ? 'bg-cyan-500 text-slate-950 shadow-sm'
                      : 'bg-slate-200 dark:bg-white/5 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  No (Ongoing)
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, is_completed: true, physical_progress_percent: 100 })}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                    formData.is_completed
                      ? 'bg-emerald-500 text-slate-950 shadow-sm'
                      : 'bg-slate-200 dark:bg-white/5 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  Yes (Completed)
                </button>
              </div>
            </div>

            {/* Assessment Payload Preview Table */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200 dark:border-white/10 space-y-2 text-xs font-mono">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider pb-1 border-b border-slate-200 dark:border-white/10">
                Inference Feature Vector Summary
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-600 dark:text-slate-300">
                <div>Project ID: <strong className="text-slate-900 dark:text-white">{formData.project_id}</strong></div>
                <div>Agency: <strong className="text-slate-900 dark:text-white">{formData.agency}</strong></div>
                <div>Approved Cost: <strong className="text-slate-900 dark:text-white">₹{formData.original_cost_crore} Cr</strong></div>
                <div>Revised Cost: <strong className="text-slate-900 dark:text-white">₹{formData.revised_cost_crore} Cr</strong></div>
                <div>Sanction Month: <strong className="text-slate-900 dark:text-white">{formData.approval_start_date}</strong></div>
                <div>Target Horizon: <strong className="text-slate-900 dark:text-white">{formData.revised_completion_date || formData.original_completion_date}</strong></div>
                <div>Physical Progress: <strong className="text-cyan-500">{formData.physical_progress_percent}%</strong></div>
                <div>State: <strong className="text-slate-900 dark:text-white">{formData.state}</strong></div>
              </div>
            </div>
          </div>
        )}

        {/* Wizard Controls */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-white/10">
          <div>
            {step > 1 ? (
              <button
                type="button"
                onClick={handlePrev}
                disabled={isLoading}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 dark:border-white/10 text-xs font-mono font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors disabled:opacity-50"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
            ) : <div />}
          </div>

          <div>
            {step < 5 ? (
              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-mono font-bold tracking-wide shadow-md shadow-cyan-500/20 transition-all duration-150"
              >
                <span>Continue to {stepsList[step]?.label}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-400 hover:from-cyan-400 hover:to-sky-300 text-slate-950 font-mono font-bold text-sm tracking-wider shadow-lg shadow-cyan-500/25 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                    <span>ANALYZING PROJECT...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 fill-current" />
                    <span>GENERATE PROJECT INTELLIGENCE</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
