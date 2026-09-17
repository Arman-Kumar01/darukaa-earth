"""Analytics and dashboard Pydantic schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MetricPoint(BaseModel):
    """Single time-series data point for charts."""

    recorded_at: datetime
    carbon_value: float
    biodiversity_score: float
    vegetation_index: float
    monitoring_score: float


class SiteAnalyticsResponse(BaseModel):
    """Complete analytics for a site."""

    site_id: int
    site_name: str
    project_name: str
    metrics: List[MetricPoint]
    # Aggregated stats
    latest_carbon_value: Optional[float] = None
    latest_biodiversity_score: Optional[float] = None
    avg_carbon_value: Optional[float] = None
    avg_biodiversity_score: Optional[float] = None
    carbon_trend: Optional[float] = None  # percentage change over period
    biodiversity_trend: Optional[float] = None


class MonitoringEventResponse(BaseModel):
    """Monitoring event for activity feed."""

    id: int
    event_date: str
    event_type: str
    notes: Optional[str]

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    """Aggregated dashboard KPIs computed from database."""

    total_projects: int
    total_sites: int
    total_area_hectares: float
    average_biodiversity_score: float
    total_carbon_value: float
    recent_projects: List[dict]
    area_by_project_type: dict
    active_sites_count: int
