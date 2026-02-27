"""
Tests for health and system endpoints.

Tests GET /health and GET / endpoints.
"""

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, test_client):
        """Test that /health returns 200 OK."""
        response = await test_client.get("/health")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_healthy_status(self, test_client):
        """Test that /health returns healthy status."""
        response = await test_client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_version(self, test_client):
        """Test that /health returns version info."""
        response = await test_client.get("/health")
        data = response.json()

        assert "version" in data
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_env(self, test_client):
        """Test that /health returns environment info."""
        response = await test_client.get("/health")
        data = response.json()

        assert "env" in data


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint_returns_200(self, test_client):
        """Test that / returns 200 OK."""
        response = await test_client.get("/")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_endpoint_returns_service_info(self, test_client):
        """Test that / returns service information."""
        response = await test_client.get("/")
        data = response.json()

        assert "service" in data
        assert data["service"] == "EdAccelerator API"

    @pytest.mark.asyncio
    async def test_root_endpoint_returns_version(self, test_client):
        """Test that / returns version."""
        response = await test_client.get("/")
        data = response.json()

        assert "version" in data
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_root_endpoint_returns_phases(self, test_client):
        """Test that / returns available phases."""
        response = await test_client.get("/")
        data = response.json()

        assert "phases" in data
        assert data["phases"] == ["evaluator", "teacher", "quiz", "review"]


class TestPassageEndpoint:
    """Tests for GET /passage endpoint."""

    @pytest.mark.asyncio
    async def test_passage_endpoint_returns_200(self, test_client):
        """Test that /passage returns 200 OK."""
        response = await test_client.get("/passage")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_passage_endpoint_returns_passage_data(self, test_client):
        """Test that /passage returns passage information."""
        response = await test_client.get("/passage")
        data = response.json()

        assert "title" in data
        assert "content" in data
        assert "difficulty" in data
