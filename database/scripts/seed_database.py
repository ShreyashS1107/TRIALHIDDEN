import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', '.env'))

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL is required in backend/.env")
    exit(1)

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def seed_projects_and_snapshots(conn, csv_path):
    print(f"Seeding projects and monthly_snapshots from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.replace({pd.NA: None, float('nan'): None})
    
    projects_df = df.sort_values('report_month').drop_duplicates(subset=['project_id'], keep='last')
    
    projects_data = []
    for _, row in projects_df.iterrows():
        projects_data.append((
            row['project_id'], row['project_name'], row['agency'], row['state'],
            row['legacy_ocms_code'], row['approval_start_date'], row['original_completion_date'],
            row['original_cost_crore'], True
        ))
        
    projects_query = """
    INSERT INTO projects (
        project_id, project_name, agency, state, legacy_ocms_code, 
        approval_start_date, original_completion_date, original_cost_crore, is_active
    ) VALUES %s ON CONFLICT (project_id) DO NOTHING;
    """
    
    with conn.cursor() as cur:
        execute_values(cur, projects_query, projects_data)
        conn.commit()
    print(f"  Inserted up to {len(projects_data)} projects.")

    snapshots_data = []
    for _, row in df.iterrows():
        progress = row['physical_progress_percent']
        if progress is not None: progress = max(0.0, min(100.0, float(progress)))
        revised_cost = row['revised_cost_crore']
        if revised_cost is not None: revised_cost = max(0.0, float(revised_cost))
        cum_exp = row['cumulative_expenditure_crore']
        if cum_exp is not None: cum_exp = max(0.0, float(cum_exp))

        snapshots_data.append((
            row['project_id'], row['report_month'], row['revised_completion_date'],
            revised_cost, cum_exp, progress, row['source_file'], row['source_table']
        ))
        
    snapshots_query = """
    INSERT INTO monthly_snapshots (
        project_id, report_month, revised_completion_date, revised_cost_crore, 
        cumulative_expenditure_crore, physical_progress_percent, source_file, source_table
    ) VALUES %s ON CONFLICT (project_id, report_month) DO NOTHING;
    """
    
    with conn.cursor() as cur:
        execute_values(cur, snapshots_query, snapshots_data)
        conn.commit()
    print(f"  Inserted up to {len(snapshots_data)} monthly_snapshots.")

def seed_completed_projects(conn, csv_path):
    print(f"Seeding completed_projects from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.replace({pd.NA: None, float('nan'): None})
    
    data = []
    for _, row in df.iterrows():
        data.append((
            row['project_id'], row['project_name'], row['agency'], row['state'],
            row['original_cost_crore'], row['revised_cost_crore'], 
            row['cumulative_expenditure_crore'], row['actual_completion_date'],
            row['report_month'], row['source_file']
        ))
        
    query = """
    INSERT INTO completed_projects (
        project_id, project_name, agency, state, original_cost_crore, 
        actual_cost_crore, cumulative_expenditure_crore, actual_completion_date, 
        report_month, source_file
    ) VALUES %s ON CONFLICT (project_id) DO NOTHING;
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, data)
        conn.commit()
    print(f"  Inserted up to {len(data)} completed_projects.")

def seed_newly_added_projects(conn, csv_path):
    print(f"Seeding newly_added_projects from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.replace({pd.NA: None, float('nan'): None})
    
    # STRATEGY FOR IDEMPOTENCY:
    # Since newly_added_projects lacks a UNIQUE constraint, we query existing natural keys
    # Natural key: (project_id, report_month)
    with conn.cursor() as cur:
        cur.execute("SELECT project_id, report_month FROM newly_added_projects;")
        existing_keys = set(cur.fetchall())
    
    data = []
    for _, row in df.iterrows():
        natural_key = (row['project_id'], row['report_month'])
        if natural_key not in existing_keys:
            data.append((
                row['project_id'], row['project_name'], row['agency'], row['state'],
                row['original_cost_crore'], row['approval_start_date'],
                row['original_completion_date'], row['report_month'], row['source_file']
            ))
            existing_keys.add(natural_key) # Prevent duplicates from within the CSV itself
        
    if not data:
        print("  0 new newly_added_projects to insert.")
        return

    query = """
    INSERT INTO newly_added_projects (
        project_id, project_name, agency, state, original_cost_crore, 
        approval_start_date, original_completion_date, report_month, source_file
    ) VALUES %s;
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, data)
        conn.commit()
    print(f"  Inserted {len(data)} newly_added_projects.")

def seed_ml_risk_scores(conn, csv_path):
    print(f"Seeding ml_risk_scores from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.replace({pd.NA: None, float('nan'): None})
    
    data = []
    for _, row in df.iterrows():
        data.append((
            row['project_id'], row['prediction_month'], row['schedule_delay_risk'],
            row['cost_overrun_risk'], row['schedule_revision_risk'],
            row['selected_integrated_risk'], row['risk_band'],
            row['dominant_component'], row['schedule_contribution'],
            row['cost_contribution'], row['schedule_revision_contribution']
        ))
        
    query = """
    INSERT INTO ml_risk_scores (
        project_id, report_month, schedule_delay_risk, cost_overrun_risk, 
        schedule_revision_risk, selected_integrated_risk, risk_band, 
        dominant_component, schedule_contribution, cost_contribution, schedule_revision_contribution
    ) VALUES %s ON CONFLICT (project_id, report_month) DO NOTHING;
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, data, template="(%s, %s, %s, %s, %s, %s, %s::risk_band_enum, %s::dominant_component_enum, %s, %s, %s)")
        conn.commit()
    print(f"  Inserted up to {len(data)} ml_risk_scores.")

def seed_data_anomalies_log(conn, csv_path):
    print(f"Seeding data_anomalies_log from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.replace({pd.NA: None, float('nan'): None})
    
    # STRATEGY FOR IDEMPOTENCY:
    # Since data_anomalies_log lacks a UNIQUE constraint, query existing natural keys.
    # Natural key: (project_id, report_month, flag_code)
    with conn.cursor() as cur:
        cur.execute("SELECT project_id, report_month, flag_code FROM data_anomalies_log;")
        existing_keys = set(cur.fetchall())
        
    data = []
    for _, row in df.iterrows():
        natural_key = (row['project_id'], row['report_month'], row['flag_category'])
        if natural_key not in existing_keys:
            data.append((
                row['project_id'], row['report_month'], row['flag_category'], 
                row['severity'], None, None, row['flag_reason']
            ))
            existing_keys.add(natural_key) # Prevent duplicates within the CSV
            
    if not data:
        print("  0 new data_anomalies_log to insert.")
        return
        
    query = """
    INSERT INTO data_anomalies_log (
        project_id, report_month, flag_code, severity, metric_value, prior_value, details
    ) VALUES %s;
    """
    
    with conn.cursor() as cur:
        execute_values(cur, query, data, template="(%s, %s, %s, %s::alert_severity_enum, %s, %s, %s)")
        conn.commit()
    print(f"  Inserted {len(data)} data_anomalies_log.")



def seed_execution_stress_scores(conn, csv_path):
    print(f"Seeding execution_stress_scores from {csv_path}...")
    df = pd.read_csv(csv_path)
    df = df.replace({pd.NA: None, float('nan'): None})
    
    data = []
    for _, row in df.iterrows():
        esi = float(row['execution_stress_index'])
        if esi < 0.35:
            esi_tier = 'NOMINAL'
        elif esi < 0.55:
            esi_tier = 'WATCH'
        elif esi < 0.75:
            esi_tier = 'ATTENTION'
        else:
            esi_tier = 'HIGH_PRIORITY'
            
        components = {
            'Physical Progress Stagnation': 0.30 * float(row['s_stag']),
            'Progress Velocity Collapse': 0.25 * float(row['s_vel']),
            'Expenditure Divergence': 0.20 * float(row['s_div']),
            'Schedule Slippage Debt': 0.15 * float(row['s_sched']),
            'Reporting Friction': 0.10 * float(row['s_rep'])
        }
        dominant_stressor = max(components.items(), key=lambda x: x[1])[0]
        
        # Prescriptive action mapping
        if esi >= 0.75 and int(row['total_stress_flags']) >= 3:
            action = 'INTER_MINISTERIAL_COMMITTEE_ESCALATION'
        elif float(row['s_stag']) >= 0.75 or int(row['flag_stag']) == 1:
            action = 'SITE_OBSTACLE_AUDIT'
        elif float(row['s_div']) >= 0.75 or int(row['flag_div']) == 1:
            action = 'FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT'
        elif float(row['s_vel']) >= 0.75 or int(row['flag_vel']) == 1:
            action = 'RESOURCE_MOBILIZATION_DIRECTIVE'
        elif float(row['s_sched']) >= 0.75 or int(row['flag_sched']) == 1:
            action = 'CRITICAL_PATH_RECALIBRATION'
        elif float(row['s_rep']) >= 0.75 or int(row['flag_rep']) == 1:
            action = 'DATA_COMPLIANCE_DIRECTIVE'
        else:
            if dominant_stressor == 'Expenditure Divergence':
                action = 'FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT'
            elif dominant_stressor == 'Progress Velocity Collapse':
                action = 'RESOURCE_MOBILIZATION_DIRECTIVE'
            elif dominant_stressor == 'Schedule Slippage Debt':
                action = 'CRITICAL_PATH_RECALIBRATION'
            elif dominant_stressor == 'Reporting Friction':
                action = 'DATA_COMPLIANCE_DIRECTIVE'
            else:
                action = 'SITE_OBSTACLE_AUDIT'
                
        data.append((
            row['project_id'], row['prediction_month'],
            row['s_stag'], row['s_vel'], row['s_div'], row['s_sched'], row['s_rep'],
            row['flag_stag'], row['flag_vel'], row['flag_div'], row['flag_sched'], row['flag_rep'],
            row['total_stress_flags'], row['execution_stress_index'],
            esi_tier, dominant_stressor, action
        ))
        
    query = """
    INSERT INTO execution_stress_scores (
        project_id, report_month, s_stag, s_vel, s_div, s_sched, s_rep,
        flag_stag, flag_vel, flag_div, flag_sched, flag_rep, total_stress_flags,
        execution_stress_index, esi_tier, dominant_stressor, suggested_action
    ) VALUES %s ON CONFLICT (project_id, report_month) DO NOTHING;
    """
    
    with conn.cursor() as cur:
        from psycopg2.extras import execute_values
        execute_values(cur, query, data, template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::esi_tier_enum, %s::dominant_stressor_enum, %s::prescriptive_action_enum)")
        conn.commit()
    print(f"  Inserted up to {len(data)} execution_stress_scores.")


if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    master_csv = os.path.join(base_dir, 'ai-ml', 'data', 'paimana_master_dataset.csv')
    completed_csv = os.path.join(base_dir, 'ai-ml', 'data', 'paimana_completed_projects.csv')
    newly_added_csv = os.path.join(base_dir, 'ai-ml', 'data', 'paimana_newly_added_projects.csv')
    manual_review_csv = os.path.join(base_dir, 'ai-ml', 'reports', 'manual_review.csv')
    ml_risk_scores_csv = os.path.join(base_dir, 'ai-ml', 'ml', 'risk_engine', 'integrated_risk_scores.csv')
    execution_stress_scores_csv = os.path.join(base_dir, 'ai-ml', 'experiments', 'execution_risk', 'execution_stress_scores.csv')

    print("Starting database seeding process...")
    try:
        conn = get_connection()
        seed_projects_and_snapshots(conn, master_csv)
        seed_completed_projects(conn, completed_csv)
        seed_newly_added_projects(conn, newly_added_csv)
        seed_ml_risk_scores(conn, ml_risk_scores_csv)
        seed_data_anomalies_log(conn, manual_review_csv)
        conn.close()
        print("Database seeding completed successfully.")
    except Exception as e:
        print(f"Error during database seeding: {e}")

