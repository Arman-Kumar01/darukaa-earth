"""Site service: business logic for site CRUD with PostGIS geometry."""

import json
import logging
import math

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.site import Site
from app.models.site_metric import SiteMetric
from app.schemas.site import (
    SiteCreate,
    SiteGeoJSONCollection,
    SiteGeoJSONFeature,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
)

logger = logging.getLogger(__name__)


def _get_latest_metrics(db: Session, site_id: int) -> tuple[float | None, float | None]:
    """Return the most recent carbon and biodiversity values for a site."""
    latest = (
        db.query(SiteMetric)
        .filter(SiteMetric.site_id == site_id)
        .order_by(SiteMetric.recorded_at.desc())
        .first()
    )
    if latest:
        return latest.carbon_value, latest.biodiversity_score
    return None, None


def _site_to_response(site: Site, db: Session) -> SiteResponse:
    """Convert a Site ORM object to a SiteResponse with GeoJSON and metrics."""
    geojson = None
    if site.geometry is not None:
        try:
            result = db.execute(
                text("SELECT ST_AsGeoJSON(:geom)"), {"geom": site.geometry}
            ).scalar()
            if result:
                geojson = json.loads(result)
        except Exception as e:
            logger.warning(f"Could not serialize geometry for site {site.id}: {e}")

    latest_carbon, latest_biodiversity = _get_latest_metrics(db, site.id)

    resp = SiteResponse.model_validate(site)
    resp.geometry = geojson
    resp.latest_carbon_value = latest_carbon
    resp.latest_biodiversity_score = latest_biodiversity
    return resp


def _compute_spatial_properties(
    db: Session, geojson_str: str
) -> tuple[float, float | None, float | None]:
    """Use PostGIS to calculate area in hectares and centroid coordinates."""
    try:
        result = db.execute(
            text("""
                SELECT
                    ST_Area(ST_GeomFromGeoJSON(:geojson)::geography) / 10000.0 AS area_ha,
                    ST_Y(ST_Centroid(ST_GeomFromGeoJSON(:geojson))) AS centroid_lat,
                    ST_X(ST_Centroid(ST_GeomFromGeoJSON(:geojson))) AS centroid_lng
            """),
            {"geojson": geojson_str},
        ).first()

        if result:
            return (
                round(float(result.area_ha), 4),
                float(result.centroid_lat),
                float(result.centroid_lng),
            )
    except Exception as e:
        logger.error(f"Spatial calculation error: {e}")
    return 0.0, None, None


def get_sites(
    db: Session,
    project_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
    status_filter: str | None = None,
) -> SiteListResponse:
    """Return paginated sites, optionally filtered by project."""
    query = db.query(Site)
    if project_id:
        query = query.filter(Site.project_id == project_id)
    if status_filter:
        query = query.filter(Site.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size
    sites = query.order_by(Site.created_at.desc()).offset(offset).limit(page_size).all()

    return SiteListResponse(
        data=[_site_to_response(s, db) for s in sites],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if page_size else 1,
    )


def get_site(db: Session, site_id: int) -> SiteResponse:
    """Get a single site by ID."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Site {site_id} not found."
        )
    return _site_to_response(site, db)


def create_site(db: Session, payload: SiteCreate) -> SiteResponse:
    """
    Create a new site with a PostGIS polygon.

    1. Validates that the project exists.
    2. Converts GeoJSON to PostGIS geometry using ST_GeomFromGeoJSON.
    3. Calculates area via ST_Area(geom::geography)/10000 (geodetic hectares).
    4. Calculates centroid via ST_Centroid.
    5. Stores all spatial data in PostGIS.
    """
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {payload.project_id} not found."
        )

    geojson_str = json.dumps(payload.geometry.model_dump())
    area_ha, centroid_lat, centroid_lng = _compute_spatial_properties(db, geojson_str)

    site = Site(
        project_id=payload.project_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        monitoring_date=payload.monitoring_date,
        geometry=f"SRID=4326;{_geojson_to_wkt(payload.geometry.coordinates)}",
        area_hectares=area_ha,
        centroid_lat=centroid_lat,
        centroid_lng=centroid_lng,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    logger.info(f"Site created: {site.name} (id={site.id}), area={area_ha:.2f}ha")
    return _site_to_response(site, db)


def _geojson_to_wkt(coordinates: list) -> str:
    """Convert GeoJSON polygon coordinates array to WKT POLYGON string."""
    rings = []
    for ring in coordinates:
        pairs = ", ".join(f"{coord[0]} {coord[1]}" for coord in ring)
        rings.append(f"({pairs})")
    return f"POLYGON({', '.join(rings)})"


def update_site(db: Session, site_id: int, payload: SiteUpdate) -> SiteResponse:
    """Update site metadata fields."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Site {site_id} not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(site, key, value)

    db.commit()
    db.refresh(site)
    return _site_to_response(site, db)


def delete_site(db: Session, site_id: int) -> dict:
    """Delete a site and its metrics (cascade)."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Site {site_id} not found."
        )
    db.delete(site)
    db.commit()
    return {"detail": "Site deleted successfully."}


def get_sites_as_geojson(
    db: Session,
    project_id: int | None = None,
    status_filter: str | None = None,
) -> SiteGeoJSONCollection:
    """Return all sites as a GeoJSON FeatureCollection for map rendering."""
    query = db.query(Site)
    if project_id:
        query = query.filter(Site.project_id == project_id)
    if status_filter:
        query = query.filter(Site.status == status_filter)

    sites = query.all()
    features = []

    for site in sites:
        geojson = None
        if site.geometry is not None:
            try:
                result = db.execute(
                    text("SELECT ST_AsGeoJSON(:geom)"), {"geom": site.geometry}
                ).scalar()
                if result:
                    geojson = json.loads(result)
            except Exception:
                pass

        if geojson is None:
            continue

        latest_carbon, latest_biodiversity = _get_latest_metrics(db, site.id)

        features.append(
            SiteGeoJSONFeature(
                id=site.id,
                geometry=geojson,
                properties={
                    "id": site.id,
                    "name": site.name,
                    "project_id": site.project_id,
                    "status": site.status,
                    "area_hectares": site.area_hectares,
                    "centroid_lat": site.centroid_lat,
                    "centroid_lng": site.centroid_lng,
                    "monitoring_date": site.monitoring_date.isoformat()
                    if site.monitoring_date
                    else None,
                    "latest_carbon_value": latest_carbon,
                    "latest_biodiversity_score": latest_biodiversity,
                },
            )
        )

    return SiteGeoJSONCollection(features=features)
