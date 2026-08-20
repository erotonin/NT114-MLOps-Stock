from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "artifacts/evaluation/FPT_walk_forward_ensemble_final.json").read_text(encoding="utf-8"))
models = report["models"]
names = ["Naive", "LightGBM", "TFT", "Equal-weight\nEnsemble"]
keys = ["naive", "lightgbm", "tft", "equal_weight_ensemble"]
metrics = [
    ("mean_mae", "Mean MAE", "#2563eb"),
    ("mean_rmse", "Mean RMSE", "#059669"),
    ("mean_directional_accuracy", "Directional Accuracy (%)", "#d97706"),
    ("mean_strategy_sharpe", "Mean Strategy Sharpe", "#7c3aed"),
]

fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=False)
fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.16, wspace=0.28, hspace=0.34)
fig.suptitle("FPT T+3 Walk-forward Metrics (7 Expanding Folds)", fontsize=15, fontweight="bold")
for ax, (metric, title, color) in zip(axes.ravel(), metrics):
    values = [models[key][metric] for key in keys]
    bars = ax.bar(names, values, color=color, alpha=0.88)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    if metric == "mean_strategy_sharpe":
        ax.axhline(0, color="black", linewidth=0.8)

fig.text(0.5, 0.025, "Source: artifacts/evaluation/FPT_walk_forward_ensemble_final.json. Bounded one-epoch TFT benchmark.", ha="center", fontsize=8)
out = ROOT / "artifacts/evaluation/defense_metrics_comparison.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=180)
print(out)
