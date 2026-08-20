"""Leakage-aware time-series evaluation utilities."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Iterator

import numpy as np


@dataclass
class Fold:
    fold: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    def as_dict(self) -> dict:
        return asdict(self)


def walk_forward_splits(
    n_samples: int,
    train_size: int = 300,
    validation_size: int = 60,
    step_size: int = 60,
    gap: int = 3,
) -> Iterator[Fold]:
    """Yield expanding-window folds with a gap before validation."""
    if n_samples <= train_size + gap:
        return
    fold = 1
    train_end = train_size
    while train_end + gap < n_samples:
        test_start = train_end + gap
        test_end = min(test_start + validation_size, n_samples)
        if test_start >= test_end:
            break
        yield Fold(fold, 0, train_end, test_start, test_end)
        fold += 1
        train_end += step_size


def regression_metrics(y_true: Iterable[float], y_pred: Iterable[float], current_price: Iterable[float] | None = None, transaction_cost_bps: float = 10.0) -> dict:
    true = np.asarray(list(y_true), dtype=float)
    pred = np.asarray(list(y_pred), dtype=float)
    if true.shape != pred.shape or len(true) == 0:
        raise ValueError("y_true and y_pred must have the same non-zero shape")
    error = pred - true
    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(error**2)))
    denominator = np.maximum(np.abs(true), 1e-8)
    mape = float(np.mean(np.abs(error) / denominator) * 100.0)
    smape = float(np.mean(2.0 * np.abs(error) / (np.abs(true) + np.abs(pred) + 1e-8)) * 100.0)
    result = {"mae": mae, "rmse": rmse, "mape": mape, "smape": smape, "sample_size": int(len(true))}
    if current_price is not None:
        close = np.asarray(list(current_price), dtype=float)
        if close.shape == true.shape:
            true_direction = true >= close
            pred_direction = pred >= close
            result["directional_accuracy"] = float(np.mean(true_direction == pred_direction) * 100.0)
            positions = np.where(pred_direction, 1.0, -1.0)
            returns = (true - close) / np.maximum(np.abs(close), 1e-8)
            turnover = np.abs(np.diff(np.concatenate(([0.0], positions))))
            net_returns = positions * returns - turnover * transaction_cost_bps / 10000.0
            result["strategy_return"] = float(np.prod(1.0 + net_returns) - 1.0)
            result["strategy_sharpe"] = float(np.mean(net_returns) / (np.std(net_returns) + 1e-8) * np.sqrt(252.0))
    return result


def aggregate_fold_metrics(folds: list[dict]) -> dict:
    if not folds:
        return {"folds": [], "sample_size": 0}
    numeric_keys = [key for key, value in folds[0].items() if isinstance(value, (int, float)) and key not in {"fold"}]
    result = {"folds": folds, "sample_size": int(sum(item.get("sample_size", 0) for item in folds))}
    for key in numeric_keys:
        values = [float(item[key]) for item in folds if item.get(key) is not None]
        if values:
            result[f"mean_{key}"] = float(np.mean(values))
            result[f"std_{key}"] = float(np.std(values))
    return result
