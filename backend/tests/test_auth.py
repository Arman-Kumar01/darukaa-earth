"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient


class TestUserRegistration:
    """Test user registration flow."""

    def test_register_success(self, client: TestClient):
        """User can register with valid credentials."""
        response = client.post(
            "/api/auth/register",
            json={
                "name": "Jane Doe",
                "email": "jane@example.com",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "jane@example.com"
        assert data["user"]["name"] == "Jane Doe"
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

    def test_register_duplicate_email(self, client: TestClient, registered_user):
        """Registration fails with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "name": "Another User",
                "email": registered_user["user"]["email"],
                "password": "AnotherPass123",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """Registration fails with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "name": "Test",
                "email": "not-an-email",
                "password": "ValidPass123",
            },
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Registration fails with password under 8 characters."""
        response = client.post(
            "/api/auth/register",
            json={
                "name": "Test",
                "email": "shortpass@example.com",
                "password": "abc",
            },
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test user login flow."""

    def test_login_success(self, client: TestClient, registered_user):
        """User can log in with correct credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "testuser@example.com"

    def test_login_wrong_password(self, client: TestClient, registered_user):
        """Login fails with incorrect password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword!",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Login fails for non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "SomePass123"},
        )
        assert response.status_code == 401


class TestProtectedRoutes:
    """Test that protected routes require authentication."""

    def test_get_me_with_token(self, client: TestClient, auth_headers):
        """Authenticated user can retrieve their profile."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"

    def test_get_me_without_token(self, client: TestClient):
        """Unauthenticated request to /me returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client: TestClient):
        """Invalid JWT token returns 401."""
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401

    def test_projects_requires_auth(self, client: TestClient):
        """Projects endpoint requires authentication."""
        response = client.get("/api/projects")
        assert response.status_code == 401
