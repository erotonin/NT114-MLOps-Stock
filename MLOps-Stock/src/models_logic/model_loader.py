"""Model artifact loader with local, MLflow and registry-aware paths.

Resolution order:
1. Explicit local model directory (portable development/offline demo).
2. MLflow run selected by approved model version if configured.
3. Latest MLflow run for backwards compatibility with the old project.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError:  # MLflow is optional for lightweight offline inference images.
    mlflow = None
    MlflowClient = object


CACHE_DIR = os.getenv("MODELS_CACHE_DIR", "/tmp/models")
LOCAL_MODELS_DIR = os.getenv("LOCAL_MODELS_DIR", "models")


def _local_artifacts(symbol: str) -> str | None:
    root = Path(LOCAL_MODELS_DIR)
    manifest = root / f"{symbol}_artifact_manifest.json"
    required = [
        root / f"{symbol}_tft_model.pt",
        root / f"{symbol}_lgbm_model.pkl",
        root / f"{symbol}_scaler_x.pkl",
        root / f"{symbol}_scaler_y.pkl",
    ]
    if not manifest.exists() or not all(item.exists() for item in required):
        return None
    return str(root)


def _copy_mlflow_artifacts(symbol: str, client: MlflowClient, run_id: str) -> str:
    dest_dir = os.path.join(CACHE_DIR, symbol)
    artifacts_dir = os.path.join(dest_dir, "models")
    os.makedirs(dest_dir, exist_ok=True)
    manifest_path = os.path.join(artifacts_dir, f"{symbol}_artifact_manifest.json")
    if not os.path.exists(manifest_path):
        client.download_artifacts(run_id, "models", dest_dir)
    return artifacts_dir


def download_model_artifacts(symbol: str) -> str:
    sym = symbol.upper()
    local = _local_artifacts(sym)
    if local:
        return local

    dest_dir = os.path.join(CACHE_DIR, sym)
    artifacts_dir = os.path.join(dest_dir, "models")
    manifest_path = os.path.join(artifacts_dir, f"{sym}_artifact_manifest.json")
    if os.path.exists(manifest_path):
        return artifacts_dir

    if mlflow is None:
        raise RuntimeError(
            "MLflow is not installed and no local model artifacts were found. "
            "Mount LOCAL_MODELS_DIR or install the training/MLflow dependencies."
        )

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    experiment = client.get_experiment_by_name("stock_ensemble_training")
    if experiment is None:
        raise FileNotFoundError(f"Experiment 'stock_ensemble_training' not found on MLflow server {tracking_uri}")

    approved_version = os.getenv(f"MODEL_VERSION_{sym}") or os.getenv("MODEL_VERSION")
    filter_string = f"params.symbol = '{sym}'"
    runs = client.search_runs(experiment_ids=[experiment.experiment_id], filter_string=filter_string, order_by=["start_time DESC"], max_results=50)
    if approved_version:
        runs = [run for run in runs if run.data.tags.get("model_version") == approved_version or run.data.params.get("model_version") == approved_version]
    if not runs:
        raise FileNotFoundError(f"No approved MLflow run found for symbol '{sym}'")
    return _copy_mlflow_artifacts(sym, client, runs[0].info.run_id)


def load_manifest(model_dir: str, symbol: str) -> dict:
    path = Path(model_dir) / f"{symbol.upper()}_artifact_manifest.json"
    if not path.exists():
        return {"symbol": symbol.upper(), "model_version": "unknown", "features": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"symbol": symbol.upper(), "model_version": "unknown", "features": []}
