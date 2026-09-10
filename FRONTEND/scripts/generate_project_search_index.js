const fs = require('fs');
const path = require('path');

const CSV_FILE = path.join(__dirname, '../../TRIALHIDDEN/data/paimana_master_dataset.csv');
const RISK_CSV = path.join(__dirname, '../../TRIALHIDDEN/ml/risk_engine/integrated_risk_scores.csv');
const OUT_INDEX = path.join(__dirname, '../public/data/projects_search_index.json');
const OUT_HISTORY = path.join(__dirname, '../public/data/projects_longitudinal.json');

// Accurate CSV line parser that respects quotes
function parseCsvLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current.trim());
  return values;
}

// Known standard Indian states to clean noisy state fields
const KNOWN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
  'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
  'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
  'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Multi State'
];

function cleanState(raw) {
  if (!raw) return 'Central / Multi-State';
  const upper = raw.toUpperCase();
  for (const s of KNOWN_STATES) {
    if (upper.includes(s.toUpperCase())) return s;
  }
  const cleaned = raw.replace(/^[0-9,.\s]+/, '').replace(/(COAL|CIVIL AVIATION|RAILWAYS|ROAD|POWER).*$/i, '').trim();
  return cleaned || 'Central / Multi-State';
}

function cleanAgency(raw) {
  if (!raw) return 'GOI / Central';
  return raw.replace(/\[.*?\]/g, '').trim();
}

console.log('Loading risk scores from', RISK_CSV);
const riskHistoryMap = new Map(); // pid -> array of monthly risk snapshots
if (fs.existsSync(RISK_CSV)) {
  const riskLines = fs.readFileSync(RISK_CSV, 'utf8').split('\n');
  for (let i = 1; i < riskLines.length; i++) {
    const line = riskLines[i].trim();
    if (!line) continue;
    const parts = parseCsvLine(line);
    const pid = parts[0];
    if (!pid) continue;
    
    // Header: project_id,project_name,agency,state,prediction_month,schedule_delay_risk,cost_overrun_risk,schedule_revision_risk,integrated_risk_equal,integrated_risk_weighted,selected_integrated_risk,risk_band,schedule_contribution,cost_contribution,schedule_revision_contribution,dominant_component
    const month = parts[4];
    const delayRisk = parseFloat(parts[5]) || 0;
    const costRisk = parseFloat(parts[6]) || 0;
    const revRisk = parseFloat(parts[7]) || 0;
    const integratedRisk = parseFloat(parts[10]) || 0;
    let band = (parts[11] || 'LOW').toUpperCase();
    if (band === 'MODERATE') band = 'MEDIUM';
    const schedContrib = parseFloat(parts[12]) || 0;
    const costContrib = parseFloat(parts[13]) || 0;
    const revContrib = parseFloat(parts[14]) || 0;
    const dominant = parts[15] || (delayRisk > costRisk ? 'Schedule Delay' : 'Cost Escalation');

    if (!riskHistoryMap.has(pid)) {
      riskHistoryMap.set(pid, []);
    }

    riskHistoryMap.get(pid).push({
      month,
      schedule_delay_risk: Math.round(delayRisk * 1000) / 1000,
      cost_overrun_risk: Math.round(costRisk * 1000) / 1000,
      schedule_revision_risk: Math.round(revRisk * 1000) / 1000,
      selected_integrated_risk: Math.round(integratedRisk * 1000) / 1000,
      risk_band: band,
      schedule_contribution: Math.round(schedContrib * 1000) / 1000,
      cost_contribution: Math.round(costContrib * 1000) / 1000,
      schedule_revision_contribution: Math.round(revContrib * 1000) / 1000,
      dominant_component: dominant
    });
  }
}
console.log(`Loaded risk scores for ${riskHistoryMap.size} projects.`);

console.log('Reading longitudinal records from', CSV_FILE);
const csvContent = fs.readFileSync(CSV_FILE, 'utf8');
const lines = csvContent.split('\n');

const projectMap = new Map();
const projectHistory = new Map();

for (let i = 1; i < lines.length; i++) {
  const line = lines[i].trim();
  if (!line) continue;

  const row = parseCsvLine(line);
  if (row.length < 13) continue;

  // Header: project_id,project_name,agency,legacy_ocms_code,state,approval_start_date,original_completion_date,revised_completion_date,original_cost_crore,revised_cost_crore,cumulative_expenditure_crore,physical_progress_percent,report_month,source_file,source_table
  const [
    project_id, project_name, agency, legacy_ocms_code, state,
    approval_start_date, original_completion_date, revised_completion_date,
    original_cost_crore, revised_cost_crore, cumulative_expenditure_crore,
    physical_progress_percent, report_month, source_file, source_table
  ] = row;

  if (!project_id) continue;

  const origCost = parseFloat(original_cost_crore) || 0;
  const revCost = parseFloat(revised_cost_crore) || origCost;
  const spent = parseFloat(cumulative_expenditure_crore) || 0;
  const progress = parseFloat(physical_progress_percent) || 0;

  // Record historical snapshot
  if (!projectHistory.has(project_id)) {
    projectHistory.set(project_id, []);
  }

  projectHistory.get(project_id).push({
    report_month,
    original_cost_crore: origCost,
    revised_cost_crore: revCost,
    cumulative_expenditure_crore: spent,
    physical_progress_percent: progress,
    original_completion_date: original_completion_date || '',
    revised_completion_date: revised_completion_date || '',
    source_file: source_file || 'FlashReport.pdf',
    source_table: source_table || 'Table 6: All Ongoing Projects'
  });

  // Track latest state
  const existing = projectMap.get(project_id);
  const isLater = !existing || (report_month && report_month >= existing.last_reported_month);

  if (isLater) {
    projectMap.set(project_id, {
      project_id,
      project_name: project_name.replace(/^"|"$/g, '').trim(),
      agency: cleanAgency(agency),
      legacy_ocms_code: legacy_ocms_code || '',
      state: cleanState(state),
      original_cost_crore: origCost,
      revised_cost_crore: revCost,
      cumulative_expenditure_crore: spent,
      original_completion_date: original_completion_date || '',
      revised_completion_date: revised_completion_date || '',
      physical_progress_percent: progress,
      last_reported_month: report_month,
      approval_start_date: approval_start_date || '',
      source_file: source_file || 'FlashReport.pdf',
      source_table: source_table || 'Table 6: All Ongoing Projects'
    });
  }
}

