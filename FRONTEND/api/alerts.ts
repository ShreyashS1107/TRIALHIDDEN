import { SystemAlert, AnomalyItem } from './types';

export async function getSystemAlerts(filterSource?: string): Promise<SystemAlert[]> {
  let alerts: SystemAlert[] = [];
  if (typeof window !== 'undefined') {
    const res = await fetch('/data/system_alerts.json');
    if (!res.ok) return [];
    alerts = await res.json();
  } else {
    try {
      const fs = require('fs');
      const path = require('path');
      const file = path.join(process.cwd(), 'public', 'data', 'system_alerts.json');
      alerts = JSON.parse(fs.readFileSync(file, 'utf-8'));
    } catch (e) {
      alerts = [];
    }
  }

  if (filterSource && filterSource !== 'ALL') {
    return alerts.filter((a) => a.source === filterSource);
  }
  return alerts;
}

export async function getAnomaliesList(): Promise<AnomalyItem[]> {
  if (typeof window !== 'undefined') {
    const res = await fetch('/data/anomalies.json');
    if (!res.ok) return [];
    return res.json();
  }
  try {
    const fs = require('fs');
    const path = require('path');
    const file = path.join(process.cwd(), 'public', 'data', 'anomalies.json');
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (e) {
    return [];
  }
}
