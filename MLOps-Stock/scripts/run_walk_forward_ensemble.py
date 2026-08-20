from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.mlops_control.evaluation import aggregate_fold_metrics, regression_metrics, walk_forward_splits
from src.models_logic.lgbm_model import LGBMModel
from src.models_logic.tft_model import TFTSkeleton

FEATURES = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi",
    "macd", "macd_signal", "bb_upper", "bb_lower", "log_return",
]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def train_tft(X_train: np.ndarray, y_train: np.ndarray, window: int, epochs: int) -> TFTSkeleton:
    model = TFTSkeleton(num_features=X_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = torch.nn.MSELoss()
    if len(X_train) <= window:
        raise RuntimeError("Training window is too short for TFT sequence construction")
    seq = torch.tensor(np.stack([X_train[i - window:i] for i in range(window, len(X_train))]), dtype=torch.float32)
    target = torch.tensor(y_train[window:], dtype=torch.float32)
    model.train()
    for _ in range(max(1, epochs)):
        permutation = torch.randperm(len(seq))
        for start in range(0, len(seq), 32):
            idx = permutation[start:start + 32]
            optimizer.zero_grad()
            prediction = model(seq[idx]).flatten()
            loss = criterion(prediction, target[idx])
            loss.backward()
            optimizer.step()
    model.eval()
    return model


def predict_tft(model: TFTSkeleton, X_context: np.ndarray, positions: list[int], window: int) -> np.ndarray:
    sequences = np.stack([X_context[pos - window:pos] for pos in positions])
    with torch.no_grad():
        return model(torch.tensor(sequences, dtype=torch.float32)).flatten().numpy()


def evaluate(symbol: str, train_size: int, validation_size: int, step_size: int, window: int, tft_epochs: int, max_folds: int | None) -> dict:
    path = ROOT / "data" / f"{symbol.upper()}.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True).dropna(subset=FEATURES + ["target"])
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["target"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    reports = {"naive": [], "lightgbm": [], "tft": [], "equal_weight_ensemble": []}
    folds = []
    for fold_number, fold in enumerate(walk_forward_splits(len(df), train_size=train_size, validation_size=validation_size, step_size=step_size, gap=3), start=1):
        if max_folds is not None and fold_number > max_folds:
            break
        seed_everything(42 + fold_number)
        folds.append(fold.as_dict())
        train_slice = slice(fold.train_start, fold.train_end)
        test_positions = list(range(fold.test_start - fold.train_start, fold.test_end - fold.train_start))
        X_train = X[train_slice]
        y_train = y[train_slice]
        scaler_x = StandardScaler().fit(X_train)
        scaler_y = StandardScaler().fit(y_train.reshape(-1, 1))
        X_train_scaled = scaler_x.transform(X_train)
        y_train_scaled = scaler_y.transform(y_train.reshape(-1, 1)).ravel()
        X_context = X[fold.train_start:fold.test_end]
        X_context_scaled = scaler_x.transform(X_context)
        X_test_scaled = X_context_scaled[test_positions]

        lgbm = LGBMModel()
        val_start = max(window, int(len(X_train_scaled) * 0.8))
        lgbm.train(X_train_scaled, y_train_scaled, X_train_scaled[val_start:], y_train_scaled[val_start:])
        lgbm_scaled = np.asarray(lgbm.predict(X_test_scaled)).ravel()

        tft = train_tft(X_train_scaled, y_train_scaled, window=window, epochs=tft_epochs)
        tft_scaled = predict_tft(tft, X_context_scaled, test_positions, window=window)
        ensemble_scaled = 0.5 * tft_scaled + 0.5 * lgbm_scaled

        y_true = y[fold.test_start:fold.test_end]
        close_test = close[fold.test_start:fold.test_end]
        predictions = {
            "naive": close_test,
            "lightgbm": scaler_y.inverse_transform(lgbm_scaled.reshape(-1, 1)).ravel(),
            "tft": scaler_y.inverse_transform(tft_scaled.reshape(-1, 1)).ravel(),
            "equal_weight_ensemble": scaler_y.inverse_transform(ensemble_scaled.reshape(-1, 1)).ravel(),
        }
        for name, prediction in predictions.items():
            reports[name].append({"fold": fold.fold, **regression_metrics(y_true, prediction, close_test)})
        print(f"fold={fold.fold} samples={len(y_true)} lgbm_mae={reports['lightgbm'][-1]['mae']:.2f} tft_mae={reports['tft'][-1]['mae']:.2f} ensemble_mae={reports['equal_weight_ensemble'][-1]['mae']:.2f}", flush=True)

    return {
        "symbol": symbol.upper(),
        "target": "close_t_plus_3",
        "features": FEATURES,
        "protocol": {"train_size": train_size, "validation_size": validation_size, "step_size": step_size, "gap": 3, "window": window, "tft_epochs": tft_epochs, "ensemble": "equal_weight_average_of_fold_test_predictions"},
        "folds": folds,
        "models": {name: aggregate_fold_metrics(values) for name, values in reports.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="FPT")
    parser.add_argument("--train-size", type=int, default=300)
    parser.add_argument("--validation-size", type=int, default=60)
    parser.add_argument("--step-size", type=int, default=60)
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--tft-epochs", type=int, default=2)
    parser.add_argument("--max-folds", type=int, default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    report = evaluate(args.symbol, args.train_size, args.validation_size, args.step_size, args.window, args.tft_epochs, args.max_folds)
    output = ROOT / (args.output or f"artifacts/evaluation/{args.symbol.upper()}_walk_forward_ensemble.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved={output}")
