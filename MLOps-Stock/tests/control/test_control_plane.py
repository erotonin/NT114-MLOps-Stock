from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.mlops_control.drift import dataframe_drift_summary, feature_drift_report, page_hinkley, psi
from src.mlops_control.policy import DriftPolicyConfig, evaluation_gate, evaluate_policy
from src.mlops_control.registry import Registry
from src.mlops_control.store import EventStore


def test_psi_is_low_for_same_distribution():
    reference = [1, 2, 3, 4, 5] * 10
    current = [1, 2, 3, 4, 5] * 10
    assert psi(reference, current) < 0.01


def test_feature_drift_detects_shift():
    reference = pd.DataFrame({"close": [1.0] * 30, "volume": [10.0] * 30})
    current = pd.DataFrame({"close": [100.0] * 30, "volume": [10.0] * 30})
    report = feature_drift_report(reference, current)
    summary = dataframe_drift_summary(report)
    assert summary["dataset_severity"] in {"warning", "critical"}
    assert "close" in summary["critical_features"] or "close" in summary["warning_features"]


def test_page_hinkley_requires_enough_samples():
    assert page_hinkley([0.1, 0.2], min_instances=20)["reason"] == "insufficient_sample"


def test_policy_requires_persistence_before_retrain():
    summary = {"evaluated_features": 3, "critical_features": ["close", "volume"], "warning_features": []}
    first = evaluate_policy(summary, consecutive_critical_checks=1, config=DriftPolicyConfig(consecutive_checks=2))
    second = evaluate_policy(summary, consecutive_critical_checks=2, config=DriftPolicyConfig(consecutive_checks=2))
    assert first.action == "alert"
    assert second.action == "retrain"


def test_evaluation_gate_rejects_regression():
    result = evaluation_gate({"mae": 2.0, "rmse": 3.0, "directional_acc": 40}, {"mae": 1.0, "rmse": 1.0, "directional_acc": 60})
    assert result["passed"] is False


def test_registry_promote_and_rollback(tmp_path: Path):
    registry = Registry(tmp_path / "registry.json")
    first = registry.register("stock-ensemble-FPT-t3", {"mae": 1.0, "rmse": 1.2, "directional_acc": 55})
    registry.promote("stock-ensemble-FPT-t3", first["version"])
    second = registry.register("stock-ensemble-FPT-t3", {"mae": 0.9, "rmse": 1.0, "directional_acc": 57})
    registry.promote("stock-ensemble-FPT-t3", second["version"])
    assert registry.get_champion("stock-ensemble-FPT-t3")["version"] == second["version"]
    registry.rollback("stock-ensemble-FPT-t3", first["version"])
    assert registry.get_champion("stock-ensemble-FPT-t3")["version"] == first["version"]


def test_event_store_prediction_label_and_performance(tmp_path: Path):
    store = EventStore(tmp_path / "events.sqlite3")
    record = store.add_prediction({"ticker": "FPT", "current_price": 100, "prediction": 110, "model_version": "1"})
    store.update_ground_truth(record["id"], 108)
    summary = store.performance_summary("FPT")
    assert summary["sample_size"] == 1
    assert summary["mae"] == 2.0
    assert summary["directional_accuracy"] == 100.0
