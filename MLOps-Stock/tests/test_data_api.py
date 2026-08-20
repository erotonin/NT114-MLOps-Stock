import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
from services.data_api.main import app

client = TestClient(app)

def test_fetch_data_success():
    mock_df = pd.DataFrame({
        'open': [100.0, 101.0],
        'high': [102.0, 103.0],
        'low': [99.0, 100.0],
        'close': [101.0, 102.0],
        'volume': [1000, 1100]
    }, index=pd.date_range("2026-04-01", periods=2))
    
    with patch("services.data_api.main.YahooData") as MockYahooData:
        instance = MockYahooData.return_value
        instance.get_historical_data.return_value = mock_df
        
        response = client.get("/fetch/VNM?days=2")
        assert response.status_code == 200
        data = response.json()
        
        assert data["ticker"] == "VNM"
        assert data["status"] == "success"
        assert "features" in data
        assert "close" in data["features"]
        assert len(data["features"]["close"]) == 2

def test_fetch_data_no_data():
    with patch("services.data_api.main.YahooData") as MockYahooData:
        instance = MockYahooData.return_value
        instance.get_historical_data.return_value = None
        
        response = client.get("/fetch/INVALID")
        assert response.status_code == 500
        assert "No data found" in response.json()["detail"]
