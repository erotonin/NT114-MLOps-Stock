from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
SYMBOL = "FPT"
FEATURES = [
    "open", "high", "low", "close", "volume", "sma_10", "sma_20", "rsi",
    "macd", "macd_signal", "bb_upper", "bb_lower", "log_return",
]
import sys
sys.path.insert(0, str(ROOT))
from src.models_logic.tft_model import TFTSkeleton

out_dir = ROOT / "artifacts" / "explainability"
out_dir.mkdir(parents=True, exist_ok=True)
models_dir = ROOT / "models"
data = pd.read_csv(ROOT / "data" / f"{SYMBOL}.csv", index_col=0, parse_dates=True).dropna(subset=FEATURES)
scaler_x = joblib.load(models_dir / f"{SYMBOL}_scaler_x.pkl")
X = scaler_x.transform(data[FEATURES].to_numpy(dtype=float))

lgbm_model = joblib.load(models_dir / f"{SYMBOL}_lgbm_model.pkl")
raw_importance = np.asarray(getattr(lgbm_model, "feature_importances_", np.zeros(len(FEATURES))), dtype=float)
if raw_importance.sum() > 0:
    lgbm_importance = raw_importance / raw_importance.sum()
else:
    lgbm_importance = raw_importance

tft = TFTSkeleton(num_features=len(FEATURES))
tft.load_state_dict(torch.load(models_dir / f"{SYMBOL}_tft_model.pt", map_location="cpu"))
tft.eval()
window = 60
windows = np.stack([X[i - window:i] for i in range(window, len(X))])
with torch.no_grad():
    tensor = torch.tensor(windows, dtype=torch.float32)
    flat = tensor.reshape(-1, len(FEATURES), 1)
    logits = tft.vsn.selector_grn(flat.reshape(flat.shape[0], -1))
    weights = torch.softmax(logits, dim=-1).numpy()
tft_importance = weights.mean(axis=0)

payload = {
    "symbol": SYMBOL,
    "features": FEATURES,
    "method": {
        "lightgbm": "normalized gain/split feature_importances_ from trained local artifact",
        "tft": "mean variable-selection softmax weights across 60-step windows",
    },
    "lightgbm": {name: float(value) for name, value in zip(FEATURES, lgbm_importance)},
    "tft_variable_selection": {name: float(value) for name, value in zip(FEATURES, tft_importance)},
    "window_count": int(len(windows)),
}
json_path = out_dir / f"{SYMBOL}_feature_importance.json"
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

order = np.argsort(lgbm_importance + tft_importance)
labels = [FEATURES[i] for i in order]
y = np.arange(len(labels))
fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(y - 0.18, lgbm_importance[order], height=0.35, label="LightGBM", color="#2563eb")
ax.barh(y + 0.18, tft_importance[order], height=0.35, label="TFT variable selection", color="#d97706")
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Normalized importance / mean selection weight")
ax.set_title("FPT Feature Importance and TFT Variable Selection")
ax.grid(axis="x", alpha=0.25)
ax.legend()
fig.tight_layout()
image_path = out_dir / f"{SYMBOL}_feature_importance.png"
fig.savefig(image_path, dpi=180)
print(json_path)
print(image_path)
