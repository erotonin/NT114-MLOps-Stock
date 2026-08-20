from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.mlops_control.evaluation import aggregate_fold_metrics, regression_metrics, walk_forward_splits
from src.models_logic.lgbm_model import LGBMModel

FEATURES = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi", "macd", "macd_signal", "bb_upper", "bb_lower", "log_return",
]


def evaluate(symbol: str, train_size: int, validation_size: int, step_size: int) -> dict:
    path = Path("data") / f"{symbol.upper()}.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True).dropna(subset=FEATURES + ["target"])
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["target"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    reports = {"naive": [], "lightgbm": []}
    folds = []
    for fold in walk_forward_splits(len(df), train_size=train_size, validation_size=validation_size, step_size=step_size, gap=3):
        folds.append(fold.as_dict())
        train_slice = slice(fold.train_start, fold.train_end)
        test_slice = slice(fold.test_start, fold.test_end)
        scaler_x = StandardScaler().fit(X[train_slice])
        scaler_y = StandardScaler().fit(y[train_slice].reshape(-1, 1))
        model = LGBMModel()
        model.train(scaler_x.transform(X[train_slice]), scaler_y.transform(y[train_slice].reshape(-1, 1)).ravel(), scaler_x.transform(X[test_slice]), scaler_y.transform(y[test_slice].reshape(-1, 1)).ravel())
        pred_scaled = model.predict(scaler_x.transform(X[test_slice]))
        pred = scaler_y.inverse_transform(np.asarray(pred_scaled).reshape(-1, 1)).ravel()
        reports["lightgbm"].append({"fold": fold.fold, **regression_metrics(y[test_slice], pred, close[test_slice])})
        reports["naive"].append({"fold": fold.fold, **regression_metrics(y[test_slice], close[test_slice], close[test_slice])})
    return {
        "symbol": symbol.upper(),
        "target": "close_t_plus_3",
        "features": FEATURES,
        "folds": folds,
        "models": {name: aggregate_fold_metrics(values) for name, values in reports.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="FPT")
    parser.add_argument("--train-size", type=int, default=300)
    parser.add_argument("--validation-size", type=int, default=60)
    parser.add_argument("--step-size", type=int, default=60)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    report = evaluate(args.symbol, args.train_size, args.validation_size, args.step_size)
    output = Path(args.output or f"artifacts/evaluation/{args.symbol.upper()}_walk_forward.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
