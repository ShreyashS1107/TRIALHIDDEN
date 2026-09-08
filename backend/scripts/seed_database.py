import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

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


if __name__ == '__main__':
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    master_csv = os.path.join(base_dir, 'data', 'paimana_master_dataset.csv')
    completed_csv = os.path.join(base_dir, 'data', 'paimana_completed_projects.csv')
    newly_added_csv = os.path.join(base_dir, 'data', 'paimana_newly_added_projects.csv')
    manual_review_csv = os.path.join(base_dir, 'reports', 'manual_review.csv')
    ml_risk_scores_csv = os.path.join(base_dir, 'ml', 'risk_engine', 'integrated_risk_scores.csv')

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

