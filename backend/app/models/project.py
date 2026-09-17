"""Project model."""
import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ProjectType(str, enum.Enum):
    """Project classification by environmental focus."""

    carbon = "carbon"
    biodiversity = "biodiversity"
    carbon_biodiversity = "carbon_biodiversity"


class ProjectStatus(str, enum.Enum):
    """Project lifecycle status."""

    active = "active"
    completed = "completed"
    planned = "planned"
    paused = "paused"


class Project(Base):
    """Environmental project containing multiple monitored sites."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType), default=ProjectType.carbon, nullable=False
    )
    region: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.active, nullable=False
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", back_populates="projects", lazy="select"
    )
    sites: Mapped[list["Site"]] = relationship(  # noqa: F821
        "Site", back_populates="project", cascade="all, delete-orphan", lazy="select"
    )
