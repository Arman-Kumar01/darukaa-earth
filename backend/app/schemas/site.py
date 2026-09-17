"""Site Pydantic schemas with GeoJSON geometry handling."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.site import SiteStatus


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon geometry."""

    type: str = Field(..., pattern="^Polygon$")
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_coordinates(cls, v: list[list[list[float]]]) -> list[list[list[float]]]:
        """Validate that the polygon has at least 4 coordinate pairs (closed ring)."""
        if not v or len(v) == 0:
            raise ValueError("Polygon must have at least one ring")
        outer_ring = v[0]
        if len(outer_ring) < 4:
            raise ValueError("Polygon ring must have at least 4 coordinate pairs (to close)")
        # Validate coordinate format: [longitude, latitude]
        for coord in outer_ring:
            if len(coord) < 2:
                raise ValueError("Each coordinate must have [longitude, latitude]")
            lng, lat = coord[0], coord[1]
            if not (-180 <= lng <= 180):
                raise ValueError(f"Longitude {lng} out of range [-180, 180]")
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude {lat} out of range [-90, 90]")
        return v


class SiteCreate(BaseModel):
    """Schema for creating a new site with PostGIS polygon."""

    project_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: SiteStatus = SiteStatus.active
    monitoring_date: date | None = None
    geometry: GeoJSONPolygon


class SiteUpdate(BaseModel):
    """Schema for updating site metadata (geometry cannot be changed via this endpoint)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: SiteStatus | None = None
    monitoring_date: date | None = None


class SiteResponse(BaseModel):
    """Full site data with GeoJSON geometry."""

    id: int
    project_id: int
    name: str
    description: str | None
    status: SiteStatus
    geometry: dict[str, Any] | None = None
    area_hectares: float | None
    centroid_lat: float | None
    centroid_lng: float | None
    monitoring_date: date | None
    created_at: datetime
    updated_at: datetime
    # Aggregated from metrics
    latest_carbon_value: float | None = None
    latest_biodiversity_score: float | None = None

    model_config = {"from_attributes": True}


class SiteListResponse(BaseModel):
    """Paginated list of sites."""

    data: list[SiteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SiteGeoJSONFeature(BaseModel):
    """GeoJSON Feature for map rendering."""

    type: str = "Feature"
    id: int
    geometry: dict[str, Any]
    properties: dict[str, Any]


class SiteGeoJSONCollection(BaseModel):
    """GeoJSON FeatureCollection for map layers."""

    type: str = "FeatureCollection"
    features: list[SiteGeoJSONFeature]
