import { ProjectSearchRecord, ProjectHistoricalRecord, ProjectRiskSnapshot, ProjectDossierData } from './types';

let cachedSearchIndex: ProjectSearchRecord[] | null = null;
let cachedHistoryData: Record<string, { timeline: ProjectHistoricalRecord[]; risk_trajectory: ProjectRiskSnapshot[] }> | null = null;

function resolveDataFile(filename: string): string | null {
  const fs = require('fs');
  const path = require('path');

  const candidates = [
    path.join(process.cwd(), 'public', 'data', filename),
    path.join(process.cwd(), 'FRONTEND', 'public', 'data', filename),
    path.join(__dirname, '../../public/data', filename),
  ];

  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return null;
}

export async function getSearchIndex(): Promise<ProjectSearchRecord[]> {
  if (cachedSearchIndex) return cachedSearchIndex;

  if (typeof window !== 'undefined') {
    try {
      const res = await fetch('/data/projects_search_index.json');
      if (!res.ok) throw new Error('Failed to load search index');
      cachedSearchIndex = await res.json();
      return cachedSearchIndex || [];
    } catch (e) {
      console.error('Client fetch error for search index:', e);
      return [];
    }
  }

  // Server-side filesystem read
  try {
    const fs = require('fs');
    const filePath = resolveDataFile('projects_search_index.json');
    if (filePath) {
      cachedSearchIndex = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      return cachedSearchIndex || [];
    }
  } catch (e) {
    console.error('Server read error for search index:', e);
  }
  return [];
}

async function getRawHistoryStore(): Promise<Record<string, any>> {
  if (cachedHistoryData) return cachedHistoryData;

  if (typeof window !== 'undefined') {
    try {
      const res = await fetch('/data/projects_longitudinal.json');
      if (!res.ok) throw new Error('Failed to load project history');
      cachedHistoryData = await res.json();
      return cachedHistoryData || {};
    } catch (e) {
      console.error('Client fetch error for history:', e);
      return {};
    }
  }

  // Server-side
  try {
    const fs = require('fs');
    const filePath = resolveDataFile('projects_longitudinal.json');
    if (filePath) {
      cachedHistoryData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      return cachedHistoryData || {};
    }
  } catch (e) {
    console.error('Server read error for history:', e);
  }
  return {};
}

export async function getProjectHistory(projectId: string): Promise<ProjectHistoricalRecord[]> {
  const store = await getRawHistoryStore();
  const entry = store[projectId];
  if (!entry) return [];
  if (Array.isArray(entry)) return entry;
  return entry.timeline || [];
}

export async function getProjectById(projectId: string): Promise<ProjectSearchRecord | null> {
  const index = await getSearchIndex();
  return index.find((p) => p.project_id === projectId || p.legacy_ocms_code === projectId) || null;
}

export async function getProjectDossier(projectId: string): Promise<ProjectDossierData | null> {
  const project = await getProjectById(projectId);
  if (!project) return null;

  const store = await getRawHistoryStore();
  const entry = store[project.project_id] || store[projectId];

  let timeline: ProjectHistoricalRecord[] = [];
  let risk_trajectory: ProjectRiskSnapshot[] = [];

  if (entry) {
    if (Array.isArray(entry)) {
      timeline = entry;
    } else {
      timeline = entry.timeline || [];
      risk_trajectory = entry.risk_trajectory || [];
    }
  }

  return {
    project,
    timeline,
    risk_trajectory
  };
}
