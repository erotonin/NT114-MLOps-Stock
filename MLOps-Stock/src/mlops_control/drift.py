"""Deterministic drift metrics and policy primitives.

The module is intentionally dependency-light so it can run in the local control
plane, a scheduled job, or a Kubernetes worker. It does not decide whether a
model is safe for production by itself; it produces auditable measurements that
are consumed by the policy layer.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import numpy as np
import pandas as pd


EPS = 1e-8


@dataclass
class DriftMetric:
    feature: str
    metric: str
    value: float
    threshold_warning: float
    threshold_critical: float
    severity: str
    reference_size: int
    current_size: int

    def as_dict(self) -> dict:
        return asdict(self)


def _clean(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    return arr


def _histogram(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> tuple[np.ndarray, np.ndarray]:
    if reference.size == 0 or current.size == 0:
        return np.array([]), np.array([])
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if edges.size < 3:
        low = float(np.min(reference))
        high = float(np.max(reference))
        if np.isclose(low, high):
            high = low + 1.0
        edges = np.linspace(low, high, min(bins + 1, 11))
    if current.min() < edges[0] or current.max() > edges[-1]:
        edges = np.concatenate(([min(reference.min(), current.min())], edges[1:-1], [max(reference.max(), current.max())]))
        edges = np.unique(edges)
    if edges.size < 3:
        edges = np.array([reference.min() - 1.0, reference.max() + 1.0])
    ref_hist, _ = np.histogram(reference, bins=edges)
    cur_hist, _ = np.histogram(current, bins=edges)
    ref_prob = (ref_hist.astype(float) + EPS) / (ref_hist.sum() + EPS * len(ref_hist))
    cur_prob = (cur_hist.astype(float) + EPS) / (cur_hist.sum() + EPS * len(cur_hist))
    return ref_prob, cur_prob


def psi(reference: Iterable[float], current: Iterable[float], bins: int = 10) -> float:
    ref = _clean(reference)
    cur = _clean(current)
    p, q = _histogram(ref, cur, bins=bins)
    if p.size == 0 or q.size == 0:
        return float("nan")
    return float(np.sum((q - p) * np.log(q / p)))


def kl_divergence(reference: Iterable[float], current: Iterable[float], bins: int = 10) -> float:
    ref = _clean(reference)
    cur = _clean(current)
    p, q = _histogram(ref, cur, bins=bins)
    if p.size == 0 or q.size == 0:
        return float("nan")
    return float(np.sum(p * np.log(p / q)))


def js_divergence(reference: Iterable[float], current: Iterable[float], bins: int = 10) -> float:
    ref = _clean(reference)
    cur = _clean(current)
    p, q = _histogram(ref, cur, bins=bins)
    if p.size == 0 or q.size == 0:
        return float("nan")
    m = 0.5 * (p + q)
    return float(0.5 * np.sum(p * np.log(p / m)) + 0.5 * np.sum(q * np.log(q / m)))


def _severity(value: float, warning: float, critical: float) -> str:
    if not np.isfinite(value):
        return "insufficient_sample"
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "stable"


def feature_drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    columns: Iterable[str] | None = None,
    min_samples: int = 20,
    warning_psi: float = 0.10,
    critical_psi: float = 0.25,
) -> list[DriftMetric]:
    """Return auditable PSI metrics for each selected numeric feature."""
    columns = list(columns or reference.columns)
    report: list[DriftMetric] = []
    for column in columns:
        if column not in reference or column not in current:
            report.append(DriftMetric(column, "psi", float("nan"), warning_psi, critical_psi, "missing", 0, 0))
            continue
        ref = _clean(reference[column].to_numpy())
        cur = _clean(current[column].to_numpy())
        value = psi(ref, cur) if len(ref) >= min_samples and len(cur) >= min_samples else float("nan")
        report.append(
            DriftMetric(
                feature=column,
                metric="psi",
                value=value,
                threshold_warning=warning_psi,
                threshold_critical=critical_psi,
                severity=_severity(value, warning_psi, critical_psi),
                reference_size=int(len(ref)),
                current_size=int(len(cur)),
            )
        )
    return report


def page_hinkley(values: Iterable[float], delta: float = 0.005, threshold: float = 50.0, min_instances: int = 20) -> dict:
    """Small, deterministic Page-Hinkley implementation for an error stream."""
    data = _clean(values)
    if len(data) < min_instances:
        return {"detected": False, "index": None, "n": int(len(data)), "reason": "insufficient_sample"}
    mean = 0.0
    cumulative = 0.0
    minimum = 0.0
    detected_at = None
    for idx, value in enumerate(data, start=1):
        mean += (value - mean) / idx
        cumulative += value - mean - delta
        minimum = min(minimum, cumulative)
        if cumulative - minimum > threshold:
            detected_at = idx - 1
            break
    return {"detected": detected_at is not None, "index": detected_at, "n": int(len(data)), "reason": "ok"}


def performance_drift(
    errors: Iterable[float],
    baseline_mae: float,
    current_mae: float,
    warning_ratio: float = 1.10,
    critical_ratio: float = 1.20,
    min_samples: int = 20,
) -> dict:
    data = _clean(errors)
    if len(data) < min_samples or baseline_mae <= EPS:
        return {
            "metric": "rolling_mae",
            "baseline_mae": float(baseline_mae),
            "current_mae": float(current_mae),
            "ratio": float("nan"),
            "severity": "insufficient_sample",
            "page_hinkley": page_hinkley(data, min_instances=min_samples),
        }
    ratio = float(current_mae / baseline_mae)
    severity = "critical" if ratio >= critical_ratio else "warning" if ratio >= warning_ratio else "stable"
    return {
        "metric": "rolling_mae",
        "baseline_mae": float(baseline_mae),
        "current_mae": float(current_mae),
        "ratio": ratio,
        "severity": severity,
        "page_hinkley": page_hinkley(data, min_instances=min_samples),
    }


def dataframe_drift_summary(report: list[DriftMetric]) -> dict:
    usable = [item for item in report if np.isfinite(item.value)]
    critical = [item.feature for item in usable if item.severity == "critical"]
    warning = [item.feature for item in usable if item.severity == "warning"]
    return {
        "metric": "psi",
        "total_features": len(report),
        "evaluated_features": len(usable),
        "critical_features": critical,
        "warning_features": warning,
        "share_drifted": float(len(critical + warning) / len(usable)) if usable else None,
        "dataset_severity": "critical" if critical else "warning" if warning else "stable" if usable else "insufficient_sample",
        "features": [item.as_dict() for item in report],
    }
