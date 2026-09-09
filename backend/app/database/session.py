from typing import Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


def _normalize_database_url(url: Optional[str]) -> Optional[str]:
    """
    Safely normalizes database URL to ensure psycopg2 dialect is used.
    Does not modify the underlying environment variable.
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


_db_url = _normalize_database_url(settings.DATABASE_URL)

engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker[Session]] = None

if _db_url:
    connect_args = {"connect_timeout": 30}
    if "sslmode" not in _db_url:
        connect_args["sslmode"] = "require"

    engine = create_engine(
        _db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_timeout=30,
    )

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
    )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI request-scoped database session dependency.
    Yields an active database session and ensures proper rollback and closure.
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database session factory is not configured. DATABASE_URL is missing or empty."
        )

    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
