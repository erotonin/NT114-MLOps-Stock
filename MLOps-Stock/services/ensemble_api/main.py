import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import httpx
import asyncio
from fastapi import FastAPI, HTTPException
import numpy as np
import joblib
import json
import redis.asyncio as redis
from src.models_logic.decision_policy import build_decision, DecisionContext
from src.models_logic.model_loader import download_model_artifacts, load_manifest
from src.mlops_control.store import EventStore

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = FastAPI(title="Ensemble API Gateway")
control_store = EventStore(os.getenv("CONTROL_DB_PATH", "artifacts/control_plane.sqlite3"))

# URLs của các Microservices
DATA_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8001/fetch/{}")
TFT_URL = os.getenv("TFT_SERVICE_URL", "http://localhost:8002/predict/tft")
LGBM_URL = os.getenv("LGBM_SERVICE_URL", "http://localhost:8003/predict/lgbm")

async def fetch_async(client, url, payload=None):
    if payload:
        resp = await client.post(url, json=payload, timeout=10.0)
    else:
        resp = await client.get(url, timeout=10.0)
    resp.raise_for_status()
    return resp.json()

@app.get("/predict/{ticker}")
async def ensemble_predict(ticker: str):
    try:
        sym = ticker.upper()
        cache_key = f"predict:{sym}"
        
        # Kiểm tra Cache trước
        try:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                print(f"[Cache Hit] Returning cached prediction for {sym}")
                return json.loads(cached_result)
        except Exception as e:
            print(f"[Redis Error] Failed to read cache for {sym}: {e}")

        async with httpx.AsyncClient() as client:
            # 1. Gọi lấy dữ liệu
            data_res = await fetch_async(client, DATA_URL.format(ticker))
            
            # 2. Bắn request song song cho 2 AI con (TFT và LGBM)
            payload = {"ticker": ticker, "features": data_res["features"]}
            
            tft_task = fetch_async(client, TFT_URL, payload)
            lgbm_task = fetch_async(client, LGBM_URL, payload)
            
            # Dừng 1 điểm để đợi cả 2 trả về (tiết kiệm thời gian rảnh rỗi)
            tft_res, lgbm_res = await asyncio.gather(tft_task, lgbm_task)
            
        tft_price = tft_res.get("predicted_t3")
        lgbm_price = lgbm_res.get("predicted_t3")

        if tft_price is None or lgbm_price is None:
            raise ValueError(f"Model errors: TFT={tft_res.get('error')}, LGBM={lgbm_res.get('error')}")

        # 3. Phân giải bằng Meta-Learner để tìm giá trị cân bằng nhất
        try:
            MODELS_DIR = download_model_artifacts(sym)
            manifest = load_manifest(MODELS_DIR, sym)
            meta_path = os.path.join(MODELS_DIR, f"{sym}_meta_learner.pkl")
            scaler_y_path = os.path.join(MODELS_DIR, f"{sym}_scaler_y.pkl")
        except FileNotFoundError:
            meta_path = None
        
        if meta_path is None or not os.path.exists(meta_path):
             meta_prediction = (tft_price + lgbm_price) / 2
        else:
            # nosemgrep: ban-pickle-load
            meta_learner = joblib.load(meta_path)
            scaler_y_path = locals().get("scaler_y_path")
            if manifest.get("meta_input_space") == "scaled_target" and scaler_y_path and os.path.exists(scaler_y_path):
                scaler_y = joblib.load(scaler_y_path)
                component_scaled = scaler_y.transform(np.array([[tft_price], [lgbm_price]])).reshape(-1)
                meta_scaled = meta_learner.predict(np.array([component_scaled]))[0]
                meta_prediction = scaler_y.inverse_transform(np.array([[meta_scaled]])).flatten()[0]
            else:
                # Backwards-compatible path for old test fixtures/artifacts.
                meta_prediction = meta_learner.predict(np.array([[tft_price, lgbm_price]]))[0]

        features = data_res["features"]
        current_price = features["close"][-1]
        
        uncertainty = abs(tft_price - lgbm_price) / current_price * 100
        
        ctx = DecisionContext(
            current_price=float(current_price),
            predicted_price=float(meta_prediction),
            uncertainty_pct=float(uncertainty)
        )
        
        result = build_decision(ctx)
        
        # Trả về kết quả cuối
        result_dict = {
            "ticker": sym,
            "current_price": float(current_price),
            "model_version": manifest.get("model_version", "unknown") if 'manifest' in locals() else "unknown",
            "feature_version": manifest.get("data_version", "unknown") if 'manifest' in locals() else "unknown",
            "horizon": int(manifest.get("horizon", 3)) if 'manifest' in locals() else 3,
            "predicted_t3": float(meta_prediction),
            "predicted_t3_tft": float(tft_price),
            "predicted_t3_lgbm": float(lgbm_price),
            "expected_return_pct": result.expected_return_pct,
            "decision": result.action,
            "metrics": {
                "confidence": result.confidence,
                "reason": result.reason,
                "uncertainty_pct": uncertainty
            }
        }
        
        try:
            control_store.add_prediction({
                "ticker": sym,
                "horizon": result_dict.get("horizon", 3),
                "current_price": result_dict["current_price"],
                "prediction": result_dict["predicted_t3"],
                "model_version": result_dict.get("model_version", "unknown"),
                "feature_version": result_dict.get("feature_version", "unknown"),
            })
        except Exception as e:
            print(f"[ControlPlane] Failed to log prediction for {sym}: {e}")

        try:
            await redis_client.setex(cache_key, 43200, json.dumps(result_dict))
            print(f"[Cache Miss] Saved prediction to Redis for {sym}")
        except Exception as e:
            print(f"[Redis Error] Failed to write cache for {sym}: {e}")
            
        return result_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
    
# Trigger build
