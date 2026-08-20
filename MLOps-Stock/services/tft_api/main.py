import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import pandas as pd
import torch
import joblib
from src.models_logic.tft_model import TFTSkeleton
from src.models_logic.model_loader import download_model_artifacts, load_manifest

app = FastAPI(title="TFT Inference Service")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "tft-api"}

class DataPayload(BaseModel):
    ticker: str
    features: Dict[str, List[float]]

@app.post("/predict/tft")
def predict_tft(payload: DataPayload):
    try:
        sym = payload.ticker.upper()
        
        # Tải weights từ MLflow/MinIO (có cache)
        MODELS_DIR = download_model_artifacts(sym)
        
        manifest = load_manifest(MODELS_DIR, sym)
        tft_path = os.path.join(MODELS_DIR, f"{sym}_tft_model.pt")
        scaler_x_path = os.path.join(MODELS_DIR, f"{sym}_scaler_x.pkl")
        scaler_y_path = os.path.join(MODELS_DIR, f"{sym}_scaler_y.pkl")
        
        if not os.path.exists(tft_path):
            return {"model": "Temporal Fusion Transformer", "predicted_t3": None, "model_version": manifest.get("model_version", "unknown"), "error": "Model not trained for this ticker"}

        df = pd.DataFrame(payload.features)
        features_list = ['open', 'high', 'low', 'close', 'volume', 'sma_10', 'sma_20', 'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower', 'log_return']
        
        # TFT cần Window Size = 60
        if len(df) < 60:
            raise ValueError("Not enough data to form a 60-day window")
            
        X_raw = df[features_list].values[-60:]
        
        # nosemgrep: ban-pickle-load
        scaler_x = joblib.load(scaler_x_path)
        # nosemgrep: ban-pickle-load
        scaler_y = joblib.load(scaler_y_path)
        
        X_scaled = scaler_x.transform(X_raw)
        X_tensor = torch.FloatTensor(X_scaled).unsqueeze(0)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        tft = TFTSkeleton(num_features=len(features_list)).to(device)
        # nosemgrep: ban-pickle-load
        tft.load_state_dict(torch.load(tft_path, map_location=device, weights_only=True))
        tft.eval()
        
        with torch.no_grad():
            pred_scaled = tft(X_tensor.to(device)).cpu().numpy().flatten()
            
        pred_price = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()[0]
        
        return {
            "model": "Temporal Fusion Transformer",
            "predicted_t3": float(pred_price),
            "model_version": manifest.get("model_version", "unknown"),
            "feature_version": manifest.get("data_version", "unknown"),
            "horizon": int(manifest.get("horizon", 3))
        }
    except FileNotFoundError as e:
        return {"model": "Temporal Fusion Transformer", "predicted_t3": None, "model_version": "unknown", "error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
# Trigger build
