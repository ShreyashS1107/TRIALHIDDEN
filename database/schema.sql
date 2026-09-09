-- ============================================================================
-- 1. EXTENSIONS & ENUM TYPES
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fast full-text / trigram fuzzy search

CREATE TYPE risk_band_enum AS ENUM ('LOW', 'MODERATE', 'HIGH', 'VERY_HIGH');
CREATE TYPE dominant_component_enum AS ENUM ('Schedule Delay', 'Cost Overrun', 'Schedule Revision');
CREATE TYPE alert_severity_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE alert_source_enum AS ENUM ('ML_ENGINE', 'RULE_ENGINE', 'EXECUTION_SURVEILLANCE', 'PREDICTIVE_ML');
CREATE TYPE alert_status_enum AS ENUM ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED');
CREATE TYPE user_role_enum AS ENUM ('MOSPI_ADMIN', 'NODAL_OFFICER', 'PUBLIC_VIEWER');

-- ============================================================================
-- 2. CANONICAL PROJECTS MASTER TABLE
-- ============================================================================
-- Holds immutable or slowly-changing project identity attributes across all reporting months.
CREATE TYPE esi_tier_enum AS ENUM ('NOMINAL', 'WATCH', 'ATTENTION', 'HIGH_PRIORITY');
CREATE TYPE dominant_stressor_enum AS ENUM (
    'Progress Velocity Collapse',
    'Physical Progress Stagnation',
    'Expenditure Divergence',
    'Schedule Slippage Debt',
    'Reporting Friction'
);
CREATE TYPE prescriptive_action_enum AS ENUM (
    'SITE_OBSTACLE_AUDIT',
    'FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT',
    'RESOURCE_MOBILIZATION_DIRECTIVE',
    'CRITICAL_PATH_RECALIBRATION',
    'DATA_COMPLIANCE_DIRECTIVE',
    'INTER_MINISTERIAL_COMMITTEE_ESCALATION'
);

CREATE TABLE projects (
    project_id VARCHAR(32) PRIMARY KEY,              -- Canonical 6-digit PAIMANA ID (e.g. '105236', '612786')
    project_name TEXT,                               -- Official full infrastructure project title
    agency TEXT NOT NULL,                            -- Implementing CPSU / Agency (e.g. 'NHAI', 'MoRTH', 'NTPC')
    state TEXT NOT NULL,                             -- State, UT, or Multi-State location
    legacy_ocms_code VARCHAR(32),                    -- Cross-referenced 8-character OCMS code (e.g. 'N24001476')
    approval_start_date VARCHAR(7),                  -- Sanction approval date in ISO YYYY-MM (e.g. '2021-09')
    original_completion_date VARCHAR(7),             -- Sanctioned original DOC in ISO YYYY-MM (e.g. '2022-09')
    original_cost_crore NUMERIC(14, 2),              -- Sanctioned capital budget in ₹ Crore
    is_active BOOLEAN NOT NULL DEFAULT TRUE,         -- Active ongoing status flag
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_projects_agency ON projects (agency);
CREATE INDEX idx_projects_state ON projects (state);
CREATE INDEX idx_projects_legacy_code ON projects (legacy_ocms_code) WHERE legacy_ocms_code IS NOT NULL;
CREATE INDEX idx_projects_name_trgm ON projects USING gin (project_name gin_trgm_ops);

-- ============================================================================
-- 3. MONTHLY LONGITUDINAL SNAPSHOTS TABLE (LAYER A RAW FACTS)
-- ============================================================================
-- Stores monthly time-series records (21,555 rows). One row per project per report_month.
CREATE TABLE monthly_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(32) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    report_month VARCHAR(7) NOT NULL,                -- Snapshot epoch in ISO YYYY-MM (e.g. '2025-04')
    revised_completion_date VARCHAR(7),              -- Current anticipated DOC in YYYY-MM (Null if unrevised)
    revised_cost_crore NUMERIC(14, 2),               -- Current anticipated cost in ₹ Crore
    cumulative_expenditure_crore NUMERIC(14, 2),     -- Total expenditure to date in ₹ Crore
    physical_progress_percent NUMERIC(5, 2),         -- Cumulative physical completion percentage [0.00, 100.00]
    source_file VARCHAR(128) NOT NULL,               -- Source Flash Report PDF filename
    source_table VARCHAR(64) NOT NULL,               -- e.g. 'Table 6: All Ongoing Projects'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_project_month UNIQUE (project_id, report_month),
    CONSTRAINT chk_progress_bounds CHECK (physical_progress_percent >= 0.0 AND physical_progress_percent <= 100.0),
    CONSTRAINT chk_costs_positive CHECK (revised_cost_crore >= 0.0 AND cumulative_expenditure_crore >= 0.0)
);

