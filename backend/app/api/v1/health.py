import logging
from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.database.session import engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Health Check")
def health_check():
    """
    Returns service and database health status.
    Verifies database connectivity without crashing if the database is unavailable.
    Never exposes database credentials or internal connection details.
    """
    db_status = "unavailable"
    overall_status = "ok"

    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as exc:
            logger.warning(
                "Database health check failed: %s",
                type(exc).__name__,
            )
            overall_status = "degraded"
    else:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "database": db_status,
    }
