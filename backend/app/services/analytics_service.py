"""Analytics service: time-series metrics and dashboard aggregations."""

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.monitoring_event import MonitoringEvent
from app.models.project import Project
from app.models.site import Site
from app.models.site_metric import SiteMetric
from app.schemas.analytics import (
    DashboardSummary,
    MetricPoint,
    MonitoringEventResponse,
    SiteAnalyticsResponse,
)

logger = logging.getLogger(__name__)


def get_site_analytics(db: Session, site_id: int, limit: int = 24) -> SiteAnalyticsResponse:
    """
    Return time-series analytics for a specific site.
    Ordered by recorded_at ascending for charting (oldest first).
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Site {site_id} not found."
        )

    metrics = (
        db.query(SiteMetric)
        .filter(SiteMetric.site_id == site_id)
        .order_by(SiteMetric.recorded_at.asc())
        .limit(limit)
        .all()
    )

    metric_points = [
        MetricPoint(
            recorded_at=m.recorded_at,
            carbon_value=m.carbon_value,
            biodiversity_score=m.biodiversity_score,
            vegetation_index=m.vegetation_index,
            monitoring_score=m.monitoring_score,
        )
        for m in metrics
    ]

    # Calculate aggregates
    latest_carbon = metrics[-1].carbon_value if metrics else None
    latest_biodiversity = metrics[-1].biodiversity_score if metrics else None
    avg_carbon = sum(m.carbon_value for m in metrics) / len(metrics) if metrics else None
    avg_biodiversity = (
        sum(m.biodiversity_score for m in metrics) / len(metrics) if metrics else None
    )

    # Calculate trend (% change from first to last observation)
    carbon_trend = None
    biodiversity_trend = None
    if len(metrics) >= 2:
        first, last = metrics[0], metrics[-1]
        if first.carbon_value and first.carbon_value != 0:
            carbon_trend = ((last.carbon_value - first.carbon_value) / first.carbon_value) * 100
        if first.biodiversity_score and first.biodiversity_score != 0:
            biodiversity_trend = (
                (last.biodiversity_score - first.biodiversity_score) / first.biodiversity_score
            ) * 100

    return SiteAnalyticsResponse(
        site_id=site.id,
        site_name=site.name,
        project_name=site.project.name if site.project else "Unknown",
        metrics=metric_points,
        latest_carbon_value=latest_carbon,
        latest_biodiversity_score=latest_biodiversity,
        avg_carbon_value=round(avg_carbon, 2) if avg_carbon else None,
        avg_biodiversity_score=round(avg_biodiversity, 2) if avg_biodiversity else None,
        carbon_trend=round(carbon_trend, 2) if carbon_trend else None,
        biodiversity_trend=round(biodiversity_trend, 2) if biodiversity_trend else None,
    )


def get_site_metrics(db: Session, site_id: int, limit: int = 24) -> list[MetricPoint]:
    """Return raw metric points for a site."""
    metrics = (
        db.query(SiteMetric)
        .filter(SiteMetric.site_id == site_id)
        .order_by(SiteMetric.recorded_at.asc())
        .limit(limit)
        .all()
    )
    return [
        MetricPoint(
            recorded_at=m.recorded_at,
            carbon_value=m.carbon_value,
            biodiversity_score=m.biodiversity_score,
            vegetation_index=m.vegetation_index,
            monitoring_score=m.monitoring_score,
        )
        for m in metrics
    ]


def get_dashboard_summary(db: Session) -> DashboardSummary:
    """
    Calculate dashboard KPIs from live database records.
    All figures come from the database — nothing is hard-coded.
    """
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_sites = db.query(func.count(Site.id)).scalar() or 0
    total_area = db.query(func.coalesce(func.sum(Site.area_hectares), 0.0)).scalar() or 0.0
    active_sites = db.query(func.count(Site.id)).filter(Site.status == "active").scalar() or 0

    # Average biodiversity from latest metric per site
    latest_metrics_subq = (
        db.query(
            SiteMetric.site_id,
            func.max(SiteMetric.recorded_at).label("max_date"),
        )
        .group_by(SiteMetric.site_id)
        .subquery()
    )
    latest_metric_values = (
        db.query(SiteMetric)
        .join(
            latest_metrics_subq,
            (SiteMetric.site_id == latest_metrics_subq.c.site_id)
            & (SiteMetric.recorded_at == latest_metrics_subq.c.max_date),
        )
        .all()
    )

    avg_biodiversity = 0.0
    total_carbon = 0.0
    if latest_metric_values:
        avg_biodiversity = sum(m.biodiversity_score for m in latest_metric_values) / len(
            latest_metric_values
        )
        total_carbon = sum(
            m.carbon_value
            * (db.query(Site.area_hectares).filter(Site.id == m.site_id).scalar() or 1.0)
            for m in latest_metric_values
        )

    # Recent projects (last 5)
    recent_projects_objs = db.query(Project).order_by(Project.created_at.desc()).limit(5).all()
    recent_projects = [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "project_type": p.project_type,
            "region": p.region,
            "created_at": p.created_at.isoformat(),
        }
        for p in recent_projects_objs
    ]

    # Area by project type
    area_by_type_rows = (
        db.query(
            Project.project_type,
            func.coalesce(func.sum(Site.area_hectares), 0.0).label("total_area"),
        )
        .outerjoin(Site, Site.project_id == Project.id)
        .group_by(Project.project_type)
        .all()
    )
    area_by_project_type = {row.project_type: float(row.total_area) for row in area_by_type_rows}

    return DashboardSummary(
        total_projects=total_projects,
        total_sites=total_sites,
        total_area_hectares=round(float(total_area), 2),
        average_biodiversity_score=round(avg_biodiversity, 2),
        total_carbon_value=round(total_carbon, 2),
        recent_projects=recent_projects,
        area_by_project_type=area_by_project_type,
        active_sites_count=active_sites,
    )


def get_monitoring_events(
    db: Session, site_id: int, limit: int = 20
) -> list[MonitoringEventResponse]:
    """Return recent monitoring events for a site."""
    events = (
        db.query(MonitoringEvent)
        .filter(MonitoringEvent.site_id == site_id)
        .order_by(MonitoringEvent.event_date.desc())
        .limit(limit)
        .all()
    )
    return [
        MonitoringEventResponse(
            id=e.id,
            event_date=e.event_date.isoformat(),
            event_type=e.event_type,
            notes=e.notes,
        )
        for e in events
    ]
