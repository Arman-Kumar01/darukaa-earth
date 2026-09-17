"""Map endpoints: GeoJSON data for Mapbox layers."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.site import SiteGeoJSONCollection
from app.services.auth_service import get_current_user
from app.services.site_service import get_sites_as_geojson

router = APIRouter()


@router.get(
    "/sites",
    response_model=SiteGeoJSONCollection,
    summary="Get all sites as GeoJSON FeatureCollection",
    description=(
        "Returns a GeoJSON FeatureCollection of all site polygons for Mapbox GL JS rendering. "
        "Each Feature includes site metadata as properties."
    ),
)
def map_sites_geojson(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by site status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteGeoJSONCollection:
    return get_sites_as_geojson(db, project_id, status)
