"""
Offline Database Ingestion & Pipeline Orchestration Script for SIH26103 Execution Surveillance (Phase 5C-2).

Flow:
    feature_dataset_v1.csv
            ↓
    ExecutionSurveillanceEngine
            ↓
    ESI structured scores
            ↓
    validation
            ↓
    idempotent PostgreSQL upsert
            ↓
    execution_stress_scores

CRITICAL SAFETY & ISOLATION RULES:
1. OFFLINE EXECUTION ONLY.
2. Never import ML dependencies into backend runtime.
3. Never expose or log DATABASE_URL, passwords, or connection strings.
4. Idempotent upsert via PostgreSQL:
   ON CONFLICT (project_id, report_month) DO UPDATE.
5. All writes occur in an explicit database transaction with automatic rollback on error.
"""

import argparse
from decimal import Decimal
import logging
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, func, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, sessionmaker

# Ensure ai-ml and backend paths are importable in offline execution
AI_ML_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = AI_ML_ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(AI_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ML_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Import Surveillance Engine and contracts from Phase 5C-1
from ml.surveillance import (
    ACTION_CRITICAL_PATH_RECALIBRATION,
    ACTION_DATA_COMPLIANCE_DIRECTIVE,
    ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
    ACTION_INTER_MINISTERIAL_ESCALATION,
    ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
    ACTION_SITE_OBSTACLE_AUDIT,
    EXECUTION_INDEX_VERSION,
    OUTPUT_SURVEILLANCE_COLUMNS,
    REQUIRED_SURVEILLANCE_FEATURES,
    STRESSOR_EXPENDITURE_DIVERGENCE,
    STRESSOR_PROGRESS_STAGNATION,
    STRESSOR_REPORTING_FRICTION,
    STRESSOR_SCHEDULE_SLIPPAGE,
    STRESSOR_VELOCITY_COLLAPSE,
    TIER_ATTENTION,
    TIER_HIGH_PRIORITY,
    TIER_NOMINAL,
    TIER_WATCH,
    ExecutionSurveillanceEngine,
    InvalidInputError,
    MissingFeatureError,
    SurveillanceError,
)

# Import SQLAlchemy ORM Models & Enums from backend
from app.models.execution import ExecutionStressScore
from app.models.project import Project
from app.models.enums import DominantStressorEnum, EsiTierEnum, PrescriptiveActionEnum


# Setup safe logging (no credentials)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("surveillance_ingestion")


# ------------------------------------------------------------------------------
# Custom Ingestion Exceptions
# ------------------------------------------------------------------------------
class IngestionError(Exception):
    """Base exception for all surveillance score ingestion errors."""
    pass


class BatchValidationError(IngestionError):
    """Raised when surveillance records fail schema or data validation."""
    pass


class BatchDuplicateKeyError(IngestionError):
    """Raised when in-batch duplicate (project_id, report_month) keys are detected."""
    pass


class MissingProjectError(IngestionError):
    """Raised when project_id does not exist in projects master table."""
    pass


class DatabaseIngestionError(IngestionError):
    """Raised when database transaction fails."""
    pass


# ------------------------------------------------------------------------------
# Canonical Constants & Helpers
# ------------------------------------------------------------------------------
MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

VALID_ESI_TIERS: Set[str] = {
    TIER_NOMINAL,
    TIER_WATCH,
    TIER_ATTENTION,
    TIER_HIGH_PRIORITY,
}

VALID_DOMINANT_STRESSORS: Set[str] = {
    STRESSOR_PROGRESS_STAGNATION,
    STRESSOR_VELOCITY_COLLAPSE,
    STRESSOR_EXPENDITURE_DIVERGENCE,
    STRESSOR_SCHEDULE_SLIPPAGE,
    STRESSOR_REPORTING_FRICTION,
}

VALID_PRESCRIPTIVE_ACTIONS: Set[str] = {
    ACTION_SITE_OBSTACLE_AUDIT,
    ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
    ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
    ACTION_CRITICAL_PATH_RECALIBRATION,
    ACTION_DATA_COMPLIANCE_DIRECTIVE,
    ACTION_INTER_MINISTERIAL_ESCALATION,
}

SCORE_NUMERIC_FIELDS: List[str] = [
    "s_stag",
    "s_vel",
    "s_div",
    "s_sched",
    "s_rep",
    "execution_stress_index",
]

FLAG_FIELDS: List[str] = [
    "flag_stag",
    "flag_vel",
    "flag_div",
    "flag_sched",
    "flag_rep",
]


def sanitize_error_message(msg: str) -> str:
    """Removes sensitive database URL or password patterns from error strings."""
    return re.sub(r"://([^:]+):([^@]+)@", "://***:***@", msg)


def resolve_database_url(cli_url: Optional[str] = None) -> str:
    """
    Safely resolves the PostgreSQL DATABASE_URL from CLI argument, OS environment,
    or backend/.env without logging credentials.
    """
    if cli_url:
        return cli_url

    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    env_file = BACKEND_ROOT / ".env"
    if env_file.exists():
        from dotenv import dotenv_values
        values = dotenv_values(env_file)
        if "DATABASE_URL" in values and values["DATABASE_URL"]:
            return values["DATABASE_URL"]

    raise IngestionError("DATABASE_URL is not configured in CLI, environment, or backend/.env.")


def to_decimal_4(val: Any) -> Decimal:
    """Safely converts numeric value to Decimal with exactly 4 decimal places."""
    f_val = round(float(val), 4)
    return Decimal(f"{f_val:.4f}")


# ------------------------------------------------------------------------------
# Validation & Transformation Pipeline
# ------------------------------------------------------------------------------
def validate_surveillance_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Validates the DataFrame returned by ExecutionSurveillanceEngine and transforms
    rows into database-compatible dictionary records.

    Validation Rules:
    1. Output DataFrame must be non-empty.
    2. All required output columns must be present.
    3. project_id must exist in every row (1-32 characters).
    4. report_month must exist in every row and match YYYY-MM format.
    5. In-batch uniqueness: (project_id, report_month) keys must be unique.
    6. All 6 score fields (s_stag, s_vel, s_div, s_sched, s_rep, execution_stress_index)
       must be finite numbers strictly within [0.0, 1.0].
    7. All 5 operational flags must be 0 or 1.
    8. total_stress_flags must be integer in [0, 5] and equal sum of flags.
    9. execution_index_version must equal 'v1.0.0-esi-5dim'.
    10. esi_tier must be a canonical EsiTierEnum value.
    11. dominant_stressor must be a canonical DominantStressorEnum value.
    12. suggested_action must be a canonical PrescriptiveActionEnum value.

    Returns:
        List[Dict[str, Any]]: Clean, typed records ready for SQLAlchemy insert.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise BatchValidationError("Surveillance DataFrame is empty or not a pandas DataFrame.")

    # 1. Required column presence
    missing_cols = [col for col in OUTPUT_SURVEILLANCE_COLUMNS if col not in df.columns]
    if missing_cols:
        raise BatchValidationError(f"Missing required surveillance output columns: {missing_cols}")

    # 2. In-batch duplicate key detection
    key_pairs = list(zip(df["project_id"].astype(str), df["report_month"].astype(str)))
    if len(key_pairs) != len(set(key_pairs)):
        duplicates = [pair for pair in set(key_pairs) if key_pairs.count(pair) > 1]
        raise BatchDuplicateKeyError(
            f"Detected {len(duplicates)} duplicate (project_id, report_month) composite keys in input batch: "
            f"{duplicates[:5]} (showing up to 5)"
        )

    validated_records: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        # Project ID
        pid = str(row["project_id"]).strip()
        if not pid or len(pid) > 32 or pid.lower() == "nan":
            raise BatchValidationError(f"Row {idx}: Invalid project_id '{pid}' (must be non-empty, <= 32 chars).")

        # Report Month
        month = str(row["report_month"]).strip()
        if not MONTH_REGEX.match(month):
            raise BatchValidationError(f"Row {idx} [Project {pid}]: Invalid report_month '{month}' (must match YYYY-MM).")

        # Score fields validation & Decimal(6,4) conversion
        row_numeric_decimals: Dict[str, Decimal] = {}
        for f in SCORE_NUMERIC_FIELDS:
            val = row[f]
            if pd.isna(val) or np.isnan(val) or np.isinf(val):
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{f}' is NaN or Inf.")
            f_val = float(val)
            if f_val < 0.0 or f_val > 1.0:
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{f}' = {f_val} is out of bounds [0.0, 1.0].")
            row_numeric_decimals[f] = to_decimal_4(f_val)

        # Operational flags validation (0 or 1)
        row_flags: Dict[str, int] = {}
        for flg in FLAG_FIELDS:
            f_raw = row[flg]
            if pd.isna(f_raw):
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{flg}' is NaN.")
            try:
                f_flt = float(f_raw)
            except (ValueError, TypeError):
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{flg}' = {f_raw} cannot be parsed as a number.")
            if f_flt not in (0.0, 1.0):
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{flg}' = {f_raw} must be 0 or 1.")
            row_flags[flg] = int(f_flt)

        # Total stress flags validation
        tot_raw = row["total_stress_flags"]
        if pd.isna(tot_raw):
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: 'total_stress_flags' is NaN.")
        try:
            tot_int = int(tot_raw)
        except (ValueError, TypeError):
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: 'total_stress_flags' = {tot_raw} cannot be cast to integer.")
        if tot_int < 0 or tot_int > 5:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: 'total_stress_flags' = {tot_int} is out of bounds [0, 5].")
        expected_tot = sum(row_flags.values())
        if tot_int != expected_tot:
            raise BatchValidationError(
                f"Row {idx} [Project {pid}, {month}]: 'total_stress_flags' ({tot_int}) does not match sum of flags ({expected_tot})."
            )

        # ESI Tier validation
        tier = str(row["esi_tier"]).strip()
        if tier not in VALID_ESI_TIERS:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid esi_tier '{tier}'. Expected one of {sorted(VALID_ESI_TIERS)}.")

        # Dominant Stressor validation
        stressor = str(row["dominant_stressor"]).strip()
        if stressor not in VALID_DOMINANT_STRESSORS:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid dominant_stressor '{stressor}'. Expected one of {sorted(VALID_DOMINANT_STRESSORS)}.")

        # Suggested Action validation
        action = str(row["suggested_action"]).strip()
        if action not in VALID_PRESCRIPTIVE_ACTIONS:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid suggested_action '{action}'. Expected one of {sorted(VALID_PRESCRIPTIVE_ACTIONS)}.")

        # Version validation
        ver = str(row["execution_index_version"]).strip()
        if ver != EXECUTION_INDEX_VERSION:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid execution_index_version '{ver}'. Expected '{EXECUTION_INDEX_VERSION}'.")

        record: Dict[str, Any] = {
            "project_id": pid,
            "report_month": month,
            "s_stag": row_numeric_decimals["s_stag"],
            "s_vel": row_numeric_decimals["s_vel"],
            "s_div": row_numeric_decimals["s_div"],
            "s_sched": row_numeric_decimals["s_sched"],
            "s_rep": row_numeric_decimals["s_rep"],
            "flag_stag": row_flags["flag_stag"],
            "flag_vel": row_flags["flag_vel"],
            "flag_div": row_flags["flag_div"],
            "flag_sched": row_flags["flag_sched"],
            "flag_rep": row_flags["flag_rep"],
            "total_stress_flags": tot_int,
            "execution_stress_index": row_numeric_decimals["execution_stress_index"],
            "esi_tier": EsiTierEnum(tier),
            "dominant_stressor": DominantStressorEnum(stressor),
            "suggested_action": PrescriptiveActionEnum(action),
            "execution_index_version": ver,
        }
        validated_records.append(record)

    return validated_records


# ------------------------------------------------------------------------------
# Foreign Key Safety Check
# ------------------------------------------------------------------------------
def verify_project_foreign_keys(session: Session, records: List[Dict[str, Any]], chunk_size: int = 1000) -> None:
    """
    Verifies that all project_ids in the batch exist in the canonical projects table.
    Fails safely before executing the upsert if any project is missing.

    Raises:
        MissingProjectError: If any project_id does not exist in projects.
    """
    if not records:
        return

    batch_project_ids = list({r["project_id"] for r in records})
    existing_project_ids: Set[str] = set()

    for i in range(0, len(batch_project_ids), chunk_size):
        chunk = batch_project_ids[i : i + chunk_size]
        found = session.execute(
            select(Project.project_id).where(Project.project_id.in_(chunk))
        ).scalars().all()
        existing_project_ids.update(found)

    missing = set(batch_project_ids) - existing_project_ids
    if missing:
        missing_sample = sorted(list(missing))[:5]
        raise MissingProjectError(
            f"Foreign key verification failed: {len(missing)} project(s) do not exist in 'projects' master table: "
            f"{missing_sample} (showing up to 5). Cannot proceed with upsert."
        )


# ------------------------------------------------------------------------------
# Idempotent Database Upsert Engine
# ------------------------------------------------------------------------------
def upsert_execution_stress_scores(
    session: Session,
    records: List[Dict[str, Any]],
    chunk_size: int = 1000,
) -> Dict[str, int]:
    """
    Executes an atomic, idempotent PostgreSQL upsert into execution_stress_scores using
    ON CONFLICT (project_id, report_month) DO UPDATE.

    Counts exact inserts vs updates by querying existing composite keys in the batch.

    Returns:
        Dict[str, int]: Counts of total, inserted, updated, and skipped rows.
    """
    if not records:
        return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0}

    total_records = len(records)
    inserted_count = 0
    updated_count = 0

    for i in range(0, total_records, chunk_size):
        chunk = records[i : i + chunk_size]
        chunk_keys = [(r["project_id"], r["report_month"]) for r in chunk]

        # Determine existing rows for accurate insert vs update accounting
        existing_keys = set(
            session.execute(
                select(ExecutionStressScore.project_id, ExecutionStressScore.report_month).where(
                    tuple_(ExecutionStressScore.project_id, ExecutionStressScore.report_month).in_(chunk_keys)
                )
            ).all()
        )

        chunk_updated = len(existing_keys)
        chunk_inserted = len(chunk) - chunk_updated

        # Build PostgreSQL INSERT ... ON CONFLICT DO UPDATE statement
        stmt = pg_insert(ExecutionStressScore).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_esi_project_month",
            set_={
                "s_stag": stmt.excluded.s_stag,
                "s_vel": stmt.excluded.s_vel,
                "s_div": stmt.excluded.s_div,
                "s_sched": stmt.excluded.s_sched,
                "s_rep": stmt.excluded.s_rep,
                "flag_stag": stmt.excluded.flag_stag,
                "flag_vel": stmt.excluded.flag_vel,
                "flag_div": stmt.excluded.flag_div,
                "flag_sched": stmt.excluded.flag_sched,
                "flag_rep": stmt.excluded.flag_rep,
                "total_stress_flags": stmt.excluded.total_stress_flags,
                "execution_stress_index": stmt.excluded.execution_stress_index,
                "esi_tier": stmt.excluded.esi_tier,
                "dominant_stressor": stmt.excluded.dominant_stressor,
                "suggested_action": stmt.excluded.suggested_action,
                "execution_index_version": stmt.excluded.execution_index_version,
                "evaluated_at": func.now(),
            },
        )

        session.execute(stmt)
        inserted_count += chunk_inserted
        updated_count += chunk_updated

    return {
        "total": total_records,
        "inserted": inserted_count,
        "updated": updated_count,
        "skipped": 0,
    }


