"""Site metrics model for time-series analytics."""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SiteMetric(Base):
    """
    Time-series environmental metrics for a site.

    DEMO NOTICE: Values in the seed data are synthetic and illustrative.
    They do not represent real environmental measurements.
    """

    __tablename__ = "site_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Environmental metrics (synthetic for demo)
    carbon_value: Mapped[float] = mapped_column(Float, nullable=False, comment="tCO2e/ha")
    biodiversity_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="0-100 index"
    )
    vegetation_index: Mapped[float] = mapped_column(
        Float, nullable=False, comment="NDVI proxy 0-1"
    )
    monitoring_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="0-100 monitoring completeness"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    site: Mapped["Site"] = relationship("Site", back_populates="metrics")  # noqa: F821