CREATE INDEX idx_snapshots_report_month ON monthly_snapshots (report_month);
CREATE INDEX idx_snapshots_project_month ON monthly_snapshots (project_id, report_month);

-- ============================================================================
-- 4. MACHINE LEARNING RISK SCORES TABLE (LAYER C PREDICTIONS)
-- ============================================================================
-- Stores multi-dimensional risk scores (15,769 pre-computed rows across 12 epochs).
CREATE TABLE ml_risk_scores (
    score_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(32) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    report_month VARCHAR(7) NOT NULL,                -- Prediction snapshot epoch (YYYY-MM)
    schedule_delay_risk NUMERIC(6, 4) NOT NULL,      -- Platt-calibrated probability in [0.0000, 1.0000]
    cost_overrun_risk NUMERIC(6, 4) NOT NULL,        -- Continuous model score in [0.0000, 1.0000]
    schedule_revision_risk NUMERIC(6, 4) NOT NULL,   -- Administrative warning score in [0.0000, 1.0000]
    selected_integrated_risk NUMERIC(6, 4) NOT NULL, -- Weighted multi-dimensional index in [0.0000, 1.0000]
    risk_band risk_band_enum NOT NULL,               -- 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH'
    dominant_component dominant_component_enum NOT NULL, -- 'Schedule Delay', 'Cost Overrun', 'Schedule Revision'
    schedule_contribution NUMERIC(6, 4) NOT NULL,    -- 0.50 * schedule_delay_risk
    cost_contribution NUMERIC(6, 4) NOT NULL,        -- 0.35 * cost_overrun_risk
    schedule_revision_contribution NUMERIC(6, 4) NOT NULL, -- 0.15 * schedule_revision_risk
    model_version VARCHAR(32) NOT NULL DEFAULT 'v1.0.0-rf02-calibrated',
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_ml_project_month UNIQUE (project_id, report_month)
);

CREATE INDEX idx_ml_scores_month_band ON ml_risk_scores (report_month, risk_band);
CREATE INDEX idx_ml_scores_integrated ON ml_risk_scores (report_month, selected_integrated_risk DESC);
CREATE INDEX idx_ml_scores_dominant ON ml_risk_scores (report_month, dominant_component);

