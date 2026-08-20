import pytest
import pandas as pd
import numpy as np
from src.data_pipeline.indicators import add_technical_indicators

def test_add_technical_indicators_none():
    assert add_technical_indicators(None) is None

def test_add_technical_indicators_small_df():
    # If len(df) < 26, it should return df unmodified
    df = pd.DataFrame({"close": [1, 2, 3]})
    res = add_technical_indicators(df)
    assert len(res.columns) == 1
    assert "sma_10" not in res.columns

def test_add_technical_indicators_success():
    # Needs at least 26 rows
    close_prices = np.linspace(100, 200, 30)
    df = pd.DataFrame({"close": close_prices})
    res = add_technical_indicators(df)
    
    assert "sma_10" in res.columns
    assert "sma_20" in res.columns
    assert "rsi" in res.columns
    assert "macd" in res.columns
    assert "macd_signal" in res.columns
    assert "bb_upper" in res.columns
    assert "bb_lower" in res.columns
    assert "log_return" in res.columns
    
    # Check that tail has values
    tail = res.iloc[-1]
    assert not np.isnan(tail["sma_10"])
    assert not np.isnan(tail["macd"])