console.log(`Parsed ${projectMap.size} unique canonical projects.`);

// Merge risk scores, compute trends, variance, and build final indexes
const searchIndex = [];
const historyExport = {};

for (const [pid, proj] of projectMap.entries()) {
  const history = projectHistory.get(pid) || [];
  history.sort((a, b) => (a.report_month > b.report_month ? 1 : -1));

  // Risk snapshots sorted chronologically
  const riskList = riskHistoryMap.get(pid) || [];
  riskList.sort((a, b) => (a.month > b.month ? 1 : -1));

  const hasML = riskList.length > 0;
  const latestRisk = hasML ? riskList[riskList.length - 1] : null;
  const prevRisk = hasML && riskList.length > 1 ? riskList[riskList.length - 2] : null;

  let riskTrend = 'stable';
  if (latestRisk && prevRisk) {
    const diff = latestRisk.selected_integrated_risk - prevRisk.selected_integrated_risk;
    if (diff > 0.02) riskTrend = 'increasing';
    else if (diff < -0.02) riskTrend = 'decreasing';
  }

  // Cost variance %
  const deltaCost = Math.max(0, proj.revised_cost_crore - proj.original_cost_crore);
  const costVariancePct = proj.original_cost_crore > 0
    ? Math.round(((proj.revised_cost_crore - proj.original_cost_crore) / proj.original_cost_crore) * 1000) / 10
    : 0;

  // Has explicit revision recorded
  const hasRevision = Boolean(
    proj.revised_completion_date &&
    proj.revised_completion_date !== proj.original_completion_date &&
    proj.revised_completion_date !== ''
  );

  const finalRecord = {
    ...proj,
    cost_escalation_crore: Math.round(deltaCost * 100) / 100,
    cost_variance_percent: costVariancePct,
    has_revision: hasRevision,
    total_snapshots: history.length,
    has_ml_telemetry: hasML,
    risk_band: latestRisk ? latestRisk.risk_band : 'NOT_ASSESSED',
    selected_integrated_risk: latestRisk ? latestRisk.selected_integrated_risk : null,
    previous_risk: prevRisk ? prevRisk.selected_integrated_risk : null,
    risk_trend: riskTrend,
    dominant_component: latestRisk ? latestRisk.dominant_component : 'Baseline Telemetry',
    schedule_delay_risk: latestRisk ? latestRisk.schedule_delay_risk : null,
    cost_overrun_risk: latestRisk ? latestRisk.cost_overrun_risk : null,
    schedule_revision_risk: latestRisk ? latestRisk.schedule_revision_risk : null,
    schedule_contribution: latestRisk ? latestRisk.schedule_contribution : null,
    cost_contribution: latestRisk ? latestRisk.cost_contribution : null,
    schedule_revision_contribution: latestRisk ? latestRisk.schedule_revision_contribution : null
  };

  searchIndex.push(finalRecord);

  // Combine monthly project history with matching risk for that month
  const enrichedHistory = history.map(snap => {
    const matchedRisk = riskList.find(r => r.month === snap.report_month);
    return {
      ...snap,
      risk: matchedRisk || null
    };
  });

  historyExport[pid] = {
    timeline: enrichedHistory,
    risk_trajectory: riskList
  };
}

// Sort alphabetically by project ID
searchIndex.sort((a, b) => a.project_id.localeCompare(b.project_id, undefined, { numeric: true }));

// Write search index
fs.writeFileSync(OUT_INDEX, JSON.stringify(searchIndex, null, 2));
console.log(`Wrote ${searchIndex.length} projects to ${OUT_INDEX}`);

// Write enriched history and risk trajectory
fs.writeFileSync(OUT_HISTORY, JSON.stringify(historyExport));
console.log(`Wrote history for ${Object.keys(historyExport).length} projects to ${OUT_HISTORY}`);

// Verify Kadapa Airport 612786
const kadapa = searchIndex.find(p => p.project_id === '612786');
console.log('\nVerification - Project 612786 (Kadapa Airport):', {
  project_id: kadapa.project_id,
  name: kadapa.project_name,
  cost_variance_percent: kadapa.cost_variance_percent,
  has_revision: kadapa.has_revision,
  original_completion_date: kadapa.original_completion_date,
  revised_completion_date: kadapa.revised_completion_date,
  source_file: kadapa.source_file,
  source_table: kadapa.source_table,
  risk_band: kadapa.risk_band,
  selected_integrated_risk: kadapa.selected_integrated_risk,
  risk_trend: kadapa.risk_trend,
  history_count: historyExport['612786']?.timeline?.length,
  risk_count: historyExport['612786']?.risk_trajectory?.length
});
