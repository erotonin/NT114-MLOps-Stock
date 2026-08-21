import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
from src.data_pipeline.yahoo_data import YahooData
from src.models_logic.request_validation import normalize_ticker
import pandas as pd
import math

app = FastAPI(title="Data Service API")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "data-api"}

@app.get("/fetch/{ticker}")
def fetch_data(ticker: str, days: int = Query(200, ge=1, le=2000)) -> Dict[str, Any]:
    try:
        symbol = normalize_ticker(ticker)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        data_provider = YahooData()
        df = data_provider.get_historical_data(symbol, days=days)
        if df is None or df.empty:
            raise ValueError(f"No data found for {ticker}")
        
        # Lấp NaN bằng 0 để tránh lỗi JSON
        df = df.fillna(0)
        
        # Chuyển index ngày thành string
        df.index = df.index.astype(str)
        features = df.to_dict(orient="list")
        
        return {
            "ticker": symbol,
            "status": "success",
            "features": features
        }
    except ValueError as e:
        # Known data-quality failures are safe and actionable for the client.
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        # Do not expose provider URLs, filesystem paths or library internals.
        raise HTTPException(status_code=502, detail="data provider unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
# Trigger build