# ------------------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------------------
def run_ingestion(
    feature_file: Path,
    month: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    rollback_test: bool = False,
    database_url: Optional[str] = None,
    reference_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Main orchestration function:
    1. Loads feature dataset.
    2. Runs ExecutionSurveillanceEngine.
    3. Validates output contract & data constraints.
    4. Optionally compares against reference dataset.
    5. Performs idempotent database upsert inside transaction.
    """
    if not feature_file.exists():
        raise FileNotFoundError(f"Feature dataset not found: {feature_file}")

    logger.info(f"Loading feature dataset from {feature_file}...")
    df = pd.read_csv(feature_file, dtype={"project_id": str}, low_memory=False)
    logger.info(f"Loaded {len(df):,} total feature rows.")

    # Apply filters if requested
    if month:
        if not MONTH_REGEX.match(month):
            raise IngestionError(f"Filter month '{month}' must match YYYY-MM.")
        month_col = "report_month" if "report_month" in df.columns else ("prediction_month" if "prediction_month" in df.columns else None)
        if month_col:
            df = df[df[month_col].astype(str) == month]
            logger.info(f"Filtered by month '{month}': {len(df):,} rows remaining.")
        else:
            logger.warning("Neither 'report_month' nor 'prediction_month' column found for filtering.")

    if project_id:
        df = df[df["project_id"].astype(str) == str(project_id)]
        logger.info(f"Filtered by project_id '{project_id}': {len(df):,} rows remaining.")

    if limit is not None and limit > 0:
        df = df.head(limit)
        logger.info(f"Applied limit={limit}: {len(df):,} rows to evaluate.")

    if df.empty:
        logger.warning("No rows matched criteria. Ingestion aborted.")
        return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "sample_records": []}

    # Execute ExecutionSurveillanceEngine
    logger.info("Instantiating ExecutionSurveillanceEngine and computing surveillance metrics...")
    engine_inst = ExecutionSurveillanceEngine()
    scored_df = engine_inst.compute_scores(df)
    logger.info(f"Surveillance calculation completed successfully for {len(scored_df):,} rows.")

    # Optional reference comparison
    if reference_file and reference_file.exists():
        logger.info(f"Comparing computed scores against reference dataset: {reference_file}...")
        ref_df = pd.read_csv(reference_file, dtype={"project_id": str}, low_memory=False)
        m_col = "prediction_month" if "prediction_month" in ref_df.columns else "report_month"
        merged = scored_df.merge(ref_df, left_on=["project_id", "report_month"], right_on=["project_id", m_col], suffixes=("_calc", "_ref"))
        if not merged.empty:
            diff_esi = np.max(np.abs(merged["execution_stress_index_calc"] - merged["execution_stress_index_ref"]))
            logger.info(f"Reference verification: compared {len(merged):,} rows. Max abs ESI difference = {diff_esi:.6f}.")

    # Validate output contract and format records
    logger.info("Validating surveillance output contract, bounds, and detecting duplicate keys...")
    records = validate_surveillance_dataframe(scored_df)
    logger.info(f"Validated {len(records):,} records. All checks passed.")

    # Prepare small sample for reporting
    sample_records = [
        {
            "project_id": r["project_id"],
            "report_month": r["report_month"],
            "execution_stress_index": str(r["execution_stress_index"]),
            "esi_tier": r["esi_tier"].value,
            "dominant_stressor": r["dominant_stressor"].value,
            "suggested_action": r["suggested_action"].value,
        }
        for r in records[:5]
    ]

    if dry_run:
        logger.info("[DRY-RUN] Execution completed. Zero database operations performed.")
        return {
            "total": len(records),
            "inserted": 0,
            "updated": 0,
            "skipped": len(records),
            "sample_records": sample_records,
        }

    # Resolve database URL and execute upsert
    db_url = resolve_database_url(database_url)
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        try:
            # Foreign key safety check
            logger.info("Verifying project foreign keys against master 'projects' table...")
            verify_project_foreign_keys(session, records)
            logger.info("Project foreign keys verified successfully.")

            logger.info("Beginning database transaction for idempotent upsert into 'execution_stress_scores'...")
            counts = upsert_execution_stress_scores(session, records)

            if rollback_test:
                logger.info("[ROLLBACK-TEST] Executing explicit rollback to guarantee zero persistent database mutation.")
                session.rollback()
                logger.info("[ROLLBACK-TEST] Rollback successful. Live database remains 100% untouched.")
                print("\n" + "*" * 50)
                print("ROLLBACK TEST: TRANSACTION ROLLED BACK")
                print("PERSISTENT WRITE: NO")
                print("*" * 50)
            else:
                session.commit()
                logger.info("Transaction committed successfully.")

            counts["sample_records"] = sample_records
            return counts
        except Exception as exc:
            session.rollback()
            sanitized_err = sanitize_error_message(str(exc))
            logger.error(f"Database transaction failed and was rolled back: {sanitized_err}")
            if isinstance(exc, IngestionError):
                raise
            raise DatabaseIngestionError(f"Database upsert failed: {sanitized_err}") from None


# ------------------------------------------------------------------------------
# CLI Entrypoint
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="SIH26103 Offline Execution Surveillance (ESI) Database Ingestion Pipeline"
    )
    parser.add_argument(
        "--feature-file",
        type=Path,
        default=AI_ML_ROOT / "features" / "feature_dataset_v1.csv",
        help="Path to feature dataset CSV (default: ai-ml/features/feature_dataset_v1.csv)",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Specific report month to ingest (YYYY-MM)",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Specific project ID to ingest",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of rows to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and validate scores without connecting or writing to database",
    )
    parser.add_argument(
        "--rollback-test",
        action="store_true",
        help="Execute upsert inside an uncommitted transaction and rollback (verification mode)",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Optional database URL override (otherwise read from environment/backend/.env)",
    )
    parser.add_argument(
        "--verify-reference",
        action="store_true",
        help="Verify freshly computed scores against experiments/execution_risk/execution_stress_scores.csv",
    )

    args = parser.parse_args()

    ref_file = (AI_ML_ROOT / "experiments" / "execution_risk" / "execution_stress_scores.csv") if args.verify_reference else None

    try:
        results = run_ingestion(
            feature_file=args.feature_file,
            month=args.month,
            project_id=args.project_id,
            limit=args.limit,
            dry_run=args.dry_run,
            rollback_test=args.rollback_test,
            database_url=args.database_url,
            reference_file=ref_file,
        )
        print("\n" + "=" * 60)
        print("EXECUTION SURVEILLANCE INGESTION SUMMARY REPORT")
        print("=" * 60)
        print(f"Total Processed       : {results.get('total', 0):,}")
        print(f"Inserted Rows         : {results.get('inserted', 0):,}")
        print(f"Updated Rows          : {results.get('updated', 0):,}")
        print(f"Skipped Rows          : {results.get('skipped', 0):,}")
        print(f"Failed Rows           : 0")
        print(f"Index Version         : {EXECUTION_INDEX_VERSION}")
        if args.month:
            print(f"Month Filter          : {args.month}")
        if args.project_id:
            print(f"Project Filter        : {args.project_id}")

        samples = results.get("sample_records", [])
        if samples:
            print("-" * 60)
            print(f"Sample Prepared Records (showing up to {len(samples)}):")
            for s in samples:
                print(f"  P{s['project_id']} [{s['report_month']}]: ESI={s['execution_stress_index']} | Tier={s['esi_tier']} | Dominant={s['dominant_stressor']} | Action={s['suggested_action']}")
        print("=" * 60)
        sys.exit(0)
    except Exception as exc:
        sanitized = sanitize_error_message(str(exc))
        print("\n" + "!" * 60, file=sys.stderr)
        print(f"INGESTION FAILED: {sanitized}", file=sys.stderr)
        print("!" * 60, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
