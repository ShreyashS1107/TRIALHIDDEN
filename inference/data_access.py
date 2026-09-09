"""
Database Access Layer for Inference Adapter
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Provides a clean, decoupled data-access boundary for fetching historical project records.
Supports SQLAlchemy Sessions, Pandas DataFrames, or custom query callables.
Enforces strict point-in-time isolation: report_month < as_of_month.
"""

import os
import re
import pandas as pd
import numpy as np


def fetch_historical_project_snapshots(
    db_session,
    as_of_month: str,
    project_ids: list[str] = None
) -> pd.DataFrame:
    """
    Fetches historical project snapshots strictly before as_of_month (report_month < as_of_month).

    Parameters:
        db_session: Database session abstraction. Can be:
            - SQLAlchemy Session / AsyncSession / Connection / Engine
            - pandas DataFrame (for testing or batch execution)
            - Callable returning DataFrame: db_session(as_of_month, project_ids)
            - None (will attempt local file fallback if available in test/dev mode)
        as_of_month: Point-in-time cutoff epoch in 'YYYY-MM' format.
        project_ids: Optional list of project IDs to filter for efficiency.

    Returns:
        pd.DataFrame containing historical records strictly with report_month < as_of_month.
    """
    if as_of_month is None or not re.match(r'^\d{4}-\d{2}$', str(as_of_month).strip()):
        raise ValueError(f"Invalid as_of_month: '{as_of_month}'. Must be in 'YYYY-MM' format.")
    
    as_of_month = str(as_of_month).strip()[:7]
    hist_df = None

    # Case 1: db_session is a pandas DataFrame
    if isinstance(db_session, pd.DataFrame):
        hist_df = db_session.copy()

    # Case 2: db_session is a callable
    elif callable(db_session):
        result = db_session(as_of_month=as_of_month, project_ids=project_ids)
        if isinstance(result, pd.DataFrame):
            hist_df = result.copy()
        elif isinstance(result, (list, dict)):
            hist_df = pd.DataFrame(result)
        else:
            raise TypeError(f"db_session callable returned unexpected type: {type(result)}")

    # Case 3: db_session is an SQLAlchemy Session or Connection
    elif db_session is not None and hasattr(db_session, 'execute'):
        # Generic query against standardized schema defined in BACKEND_API_AND_DATABASE_SPECIFICATION.txt
        query = """
            SELECT 
                s.project_id,
                p.project_name,
                p.agency,
                p.state,
                p.legacy_ocms_code,
                p.approval_start_date,
                p.original_completion_date,
                p.original_cost_crore,
                s.revised_completion_date,
                s.revised_cost_crore,
                s.cumulative_expenditure_crore,
                s.physical_progress_percent,
                s.report_month,
                s.source_file,
                s.source_table
            FROM monthly_snapshots s
            JOIN projects p ON s.project_id = p.project_id
            WHERE s.report_month < :as_of_month
        """
        params = {"as_of_month": as_of_month}
        if project_ids:
            query += " AND s.project_id = ANY(:project_ids)"
            params["project_ids"] = list(project_ids)

        try:
            from sqlalchemy import text
            result = db_session.execute(text(query), params)
            rows = result.fetchall()
            if rows:
                cols = list(result.keys())
                hist_df = pd.DataFrame([dict(zip(cols, r)) for r in rows])
            else:
                hist_df = pd.DataFrame()
        except Exception as e:
            # If standard schema query fails, try direct monthly_snapshots query
            try:
                from sqlalchemy import text
                q_direct = "SELECT * FROM monthly_snapshots WHERE report_month < :as_of_month"
                result = db_session.execute(text(q_direct), params)
                rows = result.fetchall()
                if rows:
                    cols = list(result.keys())
                    hist_df = pd.DataFrame([dict(zip(cols, r)) for r in rows])
                else:
                    hist_df = pd.DataFrame()
            except Exception as e2:
                raise RuntimeError(f"Failed to query historical data via SQLAlchemy session: {e2}") from e

    # Case 4: Fallback to local master dataset if db_session is None (Dev / Local evaluation)
    elif db_session is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        master_csv = os.path.join(base_dir, 'data', 'paimana_master_dataset.csv')
        if os.path.exists(master_csv):
            full_master = pd.read_csv(master_csv, dtype=str)
            hist_df = full_master.copy()
        else:
            hist_df = pd.DataFrame()

    else:
        raise TypeError(f"Unsupported db_session type: {type(db_session)}. Expected SQLAlchemy Session, DataFrame, or Callable.")

    if hist_df is None or len(hist_df) == 0:
        return pd.DataFrame()

    # STRICT POINT-IN-TIME GUARANTEE: Filter strictly before as_of_month
    if 'report_month' in hist_df.columns:
        hist_df['report_month'] = hist_df['report_month'].astype(str).str.strip().str[:7]
        # Discard any records from month >= as_of_month
        hist_df = hist_df[hist_df['report_month'] < as_of_month].copy()
    else:
        raise ValueError("Historical records DataFrame must contain 'report_month' column.")

    if project_ids and 'project_id' in hist_df.columns:
        pid_set = set(str(p).strip() for p in project_ids)
        hist_df['project_id'] = hist_df['project_id'].astype(str).str.strip()
        hist_df = hist_df[hist_df['project_id'].isin(pid_set)].copy()

    return hist_df
