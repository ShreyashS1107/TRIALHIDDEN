-- Migration 004: Add Historical Benchmarks Table

CREATE TABLE IF NOT EXISTS ocms_historical_benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Legacy DB Spec fields (Nullable since this is an aggregated CSV, not project-level)
    project_id VARCHAR(32) REFERENCES projects(project_id) ON DELETE SET NULL,
    legacy_ocms_code VARCHAR(32),
    agency VARCHAR(255),
    sector VARCHAR(255),
    historical_observation_months INT,
    historical_mean_cost_escalation_pct NUMERIC(10, 2),
    historical_mean_delay_months NUMERIC(10, 2),
    historical_completion_rate_pct NUMERIC(10, 2),
    
    -- Exact fields from historical_benchmarking.csv
    benchmark_level VARCHAR(64) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    year VARCHAR(64) NOT NULL,
    total_completed_projects INT,
    projects_with_schedule_outcome INT,
    delay_count INT,
    delay_rate_pct NUMERIC(10, 2),
    mean_delay_months NUMERIC(10, 2),
    median_delay_months NUMERIC(10, 2),
    projects_with_cost_outcome INT,
    cost_overrun_count INT,
    cost_overrun_rate_pct NUMERIC(10, 2),
    mean_cost_overrun_pct NUMERIC(10, 2),
    median_cost_overrun_pct NUMERIC(10, 2),
    total_original_cost_crore NUMERIC(16, 2),
    total_cumulative_expenditure_crore NUMERIC(16, 2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_ocms_benchmark_grain UNIQUE (benchmark_level, entity_name, year)
);

CREATE INDEX idx_ocms_benchmarks_entity ON ocms_historical_benchmarks (entity_name);
CREATE INDEX idx_ocms_benchmarks_level_year ON ocms_historical_benchmarks (benchmark_level, year);
