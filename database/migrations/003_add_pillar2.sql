-- Migration 003: Add Pillar 2 (Execution Stress Index) and update Dossier View

-- 1. Create Enums for Pillar 2
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

-- 2. Alter existing Enum for System Alerts
ALTER TYPE alert_source_enum ADD VALUE IF NOT EXISTS 'EXECUTION_SURVEILLANCE';
ALTER TYPE alert_source_enum ADD VALUE IF NOT EXISTS 'PREDICTIVE_ML';

-- 3. Create Execution Stress Scores Table
CREATE TABLE execution_stress_scores (
    project_id VARCHAR(32) NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    report_month VARCHAR(7) NOT NULL,
    s_stag NUMERIC(6, 4) NOT NULL,
    s_vel NUMERIC(6, 4) NOT NULL,
    s_div NUMERIC(6, 4) NOT NULL,
    s_sched NUMERIC(6, 4) NOT NULL,
    s_rep NUMERIC(6, 4) NOT NULL,
    flag_stag SMALLINT NOT NULL DEFAULT 0,
    flag_vel SMALLINT NOT NULL DEFAULT 0,
    flag_div SMALLINT NOT NULL DEFAULT 0,
    flag_sched SMALLINT NOT NULL DEFAULT 0,
    flag_rep SMALLINT NOT NULL DEFAULT 0,
    total_stress_flags SMALLINT NOT NULL DEFAULT 0,
    execution_stress_index NUMERIC(6, 4) NOT NULL,
    esi_tier esi_tier_enum NOT NULL,
    dominant_stressor dominant_stressor_enum NOT NULL,
    suggested_action prescriptive_action_enum NOT NULL,
    execution_index_version VARCHAR(32) NOT NULL DEFAULT 'v1.0.0-esi-5dim',
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_esi_project_month UNIQUE (project_id, report_month)
);

CREATE INDEX idx_esi_scores_month_tier ON execution_stress_scores (report_month, esi_tier);
CREATE INDEX idx_esi_scores_index ON execution_stress_scores (report_month, execution_stress_index DESC);
CREATE INDEX idx_esi_scores_dominant ON execution_stress_scores (report_month, dominant_stressor);

-- 4. Recreate View to include Pillar 2
DROP VIEW IF EXISTS v_project_monthly_dossier CASCADE;

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
    
    -- LAYER B: DETERMINISTIC DERIVED METRICS
    (r.revised_cost_crore - r.original_cost_crore) AS cost_escalation_crore,
    CASE 
        WHEN r.original_cost_crore > 0 
        THEN ROUND(((r.revised_cost_crore - r.original_cost_crore) / r.original_cost_crore * 100.0), 2)
        ELSE 0.0 
    END AS cost_escalation_percent,
    CASE 
        WHEN r.original_cost_crore > 0 
        THEN ROUND((r.cumulative_expenditure_crore / r.original_cost_crore * 100.0), 2)
        ELSE 0.0 
    END AS expenditure_ratio_percent,
    (100.0 - r.physical_progress_percent) AS remaining_physical_progress,
    CASE 
        WHEN r.revised_completion_date IS NOT NULL 
        THEN (
            (CAST(SUBSTRING(r.revised_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTRING(r.revised_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT))
        )
        ELSE 0.0 
    END AS schedule_slippage_months,
    (
        (CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.report_month, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.report_month, 6, 2) AS INT))
    ) AS months_to_original_doc,
    CASE 
        WHEN r.prev_prog_1m IS NOT NULL THEN (r.physical_progress_percent - r.prev_prog_1m)
        ELSE NULL 
    END AS progress_velocity_1m,
    CASE 
        WHEN r.prev_prog_3m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_3m) / 3.0), 2)
        WHEN r.prev_prog_2m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_2m) / 2.0), 2)
        WHEN r.prev_prog_1m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_1m) / 1.0), 2)
        ELSE NULL 
    END AS progress_velocity_3m,
    CASE 
        WHEN r.prev_prog_3m IS NOT NULL AND (r.physical_progress_percent - r.prev_prog_3m = 0.0) THEN 1
        ELSE 0 
    END AS stagnant_3m_flag,
    CASE 
        WHEN r.original_cost_crore > 0 
        THEN ROUND(((r.cumulative_expenditure_crore / r.original_cost_crore * 100.0) - r.physical_progress_percent), 2)
        ELSE 0.0 
    END AS expenditure_progress_divergence,
    (
        (CAST(SUBSTRING(r.report_month, 1, 4) AS INT) - CAST(SUBSTRING(r.approval_start_date, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTRING(r.report_month, 6, 2) AS INT) - CAST(SUBSTRING(r.approval_start_date, 6, 2) AS INT))
    ) AS project_age_months,
    (
        (CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.approval_start_date, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.approval_start_date, 6, 2) AS INT))
    ) AS planned_duration_months,

    -- LAYER C: MACHINE LEARNING RISK SIGNALS (Joined from ml_risk_scores)
    m.schedule_delay_risk,
    m.cost_overrun_risk,
    m.schedule_revision_risk,
    m.selected_integrated_risk,
    m.risk_band,
    m.dominant_component,
    m.schedule_contribution,
    m.cost_contribution,
    m.schedule_revision_contribution,
    CASE 
        WHEN m.selected_integrated_risk > 0 
        THEN ROUND((m.schedule_contribution / m.selected_integrated_risk * 100.0), 2)
        ELSE 0.0 
    END AS schedule_contrib_pct,
    CASE 
        WHEN m.selected_integrated_risk > 0 
        THEN ROUND((m.cost_contribution / m.selected_integrated_risk * 100.0), 2)
        ELSE 0.0 
    END AS cost_contrib_pct,
    CASE 
        WHEN m.selected_integrated_risk > 0 
        THEN ROUND((m.schedule_revision_contribution / m.selected_integrated_risk * 100.0), 2)
        ELSE 0.0 
    END AS schedule_rev_contrib_pct,
    
    -- PILLAR 2: OPERATIONAL EXECUTION SURVEILLANCE
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
