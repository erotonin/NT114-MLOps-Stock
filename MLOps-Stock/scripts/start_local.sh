#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR"
export LOCAL_MODELS_DIR="${LOCAL_MODELS_DIR:-$ROOT_DIR/models}"
export CONTROL_DB_PATH="${CONTROL_DB_PATH:-$ROOT_DIR/artifacts/control_plane.sqlite3}"
export REGISTRY_PATH="${REGISTRY_PATH:-$ROOT_DIR/artifacts/registry/registry.json}"
mkdir -p "$ROOT_DIR/artifacts" "$ROOT_DIR/models" "$ROOT_DIR/data"

if [[ ! -f "$ROOT_DIR/data/FPT.csv" ]]; then
  echo "No data snapshot found; downloading real Yahoo Finance data..."
  python3 -m src.data_pipeline.download_latest
fi

if [[ ! -f "$ROOT_DIR/models/FPT_artifact_manifest.json" ]]; then
  echo "No model artifact found; training FPT with 10 epochs..."
  RETRAIN_EPOCHS=10 python3 -m src.training.final_ensemble_train --symbol FPT
fi

start_service() {
  local name="$1"; local port="$2"; shift 2
  if curl -fsS "http://127.0.0.1:${port}/docs" >/dev/null 2>&1 || curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
    echo "${name} already listens on ${port}"
    return
  fi
  nohup env "$@" python3 -m uvicorn "services.${name}.main:app" --host 127.0.0.1 --port "$port" >"/tmp/mlops-${name}.log" 2>&1 &
  echo $! >"/tmp/mlops-${name}.pid"
}

start_service control_api 8085 CONTROL_DB_PATH="$CONTROL_DB_PATH" REGISTRY_PATH="$REGISTRY_PATH"
start_service data_api 8001
start_service tft_api 8002 LOCAL_MODELS_DIR="$LOCAL_MODELS_DIR" MLFLOW_TRACKING_URI="file://$ROOT_DIR/mlruns"
start_service lgbm_api 8003 LOCAL_MODELS_DIR="$LOCAL_MODELS_DIR" MLFLOW_TRACKING_URI="file://$ROOT_DIR/mlruns"
nohup env DATA_SERVICE_URL="http://127.0.0.1:8001/fetch/{}" TFT_SERVICE_URL="http://127.0.0.1:8002/predict/tft" LGBM_SERVICE_URL="http://127.0.0.1:8003/predict/lgbm" LOCAL_MODELS_DIR="$LOCAL_MODELS_DIR" CONTROL_DB_PATH="$CONTROL_DB_PATH" python3 -m uvicorn services.ensemble_api.main:app --host 127.0.0.1 --port 8080 >"/tmp/mlops-ensemble_api.log" 2>&1 &
echo $! >"/tmp/mlops-ensemble_api.pid"
nohup env CONTROL_DB_PATH="$CONTROL_DB_PATH" python3 -m uvicorn services.dashboard_ui.main_web:app --host 127.0.0.1 --port 8081 >"/tmp/mlops-dashboard_ui.log" 2>&1 &
echo $! >"/tmp/mlops-dashboard_ui.pid"

sleep 8
for endpoint in http://127.0.0.1:8001/docs http://127.0.0.1:8002/docs http://127.0.0.1:8003/docs http://127.0.0.1:8080/docs http://127.0.0.1:8081/ http://127.0.0.1:8085/health; do
  curl -fsS "$endpoint" >/dev/null && echo "OK $endpoint" || { echo "FAILED $endpoint"; exit 1; }
done

echo "Dashboard: http://127.0.0.1:8081"
echo "Ensemble API: http://127.0.0.1:8080/docs"
echo "Control API: http://127.0.0.1:8085/docs"
