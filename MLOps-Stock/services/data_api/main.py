import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from src.data_pipeline.yahoo_data import YahooData
import pandas as pd
import math

app = FastAPI(title="Data Service API")

@app.get("/fetch/{ticker}")
def fetch_data(ticker: str, days: int = 200) -> Dict[str, Any]:
    try:
        data_provider = YahooData()
        df = data_provider.get_historical_data(ticker, days=days)
        if df is None or df.empty:
            raise ValueError(f"No data found for {ticker}")
        
        # Lấp NaN bằng 0 để tránh lỗi JSON
        df = df.fillna(0)
        
        # Chuyển index ngày thành string
        df.index = df.index.astype(str)
        features = df.to_dict(orient="list")
        
        return {
            "ticker": ticker,
            "status": "success",
            "features": features
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
# Trigger build
