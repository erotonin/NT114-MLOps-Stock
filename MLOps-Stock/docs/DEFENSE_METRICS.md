# Final defense metrics — FPT snapshot

Generated from `artifacts/evaluation/FPT_walk_forward_final.json` and `FPT_drift_replay_final.json`.

| Model | Mean MAE | Mean RMSE | Mean sMAPE (%) | Mean Directional Accuracy (%) | Mean Strategy Sharpe |
|---|---:|---:|---:|---:|---:|
| Naive | 2,352.01 | 3,012.89 | 2.68 | 42.86 | -1.42 |
| LightGBM | 3,503.25 | 4,256.40 | 4.10 | 50.24 | 1.54 |

Walk-forward folds: **7**; train/validation protocol: expanding window, validation size 60, gap 3.

Drift replay checks: **19**; checks whose policy action was `retrain`: **18**.

> Interpretation: this report benchmarks Naive and LightGBM only. TFT and Ensemble are evidenced separately by holdout manifest, Docker serving and automated retraining gate; these are not claimed as walk-forward TFT/Ensemble results.

## TFT/Ensemble walk-forward extension

A second evaluator now runs TFT and an equal-weight Ensemble on the same seven expanding folds, using the same train size, validation size, gap and 60-step window. TFT uses one CPU epoch per fold for a bounded reproducible benchmark; the equal-weight Ensemble averages fold-test predictions from TFT and LightGBM in the same inverse-transformed price space.

| Model | Mean MAE | Mean RMSE | Mean sMAPE (%) | Mean Directional Accuracy (%) | Mean Strategy Sharpe |
|---|---:|---:|---:|---:|---:|
| Naive | 2,352.01 | 3,012.89 | 2.68 | 42.86 | -1.42 |
| LightGBM | 4,205.20 | 4,990.57 | 4.89 | 47.38 | 0.36 |
| TFT | 8,441.87 | 9,401.15 | 9.24 | 50.00 | 0.31 |
| Equal-weight Ensemble | 5,897.04 | 6,723.20 | 6.71 | 48.33 | 0.33 |

The result is deliberately reported without spin: under this one-epoch fold protocol, the equal-weight Ensemble does **not** beat the Naive baseline on MAE/RMSE and does not beat the best individual model on all metrics. Its value in the thesis is therefore the reproducible MLOps lifecycle, component diversity and promotion gate—not an unsupported claim that averaging always improves forecast accuracy. The raw report is `artifacts/evaluation/FPT_walk_forward_ensemble_final.json` and the evaluator is `scripts/run_walk_forward_ensemble.py`.
