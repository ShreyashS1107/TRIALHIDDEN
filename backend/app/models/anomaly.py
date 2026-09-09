from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import AlertSeverityEnum

if TYPE_CHECKING:
    from app.models.project import Project


class DataAnomalyLog(Base):
    """
    Data Quality & Anomalies Audit Log (The 1,868 rows policy).
    Records anomalies detected during ingestion, ETL, or cross-month delta validation.
    """
    __tablename__ = "data_anomalies_log"

    anomaly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()")
    )
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    flag_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[AlertSeverityEnum] = mapped_column(
        Enum(AlertSeverityEnum, name="alert_severity_enum", create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=AlertSeverityEnum.MEDIUM,
        server_default=text("'MEDIUM'"),
        nullable=False,
    )
    metric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    prior_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    # Inverse relationship to Project
    project: Mapped["Project"] = relationship("Project", back_populates="anomalies")
