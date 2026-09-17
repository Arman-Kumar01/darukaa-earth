"""Analytics endpoints: site metrics and time-series charts."""
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.analytics import MetricPoint, MonitoringEventResponse, SiteAnalyticsResponse
from app.services.analytics_service import (
    get_monitoring_events,
    get_site_analytics,
    get_site_metrics,
)
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get(
    "/sites/{site_id}/analytics",
    response_model=SiteAnalyticsResponse,
    summary="Get complete site analytics",
    description=(
        "Returns time-series metrics with trend analysis for a specific site. "
        "**DEMO NOTICE**: Data is synthetic and does not represent actual environmental measurements."
    ),
)
def site_analytics(
    site_id: int,
    limit: int = Query(24, ge=1, le=60, description="Number of metric observations to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteAnalyticsResponse:
    return get_site_analytics(db, site_id, limit)


@router.get(
    "/sites/{site_id}/metrics",
    response_model=List[MetricPoint],
    summary="Get raw site metric time-series",
)
def site_metrics(
    site_id: int,
    limit: int = Query(24, ge=1, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MetricPoint]:
    return get_site_metrics(db, site_id, limit)


@router.get(
    "/sites/{site_id}/monitoring-events",
    response_model=List[MonitoringEventResponse],
    summary="Get monitoring events for a site",
)
def site_monitoring_events(
    site_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MonitoringEventResponse]:
    return get_monitoring_events(db, site_id, limit)
