'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/layout/Navbar';
import HeroSection from '@/components/sections/HeroSection';
import Section02_DataFoundation from '@/components/sections/Section02_DataFoundation';
import Section04_RiskPrediction from '@/components/sections/Section04_RiskPrediction';
import Section07_ExplainableAI from '@/components/sections/Section07_ExplainableAI';
import Section08_EarlyWarningCenter from '@/components/sections/Section08_EarlyWarningCenter';
import Section09_Prioritization from '@/components/sections/Section09_Prioritization';
import Section11_LongitudinalTimeline from '@/components/sections/Section11_LongitudinalTimeline';
import Section12_DataTrust from '@/components/sections/Section12_DataTrust';
import Section13_AnomalyDetection from '@/components/sections/Section13_AnomalyDetection';
import Section14_WhatIfSimulation from '@/components/sections/Section14_WhatIfSimulation';
import Section15_Comparison from '@/components/sections/Section15_Comparison';
import Section16_AIAssistant from '@/components/sections/Section16_AIAssistant';
import Section17_SecondVideo from '@/components/sections/Section17_SecondVideo';
import Section18_FinalCTA from '@/components/sections/Section18_FinalCTA';

import { ProjectDetail, NationalSummary, SystemAlert, AnomalyItem } from '@/lib/api/types';

export default function HomePage() {
  const [projects, setProjects] = useState<ProjectDetail[]>([]);
  const [summary, setSummary] = useState<NationalSummary | null>(null);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  
  const [assistantOpen, setAssistantOpen] = useState(false);

  useEffect(() => {
    // Fetch pre-computed authentic MoSPI datasets
    fetch('/data/featured_projects.json')
      .then((res) => res.json())
      .then((data: ProjectDetail[]) => {
        setProjects(data);
      })
      .catch((err) => console.error('Error loading projects:', err));

    fetch('/data/paimana_summary.json')
      .then((res) => res.json())
      .then((data: NationalSummary) => setSummary(data))
      .catch((err) => console.error('Error loading summary:', err));

    fetch('/data/system_alerts.json')
      .then((res) => res.json())
      .then((data: SystemAlert[]) => setAlerts(data))
      .catch((err) => console.error('Error loading alerts:', err));

    fetch('/data/anomalies.json')
      .then((res) => res.json())
      .then((data: AnomalyItem[]) => setAnomalies(data))
      .catch((err) => console.error('Error loading anomalies:', err));
  }, []);

  return (
    <main className="relative min-h-screen bg-navy-950 text-slate-100 overflow-x-hidden">
      {/* 1. Global Translucent Glass Navigation */}
      <Navbar onOpenAssistant={() => setAssistantOpen(true)} />

      {/* 2. Hero Section (SIH_VIDEO_1_final.mp4, Digital Twin Particle Overlays) */}
      <HeroSection />

      {/* 3. Section 02: Data Foundation (15 Monthly Stacked Layers, 21,555 Records) */}
      <Section02_DataFoundation summary={summary} />

      {/* 4. Section 04: Risk Prediction (3D Trajectory Curves, Dual Pillars) */}
      <Section04_RiskPrediction summary={summary} />

      {/* 5. Section 07: Explainable AI (Feature Importance Bars, Cyan vs Amber) */}
      <Section07_ExplainableAI projects={projects} />

      {/* 6. Section 08: Early Warning Center (Tri-Source Alerts Feed) */}
      <Section08_EarlyWarningCenter
        alerts={alerts}
      />

      {/* 7. Section 09: Project Prioritization (Ranked Intervention Matrix 01, 02, 03) */}
      <Section09_Prioritization
        projects={projects}
      />

      {/* 8. Section 11: Longitudinal Project Timeline (Month-by-Month Trajectory) */}
      <Section11_LongitudinalTimeline projects={projects} />

      {/* 14. Section 12: Data Trust Layer (5 Validation Dimensions, 1,868 Rows Policy) */}
      <Section12_DataTrust summary={summary} />

      {/* 15. Section 13: Anomaly Detection (Visualizing Progress/Expenditure Collapse) */}
      <Section13_AnomalyDetection anomalies={anomalies} />

      {/* 16. Section 14: What-If Simulation (Interactive Decision Sliders, DEMO SIMULATION) */}
      <Section14_WhatIfSimulation projects={projects} />

      {/* 17. Section 15: Project Comparison (Side-by-Side Asset Benchmarking) */}
      <Section15_Comparison projects={projects} />

      {/* 18. Section 16: AI Project Assistant (Contextual Q&A Grounded in Real Data) */}
      <Section16_AIAssistant />

      {/* 19. Section 17: Second Video (SIH_VIDEO_2_final.mp4 Storytelling Transition) */}
      <Section17_SecondVideo />

      {/* 20. Section 18: Final CTA (Brand Mantra, Final Enter Intelligence Button) */}
      <Section18_FinalCTA />

      {/* Floating AI Assistant Drawer */}
      <Section16_AIAssistant
        isOpen={assistantOpen}
        onClose={() => setAssistantOpen(false)}
        isFloating={true}
      />
    </main>
  );
}
