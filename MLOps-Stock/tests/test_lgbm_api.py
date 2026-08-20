import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
from services.lgbm_api.main import app

client = TestClient(app)

@pytest.fixture
def valid_payload():
    return {
        "ticker": "VNM",
        "features": {
            "open": [100.0] * 60,
            "high": [105.0] * 60,
            "low": [95.0] * 60,
            "close": [102.0] * 60,
            "volume": [1000] * 60,
            "sma_10": [101.0] * 60,
            "sma_20": [100.5] * 60,
            "rsi": [55.0] * 60,
            "macd": [0.5] * 60,
            "macd_signal": [0.4] * 60,
            "bb_upper": [106.0] * 60,
            "bb_lower": [94.0] * 60,
            "log_return": [0.01] * 60
        }
    }

@patch("services.lgbm_api.main.download_model_artifacts")
@patch("os.path.exists")
@patch("joblib.load")
def test_predict_lgbm_success(mock_joblib_load, mock_exists, mock_download, valid_payload):
    mock_download.return_value = "/tmp/models"
    mock_exists.return_value = True
    
    # Mock scalers and model
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.zeros((1, 13))
    mock_scaler.inverse_transform.return_value = np.array([[105.5]])
    
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0.5])
    
    mock_joblib_load.side_effect = [mock_scaler, mock_scaler, mock_model]
    
    response = client.post("/predict/lgbm", json=valid_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "LightGBM"
    assert data["predicted_t3"] == 105.5

@patch("services.lgbm_api.main.download_model_artifacts")
@patch("os.path.exists")
def test_predict_lgbm_model_not_found(mock_exists, mock_download, valid_payload):
    mock_download.return_value = "/tmp/models"
    mock_exists.return_value = False
    
    response = client.post("/predict/lgbm", json=valid_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_t3"] is None
    assert "Model not trained" in data["error"]
