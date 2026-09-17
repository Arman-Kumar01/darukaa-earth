"""Spatial service: PostGIS geometry operations."""

import json
import logging
from typing import Any

from geoalchemy2.functions import (
    ST_X,
    ST_Y,
    ST_Area,
    ST_AsGeoJSON,
    ST_Centroid,
    ST_GeomFromGeoJSON,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def geojson_to_wkt_geometry(geojson_dict: dict[str, Any]) -> str:
    """Convert a GeoJSON geometry dict to a WKT string for PostGIS insertion."""
    return json.dumps(geojson_dict)


def calculate_area_and_centroid(
    db: Session, geojson_str: str
) -> tuple[float, float | None, float | None]:
    """
    Calculate area in hectares and centroid coordinates from a GeoJSON polygon.

    Area calculation strategy:
    - Cast geometry to PostGIS geography type for geodetic (ellipsoid-based) area.
    - ST_Area(geometry::geography) returns square meters.
    - Divide by 10,000 to convert to hectares.
    - This avoids the error of treating geographic degrees as linear units.

    Returns: (area_hectares, centroid_lat, centroid_lng)
    """
    try:
        geom_expr = ST_GeomFromGeoJSON(geojson_str)

        result = db.execute(
            db.query(
                ST_Area(geom_expr.op("::geography")()).label("area_sq_m"),
                ST_Y(ST_Centroid(geom_expr)).label("centroid_lat"),
                ST_X(ST_Centroid(geom_expr)).label("centroid_lng"),
            ).statement
        ).first()

        if result is None:
            return 0.0, None, None

        area_hectares = float(result.area_sq_m) / 10_000.0
        centroid_lat = float(result.centroid_lat) if result.centroid_lat else None
        centroid_lng = float(result.centroid_lng) if result.centroid_lng else None

        return area_hectares, centroid_lat, centroid_lng

    except Exception as e:
        logger.error(f"Error calculating spatial properties: {e}")
        return 0.0, None, None


def geometry_to_geojson(db: Session, geometry_wkb) -> dict[str, Any] | None:
    """
    Convert a PostGIS WKB geometry column value to a GeoJSON dict.
    Uses ST_AsGeoJSON for proper serialization.
    """
    if geometry_wkb is None:
        return None
    try:
        result = db.execute(
            db.query(ST_AsGeoJSON(geometry_wkb).label("geojson")).statement
        ).scalar()
        if result:
            return json.loads(result)
        return None
    except Exception as e:
        logger.error(f"Error converting geometry to GeoJSON: {e}")
        return None
