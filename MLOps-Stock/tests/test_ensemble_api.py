import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
from services.ensemble_api.main import app

client = TestClient(app)

@patch("services.ensemble_api.main.fetch_async")
@patch("services.ensemble_api.main.download_model_artifacts")
@patch("os.path.exists")
@patch("joblib.load")
@patch("services.ensemble_api.main.build_decision")
def test_ensemble_predict_success(mock_build_decision, mock_joblib_load, mock_exists, mock_download, mock_fetch_async):
    # Mock return values for the 3 fetch_async calls
    # 1. data_res
    # 2. tft_res
    # 3. lgbm_res
    
    async def mock_fetch(*args, **kwargs):
        url = args[1]
        if "8001" in url:
            return {"features": {"close": [100.0] * 60}}
        elif "8002" in url:
            return {"predicted_t3": 105.0}
        elif "8003" in url:
            return {"predicted_t3": 104.0}
    
    mock_fetch_async.side_effect = mock_fetch
    
    mock_download.return_value = "/tmp/models"
    mock_exists.return_value = True
    
    mock_meta_learner = MagicMock()
    mock_meta_learner.predict.return_value = np.array([104.8])
    mock_joblib_load.return_value = mock_meta_learner
    
    mock_decision_result = MagicMock()
    mock_decision_result.expected_return_pct = 4.8
    mock_decision_result.action = "BUY"
    mock_decision_result.confidence = 0.85
    mock_decision_result.reason = "Strong upward trend predicted"
    mock_build_decision.return_value = mock_decision_result
    
    response = client.get("/predict/VNM")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "VNM"
    assert data["current_price"] == 100.0
    assert data["predicted_t3"] == 104.8
    assert data["expected_return_pct"] == 4.8
    assert data["decision"] == "BUY"

@patch("services.ensemble_api.main.fetch_async")
def test_ensemble_predict_api_failure(mock_fetch_async):
    async def mock_fetch(*args, **kwargs):
        raise Exception("API Connection Refused")
        
    mock_fetch_async.side_effect = mock_fetch
    
    response = client.get("/predict/VNM")
    assert response.status_code == 500
    assert "API Connection Refused" in response.json()["detail"]
