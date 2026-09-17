"""Sites endpoints: CRUD with PostGIS geometry."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.site import SiteCreate, SiteListResponse, SiteResponse, SiteUpdate
from app.services.auth_service import get_current_user
from app.services.site_service import (
    create_site,
    delete_site,
    get_site,
    get_sites,
    update_site,
)

router = APIRouter()


@router.get(
    "",
    response_model=SiteListResponse,
    summary="List all sites",
    description="Returns paginated sites with optional project and status filtering.",
)
def list_sites(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteListResponse:
    return get_sites(db, project_id, page, page_size, status)


@router.post(
    "",
    response_model=SiteResponse,
    status_code=201,
    summary="Create a new site with polygon geometry",
    description=(
        "Creates a site with a GeoJSON Polygon geometry stored in PostGIS. "
        "Area is automatically calculated using ST_Area(geom::geography)/10000 (hectares)."
    ),
)
def create_new_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteResponse:
    return create_site(db, payload)


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Get a site by ID with GeoJSON geometry",
)
def get_site_by_id(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteResponse:
    return get_site(db, site_id)


@router.put(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Update site metadata",
)
def update_site_by_id(
    site_id: int,
    payload: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteResponse:
    return update_site(db, site_id, payload)


@router.delete(
    "/{site_id}",
    summary="Delete a site",
)
def delete_site_by_id(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return delete_site(db, site_id)