-- ============================================================================
-- 5. COMPLETED & NEWLY ADDED PROJECTS TABLES (AUXILIARY TABLES)
-- ============================================================================
CREATE TABLE completed_projects (
    project_id VARCHAR(32) PRIMARY KEY,
    project_name TEXT NOT NULL,
    agency TEXT NOT NULL,
    state TEXT NOT NULL,
    original_cost_crore NUMERIC(14, 2),
    actual_cost_crore NUMERIC(14, 2),
    cumulative_expenditure_crore NUMERIC(14, 2),
    actual_completion_date VARCHAR(7),                -- ISO YYYY-MM
    report_month VARCHAR(7) NOT NULL,
    source_file VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE newly_added_projects (
    intake_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(32) NOT NULL,
    project_name TEXT NOT NULL,
    agency TEXT NOT NULL,
    state TEXT NOT NULL,
    original_cost_crore NUMERIC(14, 2),
    approval_start_date VARCHAR(7),
    original_completion_date VARCHAR(7),
    report_month VARCHAR(7) NOT NULL,
    source_file VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 6. DATA QUALITY & ANOMALIES AUDIT LOG (THE 1,868 ROWS POLICY)
-- ============================================================================
CREATE TABLE data_anomalies_log (
    anomaly_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(32) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    report_month VARCHAR(7) NOT NULL,
    flag_code VARCHAR(64) NOT NULL,                  -- e.g. 'PROGRESS_DROP_GT_25', 'EXPENDITURE_DROP_GT_50'
    severity alert_severity_enum NOT NULL DEFAULT 'MEDIUM',
    metric_value NUMERIC(14, 2),
    prior_value NUMERIC(14, 2),
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_anomalies_project_month ON data_anomalies_log (project_id, report_month);

-- ============================================================================
-- 7. SYSTEM ALERTS TABLE
-- ============================================================================
CREATE TABLE system_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(32) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    report_month VARCHAR(7) NOT NULL,
    alert_code VARCHAR(64) NOT NULL,                 -- e.g. 'ML_CRITICAL_RISK', 'RULE_CHRONIC_STAGNANT'
    severity alert_severity_enum NOT NULL,
    alert_source alert_source_enum NOT NULL,
    message TEXT NOT NULL,
    status alert_status_enum NOT NULL DEFAULT 'ACTIVE',
    acknowledged_by VARCHAR(64),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_alert_project_code_month UNIQUE (project_id, report_month, alert_code)
);

CREATE INDEX idx_alerts_month_status ON system_alerts (report_month, status, severity);

-- ============================================================================
-- 8. USERS & RBAC TABLE
-- ============================================================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'PUBLIC_VIEWER',
    agency_affiliation VARCHAR(64),                  -- Optional filtering by agency
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 9. DETERMINISTIC LAYER B DERIVED ANALYTICS ENGINE (SQL VIEWS)
-- ============================================================================
CREATE OR REPLACE VIEW v_project_monthly_dossier AS
WITH snapshots_with_lag AS (
    SELECT 
        s.snapshot_id,
        s.project_id,
        s.report_month,
        s.revised_completion_date,
        s.revised_cost_crore,
        s.cumulative_expenditure_crore,
        s.physical_progress_percent,
        s.source_file,
        s.source_table,
        p.project_name,
        p.agency,
        p.state,
        p.legacy_ocms_code,
        p.approval_start_date,
        p.original_completion_date,
        p.original_cost_crore,
        
        LAG(s.physical_progress_percent, 1) OVER (
            PARTITION BY s.project_id ORDER BY s.report_month ASC
        ) AS prev_prog_1m,
        LAG(s.physical_progress_percent, 2) OVER (
            PARTITION BY s.project_id ORDER BY s.report_month ASC
        ) AS prev_prog_2m,
        LAG(s.physical_progress_percent, 3) OVER (
            PARTITION BY s.project_id ORDER BY s.report_month ASC
        ) AS prev_prog_3m,
        LAG(s.cumulative_expenditure_crore, 1) OVER (
            PARTITION BY s.project_id ORDER BY s.report_month ASC
        ) AS prev_exp_1m
    FROM monthly_snapshots s
    JOIN projects p ON s.project_id = p.project_id
),
snapshots_with_streak AS (
    SELECT 
        *,
        SUM(CASE 
            WHEN prev_prog_1m IS NOT NULL AND physical_progress_percent = prev_prog_1m THEN 0 
            ELSE 1 
        END) OVER (PARTITION BY project_id ORDER BY report_month ASC) AS progress_streak_id
    FROM snapshots_with_lag
),
ranked_snapshots AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY project_id, progress_streak_id ORDER BY report_month ASC) - 1 AS months_since_last_progress_increase
    FROM snapshots_with_streak
)
SELECT 
    r.snapshot_id,
    r.project_id,
    r.report_month,
    r.revised_completion_date,
    r.revised_cost_crore,
    r.cumulative_expenditure_crore,
    r.physical_progress_percent,
    r.source_file,
    r.source_table,
    r.project_name,
    r.agency,
    r.state,
    r.legacy_ocms_code,
    r.approval_start_date,
    r.original_completion_date,
    r.original_cost_crore,
    r.prev_prog_1m,
    r.prev_prog_3m,
    r.prev_exp_1m,
    r.months_since_last_progress_increase,
    
    (r.revised_cost_crore - r.original_cost_crore) AS cost_escalation_crore,
    CASE WHEN r.original_cost_crore > 0 THEN ROUND(((r.revised_cost_crore - r.original_cost_crore) / r.original_cost_crore * 100.0), 2) ELSE 0.0 END AS cost_escalation_percent,
    CASE WHEN r.original_cost_crore > 0 THEN ROUND((r.cumulative_expenditure_crore / r.original_cost_crore * 100.0), 2) ELSE 0.0 END AS expenditure_ratio_percent,
    (100.0 - r.physical_progress_percent) AS remaining_physical_progress,
    CASE WHEN r.revised_completion_date IS NOT NULL THEN ((CAST(SUBSTRING(r.revised_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT)) * 12 + (CAST(SUBSTRING(r.revised_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT))) ELSE 0.0 END AS schedule_slippage_months,
    ((CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.report_month, 1, 4) AS INT)) * 12 + (CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.report_month, 6, 2) AS INT))) AS months_to_original_doc,
    CASE WHEN r.prev_prog_1m IS NOT NULL THEN (r.physical_progress_percent - r.prev_prog_1m) ELSE NULL END AS progress_velocity_1m,
    CASE WHEN r.prev_prog_3m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_3m) / 3.0), 2) WHEN r.prev_prog_2m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_2m) / 2.0), 2) WHEN r.prev_prog_1m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_1m) / 1.0), 2) ELSE NULL END AS progress_velocity_3m,
    CASE WHEN r.prev_prog_3m IS NOT NULL AND (r.physical_progress_percent - r.prev_prog_3m = 0.0) THEN 1 ELSE 0 END AS stagnant_3m_flag,
    CASE WHEN r.original_cost_crore > 0 THEN ROUND(((r.cumulative_expenditure_crore / r.original_cost_crore * 100.0) - r.physical_progress_percent), 2) ELSE 0.0 END AS expenditure_progress_divergence,
    ((CAST(SUBSTRING(r.report_month, 1, 4) AS INT) - CAST(SUBSTRING(r.approval_start_date, 1, 4) AS INT)) * 12 + (CAST(SUBSTRING(r.report_month, 6, 2) AS INT) - CAST(SUBSTRING(r.approval_start_date, 6, 2) AS INT))) AS project_age_months,
    ((CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.approval_start_date, 1, 4) AS INT)) * 12 + (CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.approval_start_date, 6, 2) AS INT))) AS planned_duration_months,
    
    m.schedule_delay_risk,
    m.cost_overrun_risk,
    m.schedule_revision_risk,
    m.selected_integrated_risk,
    m.risk_band,
    m.dominant_component,
    m.schedule_contribution,
    m.cost_contribution,
    m.schedule_revision_contribution,
    CASE WHEN m.selected_integrated_risk > 0 THEN ROUND((m.schedule_contribution / m.selected_integrated_risk * 100.0), 2) ELSE 0.0 END AS schedule_contrib_pct,
    CASE WHEN m.selected_integrated_risk > 0 THEN ROUND((m.cost_contribution / m.selected_integrated_risk * 100.0), 2) ELSE 0.0 END AS cost_contrib_pct,
    CASE WHEN m.selected_integrated_risk > 0 THEN ROUND((m.schedule_revision_contribution / m.selected_integrated_risk * 100.0), 2) ELSE 0.0 END AS schedule_rev_contrib_pct,
    
    e.execution_stress_index,
    e.s_stag,
    e.s_vel,
    e.s_sched,
    e.s_div,
    e.s_rep,
    e.flag_stag,
    e.flag_vel,
    e.flag_sched,
    e.flag_div,
    e.flag_rep,
    e.total_stress_flags,
    e.esi_tier,
    e.dominant_stressor,
    e.suggested_action,
    e.execution_index_version

FROM ranked_snapshots r
LEFT JOIN ml_risk_scores m ON r.project_id = m.project_id AND r.report_month = m.report_month
LEFT JOIN execution_stress_scores e ON r.project_id = e.project_id AND r.report_month = e.report_month;
