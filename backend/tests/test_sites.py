import os

import pytest
from fastapi.testclient import TestClient

# Determine if we're testing against SQLite (no PostGIS) or PostgreSQL (PostGIS available).
# Spatial tests (site creation, geometry retrieval) are skipped on SQLite since
# PostGIS functions (ST_AsGeoJSON, ST_GeomFromGeoJSON, etc.) are not available.
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test_darukaa.db")
DB_HAS_POSTGIS = not DB_URL.startswith("sqlite")

pgis_only = pytest.mark.skipif(
    not DB_HAS_POSTGIS,
    reason="Requires PostgreSQL + PostGIS (not available in SQLite test DB)",
)

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [77.0, 13.0],
            [77.1, 13.0],
            [77.1, 13.1],
            [77.0, 13.1],
            [77.0, 13.0],
        ]
    ],
}


def create_test_project(client: TestClient, headers: dict, name: str = "Test Project") -> int:
    """Helper: create a project and return its ID."""
    resp = client.post(
        "/api/projects",
        json={"name": name, "project_type": "carbon"},
        headers=headers,
    )
    assert resp.status_code == 201, f"Project creation failed: {resp.text}"
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Site creation tests
# ---------------------------------------------------------------------------


class TestSiteCreation:
    """Tests for POST /api/sites."""

    @pgis_only
    def test_create_site_authenticated_valid_polygon(self, client: TestClient, auth_headers: dict):
        """Authenticated user can create a site with a valid GeoJSON polygon."""
        project_id = create_test_project(client, auth_headers)

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Test Monitoring Site",
                "description": "A test site with valid polygon",
                "status": "active",
                "geometry": VALID_POLYGON,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # Check response structure
        assert "id" in data
        assert data["name"] == "Test Monitoring Site"
        assert data["description"] == "A test site with valid polygon"
        assert data["status"] == "active"
        assert data["project_id"] == project_id

        # Spatial fields — may be None on SQLite test DB (no PostGIS), non-None on PostgreSQL
        assert "area_hectares" in data
        assert "centroid_lat" in data
        assert "centroid_lng" in data

        # geometry is None on SQLite (no PostGIS ST_AsGeoJSON) or a dict on PostgreSQL
        assert data["geometry"] is None or isinstance(data["geometry"], dict)

        # Timestamps must be present
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_site_unauthenticated(self, client: TestClient, auth_headers: dict):
        """Unauthenticated request returns 401."""
        project_id = create_test_project(client, auth_headers)

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Unauthorized Site",
                "geometry": VALID_POLYGON,
            },
        )
        assert resp.status_code == 401

    def test_create_site_missing_project(self, client: TestClient, auth_headers: dict):
        """Creating a site for a non-existent project returns 404."""
        resp = client.post(
            "/api/sites",
            json={
                "project_id": 999999,
                "name": "Orphan Site",
                "geometry": VALID_POLYGON,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert "999999" in resp.json()["detail"]

    def test_create_site_invalid_geojson_type(self, client: TestClient, auth_headers: dict):
        """Invalid GeoJSON type (not Polygon) is rejected with 422."""
        project_id = create_test_project(client, auth_headers, "GeoJSON Type Test Project")

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Bad GeoJSON Site",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[77.0, 13.0], [77.1, 13.0]],
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_site_invalid_polygon_too_few_vertices(
        self, client: TestClient, auth_headers: dict
    ):
        """Polygon with fewer than 4 coordinate pairs is rejected with 422."""
        project_id = create_test_project(client, auth_headers, "Too Few Vertices Project")

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Triangle Site",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[77.0, 13.0], [77.1, 13.0], [77.0, 13.0]]  # only 3 points
                    ],
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_site_invalid_coordinates_out_of_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Coordinates outside valid lat/lng range are rejected with 422."""
        project_id = create_test_project(client, auth_headers, "Out of Range Project")

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Impossible Location Site",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [200.0, 13.0],  # longitude 200 is invalid
                            [77.1, 13.0],
                            [77.1, 13.1],
                            [77.0, 13.1],
                            [200.0, 13.0],
                        ]
                    ],
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_site_missing_name(self, client: TestClient, auth_headers: dict):
        """Site with empty name is rejected with 422."""
        project_id = create_test_project(client, auth_headers, "Missing Name Project")

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "",
                "geometry": VALID_POLYGON,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_site_missing_geometry(self, client: TestClient, auth_headers: dict):
        """Site payload without geometry is rejected with 422."""
        project_id = create_test_project(client, auth_headers, "Missing Geom Project")

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "No Geometry Site",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pgis_only
    def test_create_site_response_serialization(self, client: TestClient, auth_headers: dict):
        """Created site response has all required fields with correct types."""
        project_id = create_test_project(client, auth_headers, "Serialization Test Project")

        resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Serialization Test Site",
                "status": "planned",
                "monitoring_date": "2024-06-01",
                "geometry": VALID_POLYGON,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()

        # All fields from SiteResponse schema must be present
        required_fields = [
            "id",
            "project_id",
            "name",
            "description",
            "status",
            "area_hectares",
            "centroid_lat",
            "centroid_lng",
            "monitoring_date",
            "created_at",
            "updated_at",
            "latest_carbon_value",
            "latest_biodiversity_score",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        assert data["status"] == "planned"
        assert data["monitoring_date"] == "2024-06-01"
        assert data["latest_carbon_value"] is None  # No metrics yet
        assert data["latest_biodiversity_score"] is None


# ---------------------------------------------------------------------------
# Site retrieval tests
# ---------------------------------------------------------------------------


class TestSiteRetrieval:
    """Tests for GET /api/sites and GET /api/sites/{id}."""

    @pgis_only
    def test_get_site_by_id(self, client: TestClient, auth_headers: dict):
        """Can retrieve a created site by its ID."""
        project_id = create_test_project(client, auth_headers, "Retrieval Project")

        # Create site
        create_resp = client.post(
            "/api/sites",
            json={
                "project_id": project_id,
                "name": "Retrievable Site",
                "geometry": VALID_POLYGON,
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        site_id = create_resp.json()["id"]

        # Retrieve by ID — this was the critical failing endpoint
        get_resp = client.get(f"/api/sites/{site_id}", headers=auth_headers)
        assert (
            get_resp.status_code == 200
        ), f"GET /api/sites/{site_id} returned {get_resp.status_code}: {get_resp.text}"
        data = get_resp.json()
        assert data["id"] == site_id
        assert data["name"] == "Retrievable Site"

    @pgis_only
    def test_list_sites(self, client: TestClient, auth_headers: dict):
        """Authenticated user can list all sites."""
        project_id = create_test_project(client, auth_headers, "List Sites Project")

        # Create two sites
        for i in range(2):
            client.post(
                "/api/sites",
                json={
                    "project_id": project_id,
                    "name": f"List Test Site {i}",
                    "geometry": VALID_POLYGON,
                },
                headers=auth_headers,
            )

        resp = client.get("/api/sites", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pgis_only
    def test_list_sites_filter_by_project(self, client: TestClient, auth_headers: dict):
        """Can filter sites by project_id."""
        project_id = create_test_project(client, auth_headers, "Filter Project")
        client.post(
            "/api/sites",
            json={"project_id": project_id, "name": "Filtered Site", "geometry": VALID_POLYGON},
            headers=auth_headers,
        )

        resp = client.get(f"/api/sites?project_id={project_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(s["project_id"] == project_id for s in data["data"])

    @pgis_only
    def test_get_nonexistent_site(self, client: TestClient, auth_headers: dict):
        """Requesting a non-existent site returns 404."""
        resp = client.get("/api/sites/99999", headers=auth_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Map/GeoJSON endpoint tests
# ---------------------------------------------------------------------------


class TestMapEndpoints:
    """Tests for /api/map/sites GeoJSON endpoint."""

    @pgis_only
    def test_map_sites_returns_geojson_collection(self, client: TestClient, auth_headers: dict):
        """Map endpoint returns a GeoJSON FeatureCollection."""
        resp = client.get("/api/map/sites", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert isinstance(data["features"], list)
