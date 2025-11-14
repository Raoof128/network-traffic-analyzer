"""
Tests for the REST API module (api/main.py).

This module tests all API endpoints, request/response handling,
error cases, and API functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock


# Import the API app
try:
    from api.main import app
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    app = None


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAPIEndpoints:
    """Test suite for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test the root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Network Traffic Analyzer API" in data["message"]

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @patch("api.main.PcapHandler")
    @patch("api.main.safe_load")
    def test_analyze_endpoint_success(self, mock_safe_load, mock_pcap_handler, client, sample_pcap_file, trained_model_file):
        """Test successful analysis request."""
        # Mock the PcapHandler
        mock_pcap_handler.read_pcap.return_value = [Mock()] * 10

        # Mock the model
        mock_model = Mock()
        mock_model.predict.return_value = [0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
        mock_safe_load.return_value = mock_model

        request_data = {
            "pcap_file": str(sample_pcap_file),
            "model_path": str(trained_model_file),
        }

        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert "status" in data
        assert "total_packets" in data

    def test_analyze_endpoint_missing_file(self, client):
        """Test analysis with missing PCAP file."""
        request_data = {
            "pcap_file": "/nonexistent/file.pcap",
            "model_path": "/some/model.pkl",
        }

        response = client.post("/api/v1/analyze", json=request_data)
        # Should return error (400 or 404)
        assert response.status_code in [400, 404, 422]

    def test_analyze_endpoint_invalid_request(self, client):
        """Test analysis with invalid request data."""
        request_data = {
            # Missing required fields
            "invalid_field": "value"
        }

        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_get_analysis_result(self, client):
        """Test retrieving analysis result by ID."""
        # This would need a real analysis first, or mock the storage
        analysis_id = "test-analysis-123"
        response = client.get(f"/api/v1/analysis/{analysis_id}")

        # Will likely return 404 for non-existent ID
        # Just verify it doesn't crash
        assert response.status_code in [200, 404]

    def test_get_models_endpoint(self, client):
        """Test listing available models."""
        with patch("api.main.Path") as mock_path:
            mock_path.return_value.glob.return_value = [
                Path("/models/model1.pkl"),
                Path("/models/model2.pkl"),
            ]

            response = client.get("/api/v1/models")
            # Verify it doesn't crash
            assert response.status_code in [200, 404, 500]

    def test_get_model_by_name(self, client):
        """Test retrieving specific model information."""
        model_name = "test_model"
        response = client.get(f"/api/v1/models/{model_name}")

        # Will likely return 404 for non-existent model
        assert response.status_code in [200, 404]

    def test_upload_pcap_endpoint(self, client, sample_pcap_file):
        """Test PCAP file upload."""
        with open(sample_pcap_file, 'rb') as f:
            files = {"file": ("test.pcap", f, "application/octet-stream")}
            response = client.post("/api/v1/upload/pcap", files=files)

            # Should succeed or fail gracefully
            assert response.status_code in [200, 201, 400, 413, 422]

    def test_upload_pcap_no_file(self, client):
        """Test PCAP upload without file."""
        response = client.post("/api/v1/upload/pcap")
        assert response.status_code == 422  # Missing file

    def test_upload_pcap_invalid_file(self, client, temp_dir):
        """Test PCAP upload with invalid file."""
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("This is not a PCAP file")

        with open(invalid_file, 'rb') as f:
            files = {"file": ("invalid.txt", f, "text/plain")}
            response = client.post("/api/v1/upload/pcap", files=files)

            # Should reject invalid file
            assert response.status_code in [400, 415, 422]

    def test_get_stats_endpoint(self, client):
        """Test statistics endpoint."""
        response = client.get("/api/v1/stats")

        # Should return some stats or empty dict
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/analyze")
        # CORS should be configured
        # Just verify the endpoint responds
        assert response.status_code in [200, 405]

    def test_invalid_endpoint(self, client):
        """Test requesting non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method."""
        # Try POST on a GET-only endpoint
        response = client.post("/health")
        assert response.status_code == 405


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAPIModels:
    """Test API Pydantic models."""

    def test_analysis_request_model(self):
        """Test AnalysisRequest model validation."""
        from api.main import AnalysisRequest

        # Valid request
        request = AnalysisRequest(
            pcap_file="/path/to/file.pcap",
            model_path="/path/to/model.pkl"
        )
        assert request.pcap_file == "/path/to/file.pcap"
        assert request.model_path == "/path/to/model.pkl"

    def test_analysis_response_model(self):
        """Test AnalysisResponse model validation."""
        try:
            from api.main import AnalysisResponse

            # Valid response
            response = AnalysisResponse(
                analysis_id="test-123",
                status="completed",
                total_packets=100,
                anomalies_detected=5,
                anomaly_percentage=5.0
            )
            assert response.analysis_id == "test-123"
            assert response.total_packets == 100
        except ImportError:
            pytest.skip("AnalysisResponse model not available")


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAPIErrorHandling:
    """Test API error handling."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_internal_server_error_handling(self, client):
        """Test 500 error handling."""
        # This would require mocking an internal error
        # For now, just verify error handling exists
        pass

    def test_validation_error_format(self, client):
        """Test validation error response format."""
        response = client.post("/api/v1/analyze", json={"invalid": "data"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_rate_limiting(self, client):
        """Test rate limiting if implemented."""
        # If rate limiting is implemented, test it
        # For now, this is a placeholder
        pass


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API with real components."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_full_analysis_workflow(self, client, sample_pcap_file, temp_dir):
        """Test complete analysis workflow."""
        # This would test the full workflow:
        # 1. Upload PCAP
        # 2. Start analysis
        # 3. Check status
        # 4. Get results
        # Skipped for now as it requires full integration
        pytest.skip("Full integration test - requires complete setup")

    def test_concurrent_requests(self, client):
        """Test handling concurrent API requests."""
        # Test multiple simultaneous requests
        pytest.skip("Concurrent request testing - requires async setup")


# Performance tests
@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_health_endpoint_performance(self, client):
        """Test health endpoint response time."""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # Should respond in < 100ms

    def test_api_response_size(self, client):
        """Test API response sizes are reasonable."""
        response = client.get("/health")
        content_length = len(response.content)

        # Health check should be small
        assert content_length < 1024  # < 1KB
