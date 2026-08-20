import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import httpx
from services.dashboard_ui.main_web import app

client = TestClient(app)

def test_dashboard_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "predictions" in response.context
    assert response.context["predictions"] == {}

@patch("httpx.AsyncClient.get")
def test_dashboard_predict_success(mock_get):
    mock_response = httpx.Response(200, request=httpx.Request("GET", "http://localhost"), json={
        "ticker": "VNM",
        "current_price": 100.0,
        "predicted_t3": 105.5,
        "expected_return_pct": 5.5,
        "decision": "BUY",
        "metrics": {
            "confidence": 0.85,
            "reason": "Strong trend"
        }
    })
    
    # httpx.AsyncClient.get is an async function
    async def async_mock_get(*args, **kwargs):
        return mock_response
        
    mock_get.side_effect = async_mock_get
    
    response = client.get("/predict?ticker=VNM")
    
    assert mock_get.called, "Mock was NOT called!"
    
    assert response.status_code == 200
    assert response.context["error"] is None, f"Error occurred: {response.context['error']}"
    assert "predictions" in response.context
    preds = response.context["predictions"]
    assert "VNM" in preds
    assert preds["VNM"]["current_price"] == 100.0
    assert preds["VNM"]["predicted_price"] == 105.5
    assert preds["VNM"]["trend"] == "UP"
    assert preds["VNM"]["action"] == "BUY"

@patch("httpx.AsyncClient.get")
def test_dashboard_predict_failure(mock_get):
    async def async_mock_get(*args, **kwargs):
        raise Exception("Connection error")
        
    mock_get.side_effect = async_mock_get
    
    response = client.get("/predict?ticker=VNM")
    
    assert response.status_code == 200 # Returns HTML with error
    assert response.context["error"] is not None
    assert "Không thể kết nối" in response.context["error"]
