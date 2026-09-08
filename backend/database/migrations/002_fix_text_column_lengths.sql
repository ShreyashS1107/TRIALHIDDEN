-- Migration 002: Fix text column lengths for agency and state
-- These columns frequently exceed the previous VARCHAR(64) and VARCHAR(128) limits 
-- in the raw PAIMANA datasets.

-- 1. Safely drop the dependent view first
DROP VIEW IF EXISTS v_project_monthly_dossier CASCADE;

-- 2. Alter column types to TEXT to support unstructured source lengths
ALTER TABLE projects
ALTER COLUMN agency TYPE TEXT,
ALTER COLUMN state TYPE TEXT;

ALTER TABLE completed_projects
ALTER COLUMN agency TYPE TEXT,
ALTER COLUMN state TYPE TEXT;

ALTER TABLE newly_added_projects
ALTER COLUMN agency TYPE TEXT,
ALTER COLUMN state TYPE TEXT;

-- 3. Recreate the exact view using the new column types
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
    -- 1. Cost Escalation in ₹ Cr
    (r.revised_cost_crore - r.original_cost_crore) AS cost_escalation_crore,
    
    -- 2. Cost Escalation in %
    CASE 
        WHEN r.original_cost_crore > 0 
        THEN ROUND(((r.revised_cost_crore - r.original_cost_crore) / r.original_cost_crore * 100.0), 2)
        ELSE 0.0 
    END AS cost_escalation_percent,
    
    -- 3. Expenditure Ratio %
    CASE 
        WHEN r.original_cost_crore > 0 
        THEN ROUND((r.cumulative_expenditure_crore / r.original_cost_crore * 100.0), 2)
        ELSE 0.0 
    END AS expenditure_ratio_percent,
    
    -- 4. Remaining Physical Progress %
    (100.0 - r.physical_progress_percent) AS remaining_physical_progress,
    
    -- 5. Schedule Slippage in Months
    CASE 
        WHEN r.revised_completion_date IS NOT NULL 
        THEN (
            (CAST(SUBSTRING(r.revised_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTRING(r.revised_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT))
        )
        ELSE 0.0 
    END AS schedule_slippage_months,
    
    -- 6. Months Remaining to Original Sanctioned Deadline (Negative = Past Due)
    (
        (CAST(SUBSTRING(r.original_completion_date, 1, 4) AS INT) - CAST(SUBSTRING(r.report_month, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTRING(r.original_completion_date, 6, 2) AS INT) - CAST(SUBSTRING(r.report_month, 6, 2) AS INT))
    ) AS months_to_original_doc,
    
    -- 7. 1-Month Progress Velocity (% delta)
    CASE 
        WHEN r.prev_prog_1m IS NOT NULL THEN (r.physical_progress_percent - r.prev_prog_1m)
        ELSE NULL 
    END AS progress_velocity_1m,
    
    -- 8. 3-Month Rolling Average Progress Velocity (% / month)
    CASE 
        WHEN r.prev_prog_3m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_3m) / 3.0), 2)
        WHEN r.prev_prog_2m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_2m) / 2.0), 2)
        WHEN r.prev_prog_1m IS NOT NULL THEN ROUND(((r.physical_progress_percent - r.prev_prog_1m) / 1.0), 2)
        ELSE NULL 
    END AS progress_velocity_3m,
    
    -- 9. 3-Month Stagnation Indicator Flag (1 = Stagnant)
    CASE 
        WHEN r.prev_prog_3m IS NOT NULL AND (r.physical_progress_percent - r.prev_prog_3m = 0.0) THEN 1
        ELSE 0 
    END AS stagnant_3m_flag,
    
    -- 10. Capital Burn vs Physical Progress Divergence (%)
    CASE 
        WHEN r.original_cost_crore > 0 
        THEN ROUND(((r.cumulative_expenditure_crore / r.original_cost_crore * 100.0) - r.physical_progress_percent), 2)
        ELSE 0.0 
    END AS expenditure_progress_divergence,
    
    -- 11. Project Age (Months)
    (
        (CAST(SUBSTRING(r.report_month, 1, 4) AS INT) - CAST(SUBSTRING(r.approval_start_date, 1, 4) AS INT)) * 12 +
        (CAST(SUBSTRING(r.report_month, 6, 2) AS INT) - CAST(SUBSTRING(r.approval_start_date, 6, 2) AS INT))
    ) AS project_age_months,

    -- 12. Planned Duration (Months)
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
    END AS schedule_rev_contrib_pct

FROM ranked_snapshots r
LEFT JOIN ml_risk_scores m ON r.project_id = m.project_id AND r.report_month = m.report_month;
