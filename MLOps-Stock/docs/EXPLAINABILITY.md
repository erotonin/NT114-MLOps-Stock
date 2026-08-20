# Explainability Evidence

## Purpose

The project now includes a reproducible explainability artifact for the trained FPT snapshot. The result is intended to answer “which inputs influenced the model representation?”; it is not a causal claim that changing a feature will force a price movement.

## Methods

For LightGBM, the script reads the trained local artifact and normalizes its `feature_importances_` values. For the TFT skeleton, it computes the mean softmax variable-selection weights from the Variable Selection Network across all available 60-step windows. Both results are exported to `artifacts/explainability/FPT_feature_importance.json` and visualized in `artifacts/explainability/FPT_feature_importance.png`.

| Model | Explanation signal | Interpretation |
|---|---|---|
| LightGBM | Normalized `feature_importances_` | Relative split/gain importance from the trained tree model |
| TFT skeleton | Mean VSN softmax weight | Average variable-selection weight across temporal windows |

In the current FPT snapshot, `volume`, `log_return`, `rsi`, and MACD-related features receive relatively high TFT selection weights. The LightGBM and TFT signals should be compared as model-specific diagnostics, not treated as directly interchangeable scores.

## Limitations

The visualization is global rather than a per-prediction explanation. It does not provide SHAP values, attention rollout, counterfactuals or causal attribution. The TFT implementation is a simplified research skeleton, so its variable-selection weights are useful diagnostics but should not be presented as a complete explanation of the original Temporal Fusion Transformer paper. The artifact is snapshot-specific and can change after retraining.

## Reproduction

```powershell
python scripts\generate_explainability.py
```

The source code and raw JSON are committed together with the PNG so the figure can be regenerated for the defense.
