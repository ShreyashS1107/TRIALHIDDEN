-- Migration 001: Relax source NULL constraints
-- This migration lifts NOT NULL constraints on specific columns where the 
-- underlying PAIMANA source data naturally contains NULL/missing values.
-- It ensures that data seeding preserves the raw source state exactly without inserting fake dates or values.

-- 1. Table: projects
ALTER TABLE projects 
    ALTER COLUMN project_name DROP NOT NULL,
    ALTER COLUMN approval_start_date DROP NOT NULL,
    ALTER COLUMN original_completion_date DROP NOT NULL,
    ALTER COLUMN original_cost_crore DROP NOT NULL;

-- 2. Table: monthly_snapshots
ALTER TABLE monthly_snapshots 
    ALTER COLUMN revised_cost_crore DROP NOT NULL,
    ALTER COLUMN cumulative_expenditure_crore DROP NOT NULL,
    ALTER COLUMN physical_progress_percent DROP NOT NULL;

-- 3. Table: completed_projects
ALTER TABLE completed_projects 
    ALTER COLUMN original_cost_crore DROP NOT NULL,
    ALTER COLUMN actual_cost_crore DROP NOT NULL,
    ALTER COLUMN cumulative_expenditure_crore DROP NOT NULL,
    ALTER COLUMN actual_completion_date DROP NOT NULL;

-- 4. Table: newly_added_projects
ALTER TABLE newly_added_projects 
    ALTER COLUMN original_cost_crore DROP NOT NULL,
    ALTER COLUMN approval_start_date DROP NOT NULL,
    ALTER COLUMN original_completion_date DROP NOT NULL;
