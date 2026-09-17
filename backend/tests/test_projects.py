"""Tests for project endpoints."""

from fastapi.testclient import TestClient


class TestProjectCRUD:
    """Test project creation, retrieval, update, and deletion."""

    def test_create_project_success(self, client: TestClient, auth_headers):
        """Authenticated user can create a project."""
        response = client.post(
            "/api/projects",
            json={
                "name": "Test Carbon Project",
                "description": "A test project",
                "project_type": "carbon",
                "region": "Test Region",
                "status": "active",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Carbon Project"
        assert data["project_type"] == "carbon"
        assert data["status"] == "active"
        assert "id" in data

    def test_create_project_unauthenticated(self, client: TestClient):
        """Unauthenticated user cannot create a project."""
        response = client.post(
            "/api/projects",
            json={"name": "Unauthorized Project", "project_type": "carbon"},
        )
        assert response.status_code == 401

    def test_list_projects(self, client: TestClient, auth_headers):
        """Authenticated user can list projects."""
        # Create a project first
        client.post(
            "/api/projects",
            json={"name": "List Test Project", "project_type": "biodiversity"},
            headers=auth_headers,
        )

        response = client.get("/api/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_get_project_by_id(self, client: TestClient, auth_headers):
        """Can retrieve a specific project by ID."""
        # Create project
        create_resp = client.post(
            "/api/projects",
            json={
                "name": "Get By ID Project",
                "project_type": "carbon_biodiversity",
                "region": "Test",
            },
            headers=auth_headers,
        )
        project_id = create_resp.json()["id"]

        response = client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == project_id
        assert response.json()["name"] == "Get By ID Project"

    def test_get_nonexistent_project(self, client: TestClient, auth_headers):
        """Requesting a non-existent project returns 404."""
        response = client.get("/api/projects/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_project(self, client: TestClient, auth_headers):
        """Can update project fields."""
        create_resp = client.post(
            "/api/projects",
            json={"name": "Original Name", "project_type": "carbon"},
            headers=auth_headers,
        )
        project_id = create_resp.json()["id"]

        update_resp = client.put(
            f"/api/projects/{project_id}",
            json={"name": "Updated Name", "status": "completed"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Name"
        assert update_resp.json()["status"] == "completed"

    def test_delete_project(self, client: TestClient, auth_headers):
        """Can delete a project."""
        create_resp = client.post(
            "/api/projects",
            json={"name": "To Delete", "project_type": "carbon"},
            headers=auth_headers,
        )
        project_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
        assert delete_resp.status_code == 200

        get_resp = client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_project_search(self, client: TestClient, auth_headers):
        """Can search projects by name."""
        client.post(
            "/api/projects",
            json={"name": "Unique Search Term XYZ", "project_type": "carbon"},
            headers=auth_headers,
        )

        response = client.get("/api/projects?search=Unique+Search+Term+XYZ", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Unique Search Term XYZ" in p["name"] for p in data["data"])

    def test_project_validation(self, client: TestClient, auth_headers):
        """Empty project name is rejected."""
        response = client.post(
            "/api/projects",
            json={"name": "", "project_type": "carbon"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestHealth:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Health endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
