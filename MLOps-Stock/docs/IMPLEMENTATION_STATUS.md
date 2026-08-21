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

## Final hardening update — 2026-08-20

The final host regression command `python -m pytest -q` completed with **30 passed in 6.67 seconds**, including the CORS contract test. The test suite covers control-plane behavior, alerts, RBAC, dashboard contracts, data access, decision policy, Ensemble behavior, indicators, LightGBM, TFT and CORS allowlist behavior.

The four inference services now expose explicit readiness contracts: `GET /health` on Data API (`8001`), TFT API (`8002`), LightGBM API (`8003`) and Ensemble API (`8080`). After rebuilding and restarting the containers, all four endpoints returned HTTP 200 with service-specific JSON responses. Docker Compose healthchecks and `scripts/start_local.ps1` use these endpoints instead of relying on Swagger `/docs` availability.

The reproducibility verifier `scripts/verify_reproducibility.py` completed with `status=ok`. It validates the FPT manifest, the 13-feature contract, the real `data/FPT.csv` snapshot and every artifact referenced by the manifest, then records byte sizes and SHA-256 hashes in `artifacts/reproducibility_verification.json`. This evidence is intended to make the local defense demo auditable and to detect accidental artifact changes before rerunning inference.

Security and configuration hardening is also recorded. Control API CORS is restricted to the local dashboard origins rather than wildcard `*`, `.env.example` documents offline MLflow and alert sink variables without containing credentials, and the repository working tree was clean after the final commits. The latest pushed commit is `3aee775` (`ops: add inference health endpoints and readiness checks`).

The final acceptance sequence was:

```bash
python -m pytest -q
python scripts/smoke_test.py
python scripts/verify_reproducibility.py
```

The first command and the reproducibility verifier passed on the Windows host. The smoke test completed against the running Docker Compose stack, while the service-level health verification returned HTTP 200 for all four inference APIs. These checks demonstrate operational readiness of the local MVP; they do not imply that the Ensemble is more accurate than every baseline, as the documented walk-forward ablation correctly reports Naive as strongest on MAE/RMSE and TFT as strongest on directional accuracy.

## Additional hardening — 2026-08-21

Inference request validation was added without changing successful response schemas. A shared validator now normalizes Vietnamese stock tickers, rejects malformed symbols, requires all 13 feature columns, enforces equal-length arrays, rejects non-numeric/non-finite values and limits Data API `days` to `1..2000`. Invalid requests return HTTP 422; upstream/model failures retain their existing error handling. The new contract tests cover valid matrices, missing features, misaligned lengths, NaN values and invalid tickers.

The final host regression after this change collected **38 tests and passed all 38**. Runtime verification after rebuilding Data, TFT, LightGBM and Ensemble containers returned HTTP 200 from all four `/health` endpoints. The live contract checks rejected `GET /predict/FPT-` at Ensemble and `GET /fetch/FPT?days=5000` at Data API with HTTP 422. The Compose smoke test continued to pass real FPT prediction, Control readiness, drift policy and viewer RBAC denial.

A demo safety workflow was added as `scripts/backup_demo_artifacts.py`. It creates a timestamped backup of `models/`, `data/` and `artifacts/control_plane.sqlite3`, writes a `backup_manifest.json` containing file count, byte sizes and SHA-256 values, and supports an external `--output` path. The workflow was executed against a temporary destination and successfully backed up 11 files; temporary validation output was removed and `artifacts/backups/` is ignored by Git.

## Full-stack readiness hardening — 2026-08-21

Readiness coverage was extended beyond inference services. Redis now uses `redis-cli ping`; Control API, Monitor API and Dashboard UI use HTTP healthchecks; Dashboard UI also exposes `GET /health`. After rebuilding Dashboard and restarting the Compose stack, all seven application health URLs returned HTTP 200 and Redis returned `PONG`. This gives the defense demo a consistent readiness signal for the complete local architecture rather than checking only Swagger pages.

## Defense demo expansion — 2026-08-21

The defense script now records all application readiness endpoints, Prometheus metrics, registry/audit/retraining views, invalid-input contracts and viewer retraining denial in one evidence file. The latest run recorded HTTP 200 for all seven application health endpoints, `PONG` for Redis in the direct runtime check, HTTP 422 for invalid Ensemble ticker and invalid Data API days, HTTP 403 for viewer retraining denial, and a successful real FPT prediction through the Ensemble graph.

