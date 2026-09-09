from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import (
    DateTime,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CompletedProject(Base):
    """
    Completed Projects Archive Table.
    Holds historical completed projects as reported in Flash Reports.
    Independent historical entity with no active operational foreign keys.
    """
    __tablename__ = "completed_projects"

    project_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    agency: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    original_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    actual_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    cumulative_expenditure_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    actual_completion_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    source_file: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )


class NewlyAddedProject(Base):
    """
    Newly Added Projects Intake Table.
    Logs newly inducted infrastructure projects during report epoch ingestion.
    Independent staging entity with no active operational foreign keys.
    """
    __tablename__ = "newly_added_projects"

    intake_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()")
    )
    project_id: Mapped[str] = mapped_column(String(32), nullable=False)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    agency: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    original_cost_crore: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    approval_start_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    original_completion_date: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    source_file: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
