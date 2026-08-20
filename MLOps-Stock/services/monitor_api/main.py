"""Periodic model monitoring service.

It preserves the original /metrics and /drift/{ticker} endpoints while adding
PSI-based feature drift, delayed-label performance metrics, persisted events and
policy-controlled retraining requests.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
from fastapi import FastAPI
from prometheus_client import Gauge, generate_latest
from starlette.responses import Response

from src.data_pipeline.yahoo_data import YahooData
from src.mlops_control.alerts import emit_alert
from src.mlops_control.drift import dataframe_drift_summary, feature_drift_report
from src.mlops_control.policy import DriftPolicyConfig, evaluate_policy
from src.mlops_control.retraining import get_retraining_service
from src.mlops_control.store import EventStore

app = FastAPI(title="Model Monitor - Drift and Performance Service", version="1.0.0")
store = EventStore(os.getenv("CONTROL_DB_PATH", "artifacts/control_plane.sqlite3"))
retraining = get_retraining_service()

# Prometheus metrics.
drift_score_gauge = Gauge("model_drift_score", "Share of drifted features", ["ticker"])
drift_detected_gauge = Gauge("model_drift_detected", "Whether actionable drift was detected", ["ticker"])
drifted_features_gauge = Gauge("model_drifted_features_count", "Number of drifted features", ["ticker"])
performance_mae_gauge = Gauge("model_performance_mae", "Rolling MAE after delayed labels", ["ticker"])
performance_da_gauge = Gauge("model_directional_accuracy", "Rolling directional accuracy", ["ticker"])
retrain_trigger_gauge = Gauge("model_retrain_trigger", "Whether policy triggered retraining", ["ticker"])

MONITOR_SYMBOLS = [item.strip().upper() for item in os.getenv("MONITOR_SYMBOLS", "VNM,FPT,VCB,HPG").split(",") if item.strip()]
REFERENCE_DAYS = int(os.getenv("REFERENCE_DAYS", "120"))
CURRENT_DAYS = int(os.getenv("CURRENT_DAYS", "30"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))
MIN_SAMPLES = int(os.getenv("DRIFT_MIN_SAMPLES", "20"))
FEATURES = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi", "macd", "macd_signal",
    "bb_upper", "bb_lower", "log_return",
]
_consecutive_critical: dict[str, int] = {}


def compute_drift(symbol: str) -> dict[str, Any] | None:
    try:
        df = YahooData().get_historical_data(symbol, days=REFERENCE_DAYS + CURRENT_DAYS + 40)
        if df is None or len(df) < REFERENCE_DAYS + CURRENT_DAYS:
            return None
        reference = df.iloc[:REFERENCE_DAYS][FEATURES].reset_index(drop=True)
        current = df.iloc[-CURRENT_DAYS:][FEATURES].reset_index(drop=True)
        metrics = feature_drift_report(reference, current, columns=FEATURES, min_samples=MIN_SAMPLES)
        summary = dataframe_drift_summary(metrics)
        performance = store.performance_summary(symbol, limit=CURRENT_DAYS)
        errors = [row["absolute_error"] for row in store.list_predictions(symbol, CURRENT_DAYS) if row["absolute_error"] is not None]
        if performance.get("mae") is not None and errors:
            performance_payload = {"severity": "warning" if performance["mae"] > 0 else "stable", "current_mae": performance["mae"], "baseline_mae": performance["mae"]}
        else:
            performance_payload = None
        if summary["critical_features"]:
            _consecutive_critical[symbol] = _consecutive_critical.get(symbol, 0) + 1
        else:
            _consecutive_critical[symbol] = 0
        decision = evaluate_policy(
            summary,
            performance=performance_payload,
            consecutive_critical_checks=_consecutive_critical[symbol],
            config=DriftPolicyConfig(min_samples=MIN_SAMPLES),
        )
        result = {"symbol": symbol, "summary": summary, "performance": performance, "decision": decision.as_dict()}
        if decision.action in {"alert", "retrain"}:
            store.add_drift_event(symbol, decision.severity, decision.action, result)
            emit_alert({"ticker": symbol, "severity": decision.severity, "action": decision.action, "reason": decision.reason, "source": "monitor-api", "details": result})
        if decision.action == "retrain":
            retraining.start(symbol, horizon=3, trigger_type="drift")
        return result
    except Exception as exc:
        return {"symbol": symbol, "error": str(exc), "decision": {"severity": "error", "action": "observe"}}


def update_metrics() -> None:
    for symbol in MONITOR_SYMBOLS:
        result = compute_drift(symbol)
        if not result:
            continue
        summary = result.get("summary", {})
        decision = result.get("decision", {})
        performance = result.get("performance", {})
        drift_score_gauge.labels(ticker=symbol).set(float(summary.get("share_drifted") or 0.0))
        drift_detected_gauge.labels(ticker=symbol).set(1 if decision.get("severity") in {"warning", "critical", "critical_pending"} else 0)
        drifted_features_gauge.labels(ticker=symbol).set(len(summary.get("critical_features", [])) + len(summary.get("warning_features", [])))
        if performance.get("mae") is not None:
            performance_mae_gauge.labels(ticker=symbol).set(float(performance["mae"]))
        if performance.get("directional_accuracy") is not None:
            performance_da_gauge.labels(ticker=symbol).set(float(performance["directional_accuracy"]))
        retrain_trigger_gauge.labels(ticker=symbol).set(1 if decision.get("action") == "retrain" else 0)


def background_worker() -> None:
    while True:
        try:
            update_metrics()
        except Exception as exc:
            print(f"[Monitor] worker error: {exc}")
        time.sleep(CHECK_INTERVAL)


@app.on_event("startup")
def startup() -> None:
    threading.Thread(target=background_worker, daemon=True).start()


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type="text/plain; version=0.0.4")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "model-monitor"}


@app.get("/drift/{ticker}")
def get_drift(ticker: str) -> dict[str, Any]:
    result = compute_drift(ticker.upper())
    return result or {"error": f"Could not compute drift for {ticker}"}


@app.get("/events")
def events(ticker: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return store.list_drift_events(ticker=ticker, limit=min(limit, 1000))


@app.get("/alerts/health")
def alert_health() -> dict[str, Any]:
    return {"status": "ok", "mode": "webhook" if os.getenv("ALERT_WEBHOOK_URL") else "local_jsonl", "path": os.getenv("ALERT_LOG_PATH", "artifacts/alerts.jsonl")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8084")))
