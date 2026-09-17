"""Monitoring event model for site audit trail."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class EventType(str, enum.Enum):
    """Monitoring event classification."""

    field_survey = "field_survey"
    satellite_review = "satellite_review"
    drone_survey = "drone_survey"
    data_collection = "data_collection"
    stakeholder_meeting = "stakeholder_meeting"
    incident = "incident"


class MonitoringEvent(Base):
    """Discrete monitoring event or observation logged against a site."""

    __tablename__ = "monitoring_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType), default=EventType.field_survey, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    site: Mapped["Site"] = relationship(  # noqa: F821
        "Site", back_populates="monitoring_events"
    )
