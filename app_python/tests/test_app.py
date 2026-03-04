"""
Unit tests for DevOps Info Service
"""
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestMainEndpoint:
    """Tests for GET / endpoint"""

    def test_root_endpoint_status_code(self):
        """Test that root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_json_structure(self):
        """Test that root endpoint returns correct JSON structure"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()

        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data

    def test_service_info_fields(self):
        """Test service information fields"""
        response = client.get("/")
        data = response.json()

        service = data["service"]
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"

    def test_system_info_fields(self):
        """Test system information fields"""
        response = client.get("/")
        data = response.json()

        system = data["system"]
        assert "hostname" in system
        assert "platform" in system
        assert "platform_version" in system
        assert "architecture" in system
        assert "cpu_count" in system
        assert "python_version" in system

        assert isinstance(system["hostname"], str)
        assert isinstance(system["cpu_count"], int)
        assert isinstance(system["python_version"], str)

    def test_runtime_info_fields(self):
        """Test runtime information fields"""
        response = client.get("/")
        data = response.json()

        runtime = data["runtime"]
        assert "uptime_seconds" in runtime
        assert "uptime_human" in runtime
        assert "current_time" in runtime
        assert "timezone" in runtime

        assert isinstance(runtime["uptime_seconds"], int)
        assert isinstance(runtime["uptime_human"], str)
        assert runtime["timezone"] == "UTC"
        assert runtime["uptime_seconds"] >= 0

    def test_request_info_fields(self):
        """Test request information fields"""
        response = client.get("/")
        data = response.json()

        request_info = data["request"]
        assert "client_ip" in request_info
        assert "user_agent" in request_info
        assert "method" in request_info
        assert "path" in request_info

        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_endpoints_list(self):
        """Test endpoints list structure"""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2

        endpoint_paths = [ep["path"] for ep in endpoints]
        assert "/" in endpoint_paths
        assert "/health" in endpoint_paths


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""

    def test_health_endpoint_status_code(self):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_json_structure(self):
        """Test that health endpoint returns correct JSON structure"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_status_value(self):
        """Test that health status is 'healthy'"""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_uptime_type(self):
        """Test that uptime_seconds is a non-negative integer"""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        response = client.get("/health")
        data = response.json()

        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp


class TestErrorHandling:
    """Tests for error cases"""

    def test_404_not_found(self):
        """Test that non-existent endpoint returns 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"] == "Not Found"

    def test_wrong_method(self):
        """Test that POST to GET endpoint returns 405 or 404"""
        response = client.post("/")
        assert response.status_code in [404, 405]
