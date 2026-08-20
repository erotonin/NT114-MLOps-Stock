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

## Docker Compose acceptance evidence — 2026-08-20

All project images were built successfully on Windows Docker Desktop 29.6.1: `data-api` (529 MB), `lgbm-api` (726 MB), `ensemble-api` (590 MB), `monitor-api` (776 MB), `tft-api` (1.86 GB), `control-api` (656 MB) and `dashboard-ui` (243 MB). The dashboard Dockerfile was corrected to copy only `services/dashboard_ui/requirements.txt`; otherwise the root training requirements could accidentally pull `torch`, MLflow and `s3fs`.

The full local-offline Compose stack started successfully with eight project containers plus Redis. MLflow remains available under the optional `mlflow` profile because the GHCR image pull was slow on the laptop; local inference uses the verified FPT artifacts mounted from `models/`. Control and Monitor were reachable at their health endpoints, and Dashboard returned HTTP 200.

The recorded prediction path is in `artifacts/smoke_evidence.txt`: Data API returned HTTP 200 with 122 close observations; TFT returned `91865.71875`; LightGBM returned `70749.73788562209`; Ensemble returned HTTP 200 with current price `68800.0`, ensemble prediction `72646.32186951733`, model version `local-fpt`, feature version `local-snapshot`, and decision `SELL`. Dashboard returned HTTP 200. These values demonstrate a functioning service graph, not predictive performance or investment advice.

The Control API evidence is in `artifacts/control_smoke_evidence.txt` and the live policy check. Health returned `status=ok`; viewer access to `/models` returned HTTP 200; a two-feature PSI shift with two consecutive critical checks returned policy decision `severity=critical`, `action=retrain`, and policy version `v1`.

The host-level `python -m pytest -q` command on the Windows Python installation was not accepted because the host FastAPI TestClient environment lacked `httpx`; this is an environment dependency issue rather than a Docker runtime failure. The sandbox verification remains **28 passed**, and the Docker acceptance evidence above was collected independently on the target laptop.

## Final hardening verification

The Windows host test environment was repaired by installing the declared test dependencies `httpx`, `requests`, `redis`, `pytest` and CPU-only PyTorch. The official command `python -m pytest -q` then completed with **28 passed in 14.26 seconds**.

The repository smoke test `python scripts/smoke_test.py` was executed against the running Compose stack and passed all checks: Ensemble and Control readiness, real FPT prediction, drift policy evaluation returning `critical/retrain`, and RBAC denial for a viewer attempting retraining. The Control API image was rebuilt with the training packages required by the lazy retraining worker (`torch`, `lightgbm`, `mlflow`, `yfinance`) while keeping `s3fs` and `boto3` outside the default image to avoid the resolver loop.

The Windows startup script now validates Compose configuration, starts the local-offline profile, waits up to three minutes for all readiness URLs, reports pending services, and prints the exact Dashboard, API, Control and optional MLflow commands.

## Automated retraining regression evidence — 2026-08-20

A manual retraining request was executed through `POST /retrain` with role `analyst`, ticker `FPT`, horizon `3` and `epochs=1`. The first offline attempts exposed two real deployment defects: the Control API still referenced the optional `mlflow` hostname, and an existing MLflow experiment retained an unwritable `/home/ubuntu` artifact location. Both issues were fixed by enabling local SQLite tracking, mounting `mlflow.db`, creating a writable `/app/artifacts/mlflow` artifact root and isolating the offline experiment name.

The final job `e3594d60-d655-46e8-bc03-f04e82f0606b` reached **promoted**. Candidate model `stock-ensemble-FPT-t3` received registry version `1`, with MAE `0.2872670182790942`, RMSE `0.3548542435466494`, and Directional Accuracy `46.875`; the evaluation gate passed because no champion existed. Raw polling output is stored in `artifacts/retraining_final_evidence.txt`.

This is stronger evidence than a mocked endpoint response: the worker downloaded data, trained TFT/LightGBM/meta-learner artifacts, logged the offline MLflow run, registered the candidate and executed the promotion gate. The run used one epoch for a bounded regression check, not as the final research training configuration.

## Champion gate and artifact safety regression — 2026-08-20

A second bounded retraining run was executed after a champion already existed. Candidate version `2` for `stock-ensemble-FPT-t3` was compared against champion version `1`: MAE improved from `0.2872670182790942` to `0.2867988409553559`, RMSE improved from `0.3548542435466494` to `0.35435845756971923`, and Directional Accuracy remained `46.875`. The evaluation gate returned `passed=true` and the candidate was promoted.

The retraining worker now snapshots existing artifacts before training, seeds the registry from an existing local manifest when no champion exists, and restores the snapshot when a candidate is rejected. This prevents a rejected model from silently replacing the artifact used by local inference. Raw evidence is stored in `artifacts/retraining_guard_evidence.json`.
