from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FEATURES = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi",
    "macd", "macd_signal", "bb_upper", "bb_lower", "log_return",
]

CANDIDATES = [
    {"learning_rate": 0.05, "num_leaves": 15, "feature_fraction": 0.8, "bagging_fraction": 0.8},
    {"learning_rate": 0.03, "num_leaves": 31, "feature_fraction": 0.9, "bagging_fraction": 0.8},
    {"learning_rate": 0.08, "num_leaves": 63, "feature_fraction": 0.8, "bagging_fraction": 0.9},
]


def evaluate(symbol: str, data_path: Path, candidates: list[dict[str, float]]) -> dict[str, object]:
    frame = pd.read_csv(data_path, index_col=0, parse_dates=True).dropna(subset=FEATURES + ["target"])
    split = int(len(frame) * 0.8)
    x_train_raw, x_test_raw = frame[FEATURES].iloc[:split], frame[FEATURES].iloc[split:]
    y_train_raw, y_test_raw = frame["target"].iloc[:split], frame["target"].iloc[split:]
    scaler_x = StandardScaler().fit(x_train_raw)
    x_train = scaler_x.transform(x_train_raw)
    x_test = scaler_x.transform(x_test_raw)
    scaler_y = StandardScaler().fit(y_train_raw.to_numpy().reshape(-1, 1))
    y_train = scaler_y.transform(y_train_raw.to_numpy().reshape(-1, 1)).ravel()
    y_test = scaler_y.transform(y_test_raw.to_numpy().reshape(-1, 1)).ravel()

    results = []
    for index, candidate in enumerate(candidates, start=1):
        params = {
            "objective": "regression",
            "metric": "rmse",
            "verbosity": -1,
            "boosting_type": "gbdt",
            "seed": 42,
            **candidate,
        }
        train_set = lgb.Dataset(x_train, label=y_train)
        valid_set = lgb.Dataset(x_test, label=y_test, reference=train_set)
        model = lgb.train(
            params,
            train_set,
            num_boost_round=400,
            valid_sets=[valid_set],
            valid_names=["holdout"],
            callbacks=[lgb.early_stopping(30, verbose=False)],
        )
        pred_scaled = model.predict(x_test, num_iteration=model.best_iteration)
        pred = scaler_y.inverse_transform(np.asarray(pred_scaled).reshape(-1, 1)).ravel()
        truth = y_test_raw.to_numpy()
        results.append(
            {
                "candidate": index,
                "params": candidate,
                "best_iteration": int(model.best_iteration or 0),
                "mae_price": float(np.mean(np.abs(pred - truth))),
                "rmse_price": float(np.sqrt(np.mean((pred - truth) ** 2))),
            }
        )

    best = min(results, key=lambda row: (row["mae_price"], row["rmse_price"]))
    return {
        "symbol": symbol,
        "method": "bounded_temporal_holdout_grid",
        "seed": 42,
        "feature_count": len(FEATURES),
        "train_rows": len(x_train),
        "holdout_rows": len(x_test),
        "target_space": "price",
        "candidates": results,
        "selected_candidate": best["candidate"],
        "selection_rule": "lowest holdout MAE, then RMSE",
        "status": "ok",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded LightGBM temporal holdout tuning experiment.")
    parser.add_argument("--symbol", default="FPT")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "evaluation" / "FPT_lgbm_tuning.json")
    args = parser.parse_args()
    symbol = args.symbol.strip().upper()
    report = evaluate(symbol, ROOT / "data" / f"{symbol}.csv", CANDIDATES)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
