import pytest
from sqlalchemy import inspect, text
from app.core.config import settings
from app.database.session import engine, get_db


def test_database_url_configured():
    """
    Verify DATABASE_URL is configured without exposing its content.
    """
    assert settings.DATABASE_URL is not None, "DATABASE_URL environment variable is not configured."
    assert len(settings.DATABASE_URL.strip()) > 0, "DATABASE_URL is empty."


def test_database_select_one():
    """
    Connect using SQLAlchemy and execute SELECT 1.
    Confirms live connectivity to Supabase PostgreSQL.
    """
    assert engine is not None, "SQLAlchemy engine is not initialized."
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1, f"Expected 1 from SELECT 1, got {result}"


def test_projects_table_exists():
    """
    Safe read-only test checking that the 'projects' table exists in the database.
    Does NOT perform any DDL, INSERT, UPDATE, or DELETE.
    """
    assert engine is not None, "SQLAlchemy engine is not initialized."
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "projects" in table_names, (
        f"Expected table 'projects' to exist in database, but found: {table_names}"
    )


def test_get_db_dependency():
    """
    Verify get_db session dependency yields an active session and closes properly.
    """
    db_gen = get_db()
    session = next(db_gen)
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
