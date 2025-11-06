"""SQLAlchemy models supporting telemetry ingestion."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class TelemetryRecord(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(16), index=True)
    entity_id: Mapped[str] = mapped_column(String(32), index=True)
    metric: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))
    source: Mapped[str] = mapped_column(String(32), default="simulator")
    quality: Mapped[float] = mapped_column(Float, default=1.0)

    def as_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "quality": self.quality,
        }


class IsolationAction(Base):
    __tablename__ = "isolation_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leak_pipe_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    valve_id: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    performed_by: Mapped[str] = mapped_column(String(64), default="system")

    def as_dict(self) -> dict[str, object]:
        return {
            "leak_pipe_id": self.leak_pipe_id,
            "valve_id": self.valve_id,
            "action": self.action,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "performed_by": self.performed_by,
        }
