# Final defense metrics — FPT snapshot

Generated from `artifacts/evaluation/FPT_walk_forward_final.json` and `FPT_drift_replay_final.json`.

| Model | Mean MAE | Mean RMSE | Mean sMAPE (%) | Mean Directional Accuracy (%) | Mean Strategy Sharpe |
|---|---:|---:|---:|---:|---:|
| Naive | 2,352.01 | 3,012.89 | 2.68 | 42.86 | -1.42 |
| LightGBM | 3,503.25 | 4,256.40 | 4.10 | 50.24 | 1.54 |

Walk-forward folds: **7**; train/validation protocol: expanding window, validation size 60, gap 3.

Drift replay checks: **19**; checks whose policy action was `retrain`: **18**.

> Interpretation: this report benchmarks Naive and LightGBM only. TFT and Ensemble are evidenced separately by holdout manifest, Docker serving and automated retraining gate; these are not claimed as walk-forward TFT/Ensemble results.
