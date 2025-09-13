import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_auth_validation_errors():
    """Test authentication validation error handling"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test signup with invalid email
        resp = await ac.post("/auth/signup", json={
            "email": "invalid-email",
            "password": "short",
            "role": "ADMIN"
        })
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data
        assert "details" in data

        # Test login with missing fields
        resp = await ac.post("/auth/login", json={})
        assert resp.status_code == 422


@pytest.mark.anyio
async def test_notes_validation():
    """Test notes validation and error handling"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test create note without auth
        resp = await ac.post("/notes", json={"raw_text": "Test note"})
        assert resp.status_code == 401

        # Test invalid note ID
        resp = await ac.get("/notes/-1")
        assert resp.status_code == 401  # Will fail auth first

        # Test root endpoint
        resp = await ac.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "docs" in data


@pytest.mark.anyio 
async def test_health_endpoint():
    """Test health endpoint returns proper info"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "env" in data