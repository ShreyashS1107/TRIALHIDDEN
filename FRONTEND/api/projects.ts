import { ProjectDetail, NationalSummary } from './types';

export async function getNationalSummary(): Promise<NationalSummary> {
  if (typeof window !== 'undefined') {
    const res = await fetch('/data/paimana_summary.json');
    if (!res.ok) throw new Error('Failed to load summary');
    return res.json();
  }
  // Server-side dynamic require
  try {
    const fs = require('fs');
    const path = require('path');
    const file = path.join(process.cwd(), 'public', 'data', 'paimana_summary.json');
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (e) {
    return {} as NationalSummary;
  }
}

export async function getFeaturedProjects(): Promise<ProjectDetail[]> {
  if (typeof window !== 'undefined') {
    const res = await fetch('/data/featured_projects.json');
    if (!res.ok) throw new Error('Failed to load projects');
    return res.json();
  }
  try {
    const fs = require('fs');
    const path = require('path');
    const file = path.join(process.cwd(), 'public', 'data', 'featured_projects.json');
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (e) {
    return [];
  }
}

export async function getProjectById(projectId: string): Promise<ProjectDetail | null> {
  const projects = await getFeaturedProjects();
  return projects.find((p) => p.project_id === projectId) || null;
}
