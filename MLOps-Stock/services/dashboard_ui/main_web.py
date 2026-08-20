import sys
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Dashboard Web UI")

base_dir = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

ENSEMBLE_API_URL = os.getenv("ENSEMBLE_API_URL", "http://localhost:8080/predict/{}")
CONTROL_API_URL = os.getenv("CONTROL_PUBLIC_URL", os.getenv("CONTROL_API_URL", "http://localhost:8085"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "predictions": {}, "error": None, "control_api_url": CONTROL_API_URL})

@app.get("/predict", response_class=HTMLResponse)
async def predict(request: Request, ticker: str):
    ticker = ticker.upper()
    try:
         # Thay vì gọi hàm Local, Dashboard giờ thuần túy phục vụ giao diện và xin data từ API Gateway
         async with httpx.AsyncClient() as client:
              resp = await client.get(ENSEMBLE_API_URL.format(ticker), timeout=15.0)
              resp.raise_for_status()
              data = resp.json()
         
         # Ánh xạ dữ liệu cho đồng nhất với Template HTML
         predictions = {
             data["ticker"]: {
                 "current_price": data["current_price"],
                 "predicted_price": round(data["predicted_t3"], 2),
                 "trend": "UP" if data["predicted_t3"] > data["current_price"] else "DOWN",
                 "action": data["decision"],
                 "expected_return_pct": round(data["expected_return_pct"], 2),
                 "confidence": data["metrics"]["confidence"],
                 "reason": data["metrics"]["reason"],
                 "model_version": data.get("model_version", "legacy/latest"),
                 "uncertainty_pct": data["metrics"].get("uncertainty_pct", 0.0)
             }
         }
         
         return templates.TemplateResponse(request=request, name="index.html", context={
             "request": request,
             "predictions": predictions,
             "error": None,
             "control_api_url": CONTROL_API_URL
         })
    except httpx.HTTPStatusError as e:
         return templates.TemplateResponse(request=request, name="index.html", context={
             "request": request,
             "predictions": {},
             "error": f"Lỗi từ máy chủ API: {e.response.json().get('detail', str(e))}",
             "control_api_url": CONTROL_API_URL
         })
    except Exception as e:
         import traceback
         traceback.print_exc()
         return templates.TemplateResponse(request=request, name="index.html", context={
             "request": request,
             "predictions": {},
             "error": f"Không thể kết nối đến Máy chủ API: {str(e)}",
             "control_api_url": CONTROL_API_URL
         })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
#Trigger build
