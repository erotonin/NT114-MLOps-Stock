import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import pandas as pd
import joblib

from src.models_logic.model_loader import download_model_artifacts, load_manifest

app = FastAPI(title="LightGBM Inference Service")

class DataPayload(BaseModel):
    ticker: str
    features: Dict[str, List[float]]

@app.post("/predict/lgbm")
def predict_lgbm(payload: DataPayload):
    try:
        sym = payload.ticker.upper()
        
        # Tải weights từ MLflow/MinIO (có cache)
        MODELS_DIR = download_model_artifacts(sym)
        
        manifest = load_manifest(MODELS_DIR, sym)
        lgbm_path = os.path.join(MODELS_DIR, f"{sym}_lgbm_model.pkl")
        scaler_x_path = os.path.join(MODELS_DIR, f"{sym}_scaler_x.pkl")
        scaler_y_path = os.path.join(MODELS_DIR, f"{sym}_scaler_y.pkl")
        
        if not os.path.exists(lgbm_path):
            return {"model": "LightGBM", "predicted_t3": None, "model_version": manifest.get("model_version", "unknown"), "error": "Model not trained"}

        df = pd.DataFrame(payload.features)
        features_list = ['open', 'high', 'low', 'close', 'volume', 'sma_10', 'sma_20', 'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower', 'log_return']
        
        # LGBM chỉ cần tham số của ngày cuối cùng
        X_raw = df[features_list].values[-1:]
        
        # nosemgrep: ban-pickle-load
        scaler_x = joblib.load(scaler_x_path)
        # nosemgrep: ban-pickle-load
        scaler_y = joblib.load(scaler_y_path)
        
        X_scaled = scaler_x.transform(X_raw)
        
        # nosemgrep: ban-pickle-load
        lgbm_model = joblib.load(lgbm_path)
        pred_scaled = lgbm_model.predict(X_scaled)
        
        pred_price = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()[0]
        
        return {
            "model": "LightGBM",
            "predicted_t3": float(pred_price),
            "model_version": manifest.get("model_version", "unknown"),
            "feature_version": manifest.get("data_version", "unknown"),
            "horizon": int(manifest.get("horizon", 3))
        }
    except FileNotFoundError as e:
        return {"model": "LightGBM", "predicted_t3": None, "model_version": "unknown", "error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
# Trigger build
