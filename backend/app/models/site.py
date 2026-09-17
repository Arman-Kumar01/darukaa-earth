"""Site model with PostGIS geometry."""

import enum
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SiteStatus(str, enum.Enum):
    """Site monitoring lifecycle status."""

    active = "active"
    completed = "completed"
    planned = "planned"
    inactive = "inactive"


class Site(Base):
    """
    Geospatial monitoring site with PostGIS polygon geometry.

    The geometry column stores POLYGON in EPSG:4326 (WGS84).
    Area is calculated using ST_Area with geography cast for accurate
    geodetic measurement in square meters, then converted to hectares.
    """

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SiteStatus] = mapped_column(
        Enum(SiteStatus), default=SiteStatus.active, nullable=False
    )

    # PostGIS geometry: POLYGON in WGS84 (SRID 4326)
    # This stores the actual spatial polygon drawn by the user
    geometry = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Derived spatial attributes — calculated by PostGIS on creation
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    monitoring_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="sites", lazy="select"
    )
    metrics: Mapped[list["SiteMetric"]] = relationship(  # noqa: F821
        "SiteMetric",
        back_populates="site",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="SiteMetric.recorded_at",
    )
    monitoring_events: Mapped[list["MonitoringEvent"]] = relationship(  # noqa: F821
        "MonitoringEvent",
        back_populates="site",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        # Explicit spatial index (GeoAlchemy2 also creates one via spatial_index=True)
        Index("ix_sites_geometry", "geometry", postgresql_using="gist"),
    )
