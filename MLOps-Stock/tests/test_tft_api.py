import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
from services.tft_api.main import app

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

@patch("services.tft_api.main.download_model_artifacts")
@patch("os.path.exists")
@patch("joblib.load")
@patch("torch.load")
@patch("services.tft_api.main.TFTSkeleton")
def test_predict_tft_success(mock_tft, mock_torch_load, mock_joblib_load, mock_exists, mock_download, valid_payload):
    mock_download.return_value = "/tmp/models"
    mock_exists.return_value = True
    
    # Mock scalers
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.zeros((60, 13))
    mock_scaler.inverse_transform.return_value = np.array([[108.0]])
    mock_joblib_load.return_value = mock_scaler
    
    # Mock torch model
    mock_model_instance = MagicMock()
    # Mock the __call__ behavior for the model prediction
    mock_tensor = MagicMock()
    mock_tensor.cpu.return_value.numpy.return_value.flatten.return_value = np.array([0.8])
    mock_model_instance.return_value = mock_tensor
    mock_tft.return_value = mock_model_instance
    
    response = client.post("/predict/tft", json=valid_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "Temporal Fusion Transformer"
    assert data["predicted_t3"] == 108.0

@patch("services.tft_api.main.download_model_artifacts")
@patch("os.path.exists")
def test_predict_tft_model_not_found(mock_exists, mock_download, valid_payload):
    mock_download.return_value = "/tmp/models"
    mock_exists.return_value = False
    
    response = client.post("/predict/tft", json=valid_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_t3"] is None
    assert "Model not trained" in data["error"]

@patch("services.tft_api.main.download_model_artifacts")
@patch("os.path.exists")
def test_predict_tft_insufficient_data(mock_exists, mock_download):
    mock_download.return_value = "/tmp/models"
    mock_exists.return_value = True
    
    payload = {
        "ticker": "VNM",
        "features": {
            "open": [100.0] * 10,  # Less than 60
            "high": [105.0] * 10,
            "low": [95.0] * 10,
            "close": [102.0] * 10,
            "volume": [1000] * 10,
            "sma_10": [101.0] * 10,
            "sma_20": [100.5] * 10,
            "rsi": [55.0] * 10,
            "macd": [0.5] * 10,
            "macd_signal": [0.4] * 10,
            "bb_upper": [106.0] * 10,
            "bb_lower": [94.0] * 10,
            "log_return": [0.01] * 10
        }
    }
    
    response = client.post("/predict/tft", json=payload)
    assert response.status_code == 500
    assert "Not enough data" in response.json()["detail"]
