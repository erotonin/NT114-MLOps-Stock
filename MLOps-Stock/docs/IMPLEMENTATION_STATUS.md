# Implementation status

## Snapshot verified

- Data source: Yahoo Finance daily OHLCV.
- Snapshot verified for `VNM`, `VCB`, `HPG`, `FPT` on 2026-08-20 in the sandbox environment.
- FPT training completed successfully with 692 cleaned rows.
- FPT artifact manifest contains `model_version=local-fpt`, `data_version=local-snapshot`, `meta_input_space=scaled_target`, MAE, RMSE and Directional Accuracy after automated retraining.

## Tests

Command:

```bash
python3 -m pytest -q
```

Verified result: **28 passed**.

Compile check:

```bash
python3 -m compileall -q src services scripts
```

Verified result: **OK**.

## End-to-end evidence

The following local service path was verified:

```text
Data API -> TFT API + LightGBM API -> Ensemble API -> SQLite prediction log
```

Example FPT response contained current price `68300.0`, TFT/LightGBM component predictions, a scaled-space stacking prediction around `72k`, model version `local-fpt` and feature/data version `local-snapshot` after retraining.

The raw values are evidence that the service graph runs; they are not a claim of future accuracy or profitability.

## Evaluation evidence

- `artifacts/evaluation/FPT_walk_forward.json` was generated using real data with expanding-window walk-forward folds, a 3-day gap, Naïve baseline and LightGBM.
- `artifacts/evaluation/FPT_drift_replay.json` was generated using real historical windows and the drift policy. It records 19 checks and policy actions across historical periods.
- Automated retraining smoke test passed with a promoted candidate and registry version `4`; the job was stored in the same project event store used by the Control API.

## What is complete in code

The local control plane supports prediction logs, delayed ground-truth updates, PSI drift, JS/KL primitives, Page-Hinkley primitive, policy severity, retrain jobs, candidate/champion registry, promotion/rejection/rollback, audit events, RBAC demo and CORS configuration. The dashboard displays prediction, performance, drift events, model registry, retrain jobs and audit.

The GitOps repository contains Helm templates and values for Control API and Monitor API, an ingress route, and CI matrix entries to build/scan/sign/update image tags for Control API.

## Known limitations

The local registry is filesystem-backed and SQLite-backed for portability; production should use MLflow Model Registry/PostgreSQL/object storage. The current TFT is a research skeleton rather than a full industrial TFT implementation. Sentiment, online learning, production A/B testing and high-availability disaster recovery are not part of the verified MVP. Kubernetes rendering could not be executed in the sandbox because Helm and Docker are not installed; the manifests were edited consistently with the existing chart conventions and must be linted in the user's cluster/CI.
