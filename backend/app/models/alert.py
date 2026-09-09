from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import AlertSeverityEnum, AlertSourceEnum, AlertStatusEnum

if TYPE_CHECKING:
    from app.models.project import Project


class SystemAlert(Base):
    """
    System Alerts Table.
    Stores operational, threshold, and ML-generated alerts for active infrastructure projects.
    """
    __tablename__ = "system_alerts"
    __table_args__ = (
        UniqueConstraint("project_id", "report_month", "alert_code", name="uq_alert_project_code_month"),
    )

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()")
    )
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    alert_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[AlertSeverityEnum] = mapped_column(
        Enum(AlertSeverityEnum, name="alert_severity_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    alert_source: Mapped[AlertSourceEnum] = mapped_column(
        Enum(AlertSourceEnum, name="alert_source_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AlertStatusEnum] = mapped_column(
        Enum(AlertStatusEnum, name="alert_status_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=AlertStatusEnum.ACTIVE,
        server_default=text("'ACTIVE'"),
        nullable=False,
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    # Inverse relationship to Project
    project: Mapped["Project"] = relationship("Project", back_populates="system_alerts")
