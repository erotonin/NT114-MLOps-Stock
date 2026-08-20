"""MLOps control-plane API.

This service is intentionally independent from the legacy prediction gateway.
It can run locally with SQLite and a filesystem registry, and can later be
backed by PostgreSQL/MLflow in the Kubernetes deployment.
"""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.mlops_control.drift import dataframe_drift_summary, feature_drift_report
from src.mlops_control.policy import DriftPolicyConfig, evaluate_policy
from src.mlops_control.registry import Registry
from src.mlops_control.retraining import RetrainingService
from src.mlops_control.store import EventStore

app = FastAPI(title="MLOps Stock Control Plane", version="1.0.0")
_allowed_origins = [item.strip() for item in os.getenv("CONTROL_ALLOWED_ORIGINS", "*").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
store = EventStore(os.getenv("CONTROL_DB_PATH", "artifacts/control_plane.sqlite3"))
registry = Registry(os.getenv("REGISTRY_PATH", "artifacts/registry/registry.json"))
retraining = RetrainingService(store=store, registry=registry)


class PredictionLog(BaseModel):
    ticker: str
    horizon: int = Field(default=3, ge=1, le=30)
    current_price: float | None = None
    prediction: float | None = None
    model_version: str = "unknown"
    feature_version: str = "unknown"
    generated_at: str | None = None


class GroundTruth(BaseModel):
    ground_truth: float


class DriftRequest(BaseModel):
    ticker: str
    reference: list[dict[str, float]]
    current: list[dict[str, float]]
    columns: list[str] | None = None
    performance: dict[str, Any] | None = None
    consecutive_critical_checks: int = 0


class RetrainRequest(BaseModel):
    ticker: str
    horizon: int = Field(default=3, ge=1, le=30)
    trigger_type: str = "manual"
    epochs: int | None = Field(default=None, ge=1, le=200)


class PromoteRequest(BaseModel):
    model_name: str
    version: str
    reason: str = "manual_approval"


ROLE_ORDER = {"viewer": 1, "analyst": 2, "admin": 3}


def require_role(required: str):
    def dependency(x_role: str | None = Header(default=None)) -> str:
        role = (x_role or os.getenv("DEFAULT_ROLE", "viewer")).lower()
        if ROLE_ORDER.get(role, 0) < ROLE_ORDER[required]:
            raise HTTPException(status_code=403, detail=f"role '{role}' cannot perform this action; requires '{required}'")
        return role

    return dependency


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-plane"}


@app.post("/predictions")
def log_prediction(payload: PredictionLog, _: str = Depends(require_role("analyst"))) -> dict[str, Any]:
    return store.add_prediction(payload.model_dump())


@app.get("/predictions")
def get_predictions(ticker: str | None = None, limit: int = 100, _: str = Depends(require_role("viewer"))) -> list[dict[str, Any]]:
    return store.list_predictions(ticker=ticker, limit=min(limit, 1000))


@app.post("/predictions/{prediction_id}/label")
def label_prediction(prediction_id: str, payload: GroundTruth, _: str = Depends(require_role("analyst"))) -> dict[str, Any]:
    result = store.update_ground_truth(prediction_id, payload.ground_truth)
    if result is None:
        raise HTTPException(status_code=404, detail="prediction not found")
    return result


@app.get("/performance")
def performance(ticker: str | None = None, limit: int = 100, _: str = Depends(require_role("viewer"))) -> dict[str, Any]:
    return store.performance_summary(ticker=ticker, limit=min(limit, 1000))


@app.post("/drift/evaluate")
def evaluate_drift(payload: DriftRequest, _: str = Depends(require_role("analyst"))) -> dict[str, Any]:
    reference = pd.DataFrame(payload.reference)
    current = pd.DataFrame(payload.current)
    columns = payload.columns or [column for column in reference.columns if column in current.columns]
    report = feature_drift_report(reference, current, columns=columns)
    summary = dataframe_drift_summary(report)
    decision = evaluate_policy(summary, performance=payload.performance, consecutive_critical_checks=payload.consecutive_critical_checks)
    event = store.add_drift_event(payload.ticker, decision.severity, decision.action, {"summary": summary, "decision": decision.as_dict()})
    return {"summary": summary, "decision": decision.as_dict(), "event": event}


@app.get("/drift/events")
def drift_events(ticker: str | None = None, limit: int = 100, _: str = Depends(require_role("viewer"))) -> list[dict[str, Any]]:
    return store.list_drift_events(ticker=ticker, limit=min(limit, 1000))


@app.post("/retrain")
def trigger_retrain(payload: RetrainRequest, _: str = Depends(require_role("analyst"))) -> dict[str, Any]:
    return retraining.start(payload.ticker, payload.horizon, payload.trigger_type, payload.epochs)


@app.get("/retrain/jobs")
def retrain_jobs(limit: int = 100, _: str = Depends(require_role("viewer"))) -> list[dict[str, Any]]:
    return store.list_jobs(limit=min(limit, 1000))


@app.get("/models")
def models(_: str = Depends(require_role("viewer"))) -> list[dict[str, Any]]:
    return registry.list_models()


@app.get("/models/{model_name}")
def model_detail(model_name: str, _: str = Depends(require_role("viewer"))) -> dict[str, Any]:
    result = registry.get_model(model_name)
    if result is None:
        raise HTTPException(status_code=404, detail="model not found")
    return result


@app.post("/models/promote")
def promote(payload: PromoteRequest, role: str = Depends(require_role("admin"))) -> dict[str, Any]:
    return registry.promote(payload.model_name, payload.version, actor=role, reason=payload.reason)


@app.post("/models/rollback")
def rollback(payload: PromoteRequest, role: str = Depends(require_role("admin"))) -> dict[str, Any]:
    return registry.rollback(payload.model_name, payload.version, actor=role, reason=payload.reason)


@app.get("/audit")
def audit(limit: int = 100, _: str = Depends(require_role("viewer"))) -> list[dict[str, Any]]:
    return registry.audit(limit=min(limit, 1000))
