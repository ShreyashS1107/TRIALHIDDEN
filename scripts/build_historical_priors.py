import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

historical_completed_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\historical_completed_projects.csv"
output_dir = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors"
os.makedirs(output_dir, exist_ok=True)

df_comp = pd.read_csv(historical_completed_path)
print(f"Loaded {len(df_comp)} completed project records.")

# Clean strings
df_comp['agency'] = df_comp['agency'].astype(str).str.strip().str.upper()
df_comp['sector'] = df_comp['sector'].astype(str).str.strip().str.upper()
df_comp['actual_completion_date'] = df_comp['actual_completion_date'].astype(str).str.strip()

# Valid date format YYYY-MM
df_comp = df_comp[df_comp['actual_completion_date'].str.match(r'^\d{4}-\d{2}$', na=False)].copy()
print(f"Records with valid YYYY-MM completion date: {len(df_comp)}")

# PAIMANA Prediction Months (April 2025 to June 2026)
prediction_months = [
    f"{y:04d}-{m:02d}"
    for y in [2025, 2026]
    for m in range(1, 13)
    if (y == 2025 and m >= 4) or (y == 2026 and m <= 6)
]
print(f"Computing point-in-time priors across {len(prediction_months)} prediction months: {prediction_months}")

# Get all unique agencies and sectors from active PAIMANA dataset and historical completed
paimana_master = pd.read_csv(r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_master_dataset.csv")
all_agencies = sorted(list(set(paimana_master['agency'].dropna().str.strip().str.upper()).union(set(df_comp['agency'].unique()))))
all_sectors = sorted(list(set(paimana_master['sector'].dropna().str.strip().str.upper()).union(set(df_comp['sector'].unique())))) if 'sector' in paimana_master.columns else sorted(list(set(df_comp['sector'].unique())))

print(f"Unique agencies to evaluate: {len(all_agencies)}")
print(f"Unique sectors to evaluate: {len(all_sectors)}")

def month_diff(d1, d2):
    # d1 - d2 in months
    y1, m1 = int(d1[:4]), int(d1[5:7])
    y2, m2 = int(d2[:4]), int(d2[5:7])
    return (y1 - y2) * 12 + (m1 - m2)

def compute_window_stats(subset, min_sample=1):
    n_comp = len(subset)
    if n_comp == 0:
        return {
            'completed_count': 0,
            'delay_count': 0,
            'delay_rate_raw': np.nan,
            'mean_delay_months': np.nan,
            'median_delay_months': np.nan,
            'cost_obs_count': 0,
            'cost_overrun_count': 0,
            'cost_overrun_rate_raw': np.nan,
            'mean_cost_overrun_pct': np.nan,
            'median_cost_overrun_pct': np.nan,
            'max_source_date': None
        }
    
    # Schedule metrics
    delays = subset['historical_delay_months'].dropna()
    delay_flags = subset['historical_delay_flag'].dropna()
    n_delay_obs = len(delay_flags)
    delay_cnt = int(delay_flags.sum()) if n_delay_obs > 0 else 0
    delay_rate = (delay_cnt / n_delay_obs) if n_delay_obs >= min_sample else np.nan
    mean_delay = float(delays.mean()) if len(delays) > 0 else np.nan
    med_delay = float(delays.median()) if len(delays) > 0 else np.nan
    
    # Cost metrics
    cost_flags = subset['historical_cost_overrun_flag'].dropna()
    cost_pcts = subset['historical_cost_overrun_pct'].dropna()
    n_cost_obs = len(cost_flags)
    cost_ovr_cnt = int(cost_flags.sum()) if n_cost_obs > 0 else 0
    cost_ovr_rate = (cost_ovr_cnt / n_cost_obs) if n_cost_obs >= min_sample else np.nan
    mean_cost_pct = float(cost_pcts.mean()) if len(cost_pcts) > 0 else np.nan
    med_cost_pct = float(cost_pcts.median()) if len(cost_pcts) > 0 else np.nan
    
    max_src_d = subset['actual_completion_date'].max()
    
    return {
        'completed_count': n_comp,
        'delay_count': delay_cnt,
        'delay_rate_raw': delay_rate,
        'mean_delay_months': mean_delay,
        'median_delay_months': med_delay,
        'cost_obs_count': n_cost_obs,
        'cost_overrun_count': cost_ovr_cnt,
        'cost_overrun_rate_raw': cost_ovr_rate,
        'mean_cost_overrun_pct': mean_cost_pct,
        'median_cost_overrun_pct': med_cost_pct,
        'max_source_date': max_src_d
    }

# Compute sector priors first so we can use them for empirical Bayes shrinkage
sector_priors_records = []
agency_priors_records = []

windows = {
    'lifetime': None,
    '10y': 120,
    '5y': 60,
    '3y': 36
}

print("Building Sector Historical Priors (as-of t)...")
sector_as_of_dict = {} # (sector, as_of_date, win) -> stats

for as_of_t in prediction_months:
    # STRICT POINT-IN-TIME CONDITION: actual_completion_date < as_of_t
    valid_hist = df_comp[df_comp['actual_completion_date'] < as_of_t].copy()
    
    for sec in all_sectors:
        sec_df = valid_hist[valid_hist['sector'] == sec]
        
        for win_name, win_months in windows.items():
            if win_months is None:
                win_df = sec_df
            else:
                win_df = sec_df[sec_df['actual_completion_date'].apply(lambda d: 0 < month_diff(as_of_t, d) <= win_months)]
                
            stats = compute_window_stats(win_df)
            sector_as_of_dict[(sec, as_of_t, win_name)] = stats
            
            sector_priors_records.append({
                'sector': sec,
                'as_of_date': as_of_t,
                'window': win_name,
                'completed_count': stats['completed_count'],
                'delay_count': stats['delay_count'],
                'delay_rate_raw': stats['delay_rate_raw'],
                'mean_delay_months': stats['mean_delay_months'],
                'median_delay_months': stats['median_delay_months'],
                'cost_obs_count': stats['cost_obs_count'],
                'cost_overrun_count': stats['cost_overrun_count'],
                'cost_overrun_rate_raw': stats['cost_overrun_rate_raw'],
                'mean_cost_overrun_pct': stats['mean_cost_overrun_pct'],
                'median_cost_overrun_pct': stats['median_cost_overrun_pct'],
                'max_source_date': stats['max_source_date']
            })

df_sector_priors = pd.DataFrame(sector_priors_records)
df_sector_priors.to_csv(os.path.join(output_dir, "sector_historical_priors.csv"), index=False)
print(f"Saved sector_historical_priors.csv ({len(df_sector_priors)} rows).")

print("Building Agency Historical Priors (as-of t) with Empirical Bayes Shrinkage...")
# Empirical Bayes smoothing formula:
# smoothed_rate = (k_obs + alpha) / (n_obs + alpha + beta)
# where alpha = m * prior_rate, beta = m * (1 - prior_rate), m is weight (e.g. m = 5 pseudo-observations)
M_SMOOTH = 5.0

for as_of_t in prediction_months:
    valid_hist = df_comp[df_comp['actual_completion_date'] < as_of_t].copy()
    
    # Global portfolio prior as-of t for fallback
    global_stats = compute_window_stats(valid_hist)
    global_delay_prior = global_stats['delay_rate_raw'] if pd.notna(global_stats['delay_rate_raw']) else 0.80
    global_cost_prior = global_stats['cost_overrun_rate_raw'] if pd.notna(global_stats['cost_overrun_rate_raw']) else 0.30
    
    for ag in all_agencies:
        ag_df = valid_hist[valid_hist['agency'] == ag]
        # determine primary sector for agency if known
        ag_sec = ag_df['sector'].iloc[0] if len(ag_df) > 0 else "UNKNOWN"
        
        for win_name, win_months in windows.items():
            if win_months is None:
                win_df = ag_df
            else:
                win_df = ag_df[ag_df['actual_completion_date'].apply(lambda d: 0 < month_diff(as_of_t, d) <= win_months)]
                
            stats = compute_window_stats(win_df)
            
            # Retrieve sector-level prior as-of t for shrinkage
            sec_stats = sector_as_of_dict.get((ag_sec, as_of_t, win_name), {})
            sec_delay_p = sec_stats.get('delay_rate_raw')
            sec_cost_p = sec_stats.get('cost_overrun_rate_raw')
            
            delay_prior_p = sec_delay_p if (pd.notna(sec_delay_p)) else global_delay_prior
            cost_prior_p = sec_cost_p if (pd.notna(sec_cost_p)) else global_cost_prior
            
            # Compute empirical Bayes smoothed rate
            n_delay = stats['completed_count']
            k_delay = stats['delay_count']
            if n_delay > 0:
                delay_rate_smoothed = (k_delay + M_SMOOTH * delay_prior_p) / (n_delay + M_SMOOTH)
            else:
                delay_rate_smoothed = delay_prior_p
                
            n_cost = stats['cost_obs_count']
            k_cost = stats['cost_overrun_count']
            if n_cost > 0:
                cost_rate_smoothed = (k_cost + M_SMOOTH * cost_prior_p) / (n_cost + M_SMOOTH)
            else:
                cost_rate_smoothed = cost_prior_p
                
            agency_priors_records.append({
                'agency': ag,
                'as_of_date': as_of_t,
                'window': win_name,
                'completed_count': stats['completed_count'],
                'delay_count': stats['delay_count'],
                'delay_rate_raw': stats['delay_rate_raw'],
                'delay_rate_smoothed': delay_rate_smoothed,
                'mean_delay_months': stats['mean_delay_months'],
                'median_delay_months': stats['median_delay_months'],
                'cost_obs_count': stats['cost_obs_count'],
                'cost_overrun_count': stats['cost_overrun_count'],
                'cost_overrun_rate_raw': stats['cost_overrun_rate_raw'],
                'cost_overrun_rate_smoothed': cost_rate_smoothed,
                'mean_cost_overrun_pct': stats['mean_cost_overrun_pct'],
                'median_cost_overrun_pct': stats['median_cost_overrun_pct'],
                'max_source_date': stats['max_source_date']
            })

df_agency_priors = pd.DataFrame(agency_priors_records)
df_agency_priors.to_csv(os.path.join(output_dir, "agency_historical_priors.csv"), index=False)
print(f"Saved agency_historical_priors.csv ({len(df_agency_priors)} rows).")
print("Component 2 complete.")
