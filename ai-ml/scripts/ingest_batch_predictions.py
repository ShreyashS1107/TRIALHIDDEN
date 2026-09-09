"""
Offline Database Ingestion & Pipeline Orchestration Script for SIH26103.

Flow:
    feature snapshot CSV
            ↓
    BatchScorer.score_batch()
            ↓
    validated ML prediction records
            ↓
    SQLAlchemy mapping (Decimal, Enums, UUID)
            ↓
    idempotent PostgreSQL upsert
            ↓
    ml_risk_scores

CRITICAL SAFETY & ISOLATION RULES:
1. OFFLINE EXECUTION ONLY.
2. Never import scikit-learn/joblib into backend runtime.
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

# Import BatchScorer and contracts from Phase 5B-1
from ml.inference.batch_scorer import BatchScorer
from ml.inference.contracts import (
    BAND_HIGH,
    BAND_LOW,
    BAND_MODERATE,
    BAND_VERY_HIGH,
    DOMINANT_COST_OVERRUN,
    DOMINANT_SCHEDULE_DELAY,
    DOMINANT_SCHEDULE_REVISION,
    MODEL_VERSION,
    OUTPUT_COLUMNS,
    InferenceError,
)

# Import SQLAlchemy ORM Model & Enums
from app.models.risk import MLRiskScore
from app.models.enums import DominantComponentEnum, RiskBandEnum


# Setup safe logging (no credentials)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("batch_ingestion")


# ------------------------------------------------------------------------------
# Custom Ingestion Exceptions
# ------------------------------------------------------------------------------
class IngestionError(Exception):
    """Base exception for all batch ingestion errors."""
    pass


class BatchValidationError(IngestionError):
    """Raised when prediction records fail schema or data validation."""
    pass


class BatchDuplicateKeyError(IngestionError):
    """Raised when in-batch duplicate (project_id, report_month) keys are detected."""
    pass


class DatabaseIngestionError(IngestionError):
    """Raised when database transaction fails."""
    pass


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
VALID_RISK_BANDS: Set[str] = {BAND_LOW, BAND_MODERATE, BAND_HIGH, BAND_VERY_HIGH}
VALID_DOMINANT_COMPONENTS: Set[str] = {
    DOMINANT_SCHEDULE_DELAY,
    DOMINANT_COST_OVERRUN,
    DOMINANT_SCHEDULE_REVISION,
}


def sanitize_error_message(msg: str) -> str:
    """Removes sensitive database URL or password patterns from error strings."""
    # Mask postgresql://user:password@host:port/dbname patterns
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

    # Check backend/.env
    env_file = BACKEND_ROOT / ".env"
    if env_file.exists():
        from dotenv import dotenv_values
        values = dotenv_values(env_file)
        if "DATABASE_URL" in values and values["DATABASE_URL"]:
            return values["DATABASE_URL"]

    raise IngestionError("DATABASE_URL is not configured in CLI, environment, or backend/.env.")


# ------------------------------------------------------------------------------
# Validation & Transformation Pipeline
# ------------------------------------------------------------------------------
def validate_prediction_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Validates the DataFrame returned by BatchScorer and transforms rows into
    database-compatible dictionary records.

    Validation Rules:
    1. All required output columns must be present.
    2. Zero duplicate (project_id, report_month) pairs permitted inside the batch.
    3. project_id must be non-empty string <= 32 chars.
    4. report_month must match YYYY-MM format.
    5. All risk metrics and contributions must be valid numbers in [0.0, 1.0], no NaN/inf.
    6. risk_band must be a valid RiskBandEnum value.
    7. dominant_component must be a valid DominantComponentEnum value.
    8. model_version must be non-empty string <= 32 chars.

    Returns:
        List[Dict[str, Any]]: Clean, typed records ready for SQLAlchemy insert.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise BatchValidationError("Prediction DataFrame is empty or not a pandas DataFrame.")

    # 1. Required column presence
    missing_cols = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing_cols:
        raise BatchValidationError(f"Missing required prediction output columns: {missing_cols}")

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
        if not pid or len(pid) > 32:
            raise BatchValidationError(f"Row {idx}: Invalid project_id '{pid}' (must be 1-32 chars).")

        # Report Month
        month = str(row["report_month"]).strip()
        if not MONTH_REGEX.match(month):
            raise BatchValidationError(f"Row {idx} [Project {pid}]: Invalid report_month '{month}' (must match YYYY-MM).")

        # Risk probabilities & contributions validation
        numeric_fields = [
            "schedule_delay_risk",
            "cost_overrun_risk",
            "schedule_revision_risk",
            "selected_integrated_risk",
            "schedule_contribution",
            "cost_contribution",
            "schedule_revision_contribution",
        ]
        row_numeric_decimals: Dict[str, Decimal] = {}
        for f in numeric_fields:
            val = row[f]
            if pd.isna(val) or np.isnan(val) or np.isinf(val):
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{f}' is NaN or Inf.")
            f_val = float(val)
            if f_val < 0.0 or f_val > 1.0:
                raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: '{f}' = {f_val} is out of bounds [0, 1].")
            row_numeric_decimals[f] = Decimal(f"{f_val:.4f}")

        # Risk Band
        r_band = str(row["risk_band"]).strip()
        if r_band not in VALID_RISK_BANDS:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid risk_band '{r_band}'.")

        # Dominant Component
        dom = str(row["dominant_component"]).strip()
        if dom not in VALID_DOMINANT_COMPONENTS:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid dominant_component '{dom}'.")

        # Model Version
        m_ver = str(row["model_version"]).strip()
        if not m_ver or len(m_ver) > 32:
            raise BatchValidationError(f"Row {idx} [Project {pid}, {month}]: Invalid model_version '{m_ver}'.")

        record: Dict[str, Any] = {
            "project_id": pid,
            "report_month": month,
            "schedule_delay_risk": row_numeric_decimals["schedule_delay_risk"],
            "cost_overrun_risk": row_numeric_decimals["cost_overrun_risk"],
            "schedule_revision_risk": row_numeric_decimals["schedule_revision_risk"],
            "selected_integrated_risk": row_numeric_decimals["selected_integrated_risk"],
            "risk_band": RiskBandEnum(r_band),
            "dominant_component": DominantComponentEnum(dom),
            "schedule_contribution": row_numeric_decimals["schedule_contribution"],
            "cost_contribution": row_numeric_decimals["cost_contribution"],
            "schedule_revision_contribution": row_numeric_decimals["schedule_revision_contribution"],
            "model_version": m_ver,
        }
        validated_records.append(record)

    return validated_records


# ------------------------------------------------------------------------------
# Idempotent Database Upsert Engine
# ------------------------------------------------------------------------------
def upsert_ml_risk_scores(
    session: Session,
    records: List[Dict[str, Any]],
    chunk_size: int = 1000,
) -> Dict[str, int]:
    """
    Executes an atomic, idempotent PostgreSQL upsert into ml_risk_scores using
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

    # Process in chunks to prevent parameter limits
    for i in range(0, total_records, chunk_size):
        chunk = records[i : i + chunk_size]
        chunk_keys = [(r["project_id"], r["report_month"]) for r in chunk]

        # Determine existing rows for accurate insert vs update accounting
        existing_keys = set(
            session.execute(
                select(MLRiskScore.project_id, MLRiskScore.report_month).where(
                    tuple_(MLRiskScore.project_id, MLRiskScore.report_month).in_(chunk_keys)
                )
            ).all()
        )

        chunk_updated = len(existing_keys)
        chunk_inserted = len(chunk) - chunk_updated

        # Build PostgreSQL INSERT ... ON CONFLICT DO UPDATE statement
        stmt = pg_insert(MLRiskScore).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_ml_project_month",
            set_={
                "schedule_delay_risk": stmt.excluded.schedule_delay_risk,
                "cost_overrun_risk": stmt.excluded.cost_overrun_risk,
                "schedule_revision_risk": stmt.excluded.schedule_revision_risk,
                "selected_integrated_risk": stmt.excluded.selected_integrated_risk,
                "risk_band": stmt.excluded.risk_band,
                "dominant_component": stmt.excluded.dominant_component,
                "schedule_contribution": stmt.excluded.schedule_contribution,
                "cost_contribution": stmt.excluded.cost_contribution,
                "schedule_revision_contribution": stmt.excluded.schedule_revision_contribution,
                "model_version": stmt.excluded.model_version,
                "scored_at": func.now(),
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
) -> Dict[str, int]:
    """
    Main orchestration function:
    1. Loads feature snapshot.
    2. Runs BatchScorer.
    3. Validates output contract.
    4. Performs idempotent database upsert inside transaction.
    """
    if not feature_file.exists():
        raise FileNotFoundError(f"Feature dataset not found: {feature_file}")

    logger.info(f"Loading feature dataset from {feature_file}...")
    df = pd.read_csv(feature_file, low_memory=False)
    logger.info(f"Loaded {len(df):,} total feature rows.")

    # Apply filters if requested
    if month:
        if not MONTH_REGEX.match(month):
            raise IngestionError(f"Filter month '{month}' must match YYYY-MM.")
        df = df[df["prediction_month"] == month]
        logger.info(f"Filtered by month '{month}': {len(df):,} rows remaining.")

    if project_id:
        df = df[df["project_id"].astype(str) == str(project_id)]
        logger.info(f"Filtered by project_id '{project_id}': {len(df):,} rows remaining.")

    if limit is not None and limit > 0:
        df = df.head(limit)
        logger.info(f"Applied limit={limit}: {len(df):,} rows to score.")

    if df.empty:
        logger.warning("No rows matched criteria. Ingestion aborted.")
        return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0}

    # Execute BatchScorer
    logger.info("Instantiating BatchScorer and generating risk predictions...")
    scorer = BatchScorer()
    scored_df = scorer.score_batch(df)
    logger.info(f"Batch scoring completed successfully for {len(scored_df):,} rows.")

    # Validate output contract and format records
    logger.info("Validating prediction output contract and detecting duplicate keys...")
    records = validate_prediction_dataframe(scored_df)
    logger.info(f"Validated {len(records):,} records. All checks passed.")

    if dry_run:
        logger.info("[DRY-RUN] Execution completed. Zero database operations performed.")
        return {"total": len(records), "inserted": 0, "updated": 0, "skipped": len(records)}

    # Resolve database URL and execute upsert
    db_url = resolve_database_url(database_url)
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        try:
            logger.info("Beginning database transaction for idempotent upsert...")
            counts = upsert_ml_risk_scores(session, records)

            if rollback_test:
                logger.info("[ROLLBACK-TEST] Rolling back transaction to ensure zero persistent mutation.")
                session.rollback()
                logger.info("[ROLLBACK-TEST] Rollback successful. Live database remains 100% untouched.")
            else:
                session.commit()
                logger.info("Transaction committed successfully.")

            return counts
        except Exception as exc:
            session.rollback()
            sanitized_err = sanitize_error_message(str(exc))
            logger.error(f"Database transaction failed and was rolled back: {sanitized_err}")
            raise DatabaseIngestionError(f"Database upsert failed: {sanitized_err}") from None


# ------------------------------------------------------------------------------
# CLI Entrypoint
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="SIH26103 Offline Batch Risk Predictions Ingestion Script"
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
        help="Run inference and validation without writing to database",
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

    args = parser.parse_args()

    try:
        results = run_ingestion(
            feature_file=args.feature_file,
            month=args.month,
            project_id=args.project_id,
            limit=args.limit,
            dry_run=args.dry_run,
            rollback_test=args.rollback_test,
            database_url=args.database_url,
        )
        print("\n" + "=" * 50)
        print("BATCH INGESTION SUMMARY REPORT")
        print("=" * 50)
        print(f"Total Processed : {results.get('total', 0):,}")
        print(f"Inserted Rows   : {results.get('inserted', 0):,}")
        print(f"Updated Rows    : {results.get('updated', 0):,}")
        print(f"Skipped Rows    : {results.get('skipped', 0):,}")
        print(f"Failed Rows     : 0")
        print("=" * 50)
        sys.exit(0)
    except Exception as exc:
        sanitized = sanitize_error_message(str(exc))
        print("\n" + "!" * 50, file=sys.stderr)
        print(f"INGESTION FAILED: {sanitized}", file=sys.stderr)
        print("!" * 50, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