After adding the Dashboard health contract test, the final host regression collected **39 tests and passed all 39 in 4.74 seconds**. The repository remains synchronized with GitHub after the subsequent evidence commit.

## Feature store and dashboard management — 2026-08-21

A local versioned feature store MVP is now materialized for `FPT`, `VCB`, `VNM` and `HPG` under `artifacts/feature_store/`. Each symbol has a `v1/features.csv` snapshot and `metadata.json` containing schema, date range, row count, null count, byte size and SHA-256. The catalog is exposed through Control API `GET /features` and `GET /features/{ticker}` with viewer RBAC, and the Dashboard now renders the feature-store version, symbols, row counts and feature counts alongside registry/drift/retraining panels.

The feature-store API was tested both with unit tests and against the live Control API container. The Dashboard root returned HTTP 200 and contained the Feature store panel. The final host suite now collects **44 tests and passes all 44**; reproducibility verification and Compose smoke test also passed after integration. This demonstrates the requested feature-management path as a verified local MVP, while the production cloud version would replace filesystem snapshots with an object-backed/managed feature store.

## Hosted CI acceptance — 2026-08-21

The project now has a root-level GitHub Actions acceptance workflow at `../.github/workflows/acceptance-tests.yml`, aligned with the repository layout where `MLOps-Stock/` is the project directory. It installs the dedicated `requirements-ci.txt` profile, runs Python 3.12 compile checks and executes the full unit/API contract suite on `ubuntu-latest`.

The workflow was executed successfully in GitHub Actions run [32449547945](https://github.com/erotonin/NT114-MLOps-Stock/actions/runs/32449547945) for commit `34e546c`. The first CI attempt revealed and corrected a missing `yfinance` CI dependency; the rerun passed all steps. The hosted CI run is evidence for automated compile/test gating, while the self-hosted K3s image publishing and GitOps workflows remain deployment design/runtime-specific and are not claimed as executed here.

## Bounded fine-tuning evidence — 2026-08-21

The optional tuning script `scripts/tune_lgbm.py` now evaluates three LightGBM configurations using a chronological 80/20 temporal holdout, training-only scalers and deterministic seed `42`. On the FPT snapshot it evaluated 554 training rows and 139 holdout rows; candidate 2 was selected by lowest holdout MAE followed by RMSE, with price-space MAE `4894.85` and RMSE `5929.77`. The complete report is stored in `artifacts/evaluation/FPT_lgbm_tuning.json`.

This is presented as a bounded hyperparameter-tuning/fine-tuning experiment, not as an Optuna/Ray Tune production search and not as proof that the tuned model dominates the Naive baseline. The default serving artifacts were intentionally not replaced by this experiment; the result is reproducible evidence for the methodology and a safe extension point for future training runs.

Following feature-store and CI additions, the local regression suite collects **44 tests and passes all 44**. GitHub Actions run `32449547945` separately passed the hosted compile and full contract-test workflow.

## Alert connector contract evidence — 2026-08-21

Alert delivery now has explicit contract coverage for the offline JSONL sink, successful webhook status reporting and non-blocking webhook failure handling. A notification outage is recorded in the alert payload and does not interrupt monitoring/retraining decisions. Real Slack, Telegram or email delivery is intentionally not invoked without a user-owned endpoint and credentials.

The local regression suite now collects **47 tests** after the webhook and Control API query-boundary contract tests were added; the targeted alert suite passes all 3 tests and the targeted Control API suite passes 12 tests. GitHub Actions runs [32451716049](https://github.com/erotonin/NT114-MLOps-Stock/actions/runs/32451716049) and latest [32452225372](https://github.com/erotonin/NT114-MLOps-Stock/actions/runs/32452225372) completed successfully.

## Control query boundary hardening — 2026-08-21

Viewer collection endpoints now validate `limit` with FastAPI query constraints `1 <= limit <= 1000` for predictions, performance, drift events, retraining jobs and audit history. Invalid values are rejected with HTTP 422 before store/registry access. The targeted Control API validation suite passed all 12 tests after this change.
