"""Tests for health check endpoints."""

from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get('/api/v1/health/')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'version' in data

    async def test_health_liveness(self, client: AsyncClient):
        """Test Kubernetes liveness probe."""
        response = await client.get('/health/ready')

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data

    async def test_health_readiness(self, client: AsyncClient):
        """Test Kubernetes readiness probe."""
        response = await client.get('/health/ready')

        assert response.status_code == 200

    async def test_health_startup(self, client: AsyncClient):
        """Test Kubernetes startup probe."""
        response = await client.get('/health/startup')

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get('/')

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data or 'version' in data or 'status' in data

    async def test_health_check_response_time(self, client: AsyncClient):
        """Test that health check responds quickly."""
        import time

        start = time.time()
        response = await client.get('/api/v1/health/')
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0

    async def test_multiple_health_checks(self, client: AsyncClient):
        """Test multiple consecutive health checks."""
        for _ in range(5):
            response = await client.get('/api/v1/health/')
            assert response.status_code == 200

    async def test_health_check_headers(self, client: AsyncClient):
        """Test health check response headers."""
        response = await client.get('/api/v1/health/')

        assert response.status_code == 200
        assert 'content-type' in response.headers
        assert 'application/json' in response.headers['content-type']
