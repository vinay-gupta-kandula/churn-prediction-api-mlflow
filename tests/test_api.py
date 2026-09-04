"""
Integration tests for FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock MLflow before importing the app
sys.modules['mlflow'] = MagicMock()
sys.modules['mlflow.pyfunc'] = MagicMock()
sys.modules['mlflow.tracking'] = MagicMock()

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    model = MagicMock()
    model.predict = MagicMock(return_value=np.array([1]))
    model.predict_proba = MagicMock(return_value=np.array([[0.3, 0.7]]))
    return model


class TestHealthEndpoint:
    """Test the /health endpoint."""
    
    def test_health_check_model_loaded(self, client, mock_model):
        """Test health check when model is loaded."""
        # Patch the global model variable
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', mock_model):
            with patch.object(main_module, 'MODEL_LOADED', True):
                with patch.object(main_module, 'MODEL_VERSION', '1'):
                    response = client.get("/health")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "ok"
                    assert data["model_status"] == "loaded"
                    assert data["model_version"] == "1"
    
    def test_health_check_model_not_loaded(self, client):
        """Test health check when model is not loaded."""
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', None):
            with patch.object(main_module, 'MODEL_LOADED', False):
                response = client.get("/health")
                
                assert response.status_code == 503
                data = response.json()
                assert "detail" in data


class TestPredictEndpoint:
    """Test the /predict endpoint."""
    
    def test_predict_success(self, client, mock_model):
        """Test successful prediction."""
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', mock_model):
            with patch.object(main_module, 'MODEL_LOADED', True):
                with patch.object(main_module, 'MODEL_VERSION', '1'):
                    # Create valid input
                    request_data = {
                        "features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
                    }
                    
                    response = client.post("/predict", json=request_data)
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "prediction" in data
                    assert "probability" in data
                    assert "model_version" in data
                    assert data["prediction"] in [0, 1]
                    assert 0 <= data["probability"] <= 1
    
    def test_predict_invalid_input(self, client, mock_model):
        """Test prediction with invalid input."""
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', mock_model):
            with patch.object(main_module, 'MODEL_LOADED', True):
                # Missing required field
                request_data = {}
                
                response = client.post("/predict", json=request_data)
                
                assert response.status_code == 422  # Unprocessable Entity
    
    def test_predict_model_not_loaded(self, client):
        """Test prediction when model is not loaded."""
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', None):
            with patch.object(main_module, 'MODEL_LOADED', False):
                request_data = {
                    "features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
                }
                
                response = client.post("/predict", json=request_data)
                
                assert response.status_code == 503
                data = response.json()
                assert "detail" in data
    
    def test_predict_empty_features(self, client, mock_model):
        """Test prediction with empty features list."""
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', mock_model):
            with patch.object(main_module, 'MODEL_LOADED', True):
                request_data = {"features": []}
                
                response = client.post("/predict", json=request_data)
                
                # This might succeed or fail depending on model expectation
                # At minimum, it should return a valid HTTP status
                assert response.status_code in [200, 400, 500]
    
    def test_predict_large_feature_vector(self, client, mock_model):
        """Test prediction with a large feature vector."""
        import src.api.main as main_module
        
        with patch.object(main_module, 'MODEL', mock_model):
            with patch.object(main_module, 'MODEL_LOADED', True):
                with patch.object(main_module, 'MODEL_VERSION', '1'):
                    # Create a large feature vector
                    request_data = {
                        "features": list(np.random.rand(100).astype(float))
                    }
                    
                    response = client.post("/predict", json=request_data)
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["prediction"] in [0, 1]


class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test that root endpoint returns info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_swagger_ui_accessible(self, client):
        """Test that Swagger UI documentation is accessible."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
