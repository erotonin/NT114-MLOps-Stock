# Remaining Limitations and Defense Position

## Purpose

This document separates features that are implemented and tested from features that remain design-level or require infrastructure, credentials, or a longer research period. It prevents accidental overclaiming during the thesis defense.

## Requirement status

| Requirement from the proposal | Current status | Evidence available | Why it is not presented as more complete |
|---|---|---|---|
| OHLCV and technical-indicator features | Implemented | 13-feature contract, local snapshots, feature-store metadata | Sentiment and macroeconomic features are outside the current dataset scope |
| Versioned feature store | Implemented as local MVP | Version `v1` snapshots for FPT/VCB/VNM/HPG, catalog, metadata hashes, Control API and Dashboard panel | A production deployment would use object storage or Feast backed by a managed online/offline store |
| LightGBM and TFT serving | Implemented and runtime-tested | Four inference APIs, Docker healthchecks, prediction smoke test | TFT remains a bounded skeleton/training configuration rather than a large-scale tuned research model |
| Stacking Ensemble | Implemented and served | LightGBM + TFT + meta-learner artifacts, Ensemble API | Walk-forward results do not show universal dominance over the Naive baseline |
| Hyperparameter tuning | Bounded LightGBM experiment implemented | Three chronological-holdout candidates, seed 42, `FPT_lgbm_tuning.json` | Optuna/Ray Tune distributed search was not necessary for the laptop acceptance scope |
| Data drift | Implemented | PSI/KL-style feature drift report, replay, thresholds and alerts | Thresholds are calibrated on local historical snapshots, not on a long production stream |
| Concept/performance drift | Primitive implemented | Delayed-label performance summary and Page-Hinkley policy | Real concept-drift confirmation requires future ground-truth labels collected over time |
| Automated retraining | Implemented and executed locally | Retraining job, candidate/champion gate, artifact backup/restore, promoted candidate | This is a local/offline execution path; production scheduler/queue scale is not claimed |
| Alerting | Implemented as local JSONL plus optional webhook | Alert sink code and alert evidence | Email/Slack/Telegram delivery requires user-owned credentials and an external endpoint |
| Model registry and rollback | Implemented locally | Filesystem registry, SQLite audit, promote/rollback endpoints | MLflow remote registry/object storage is optional rather than required by local mode |
| RBAC | Implemented for viewer/analyst/admin | HTTP contract tests, viewer denial evidence | Role header is a local demonstration; production needs OAuth/JWT/SSO and secret management |
| Dashboard | Implemented and tested | Prediction, performance, drift, registry, retraining, feature-store panels | It is an operational control center, not a broker or automated trading system |
| CI acceptance | Implemented and executed | Hosted GitHub Actions run `32449547945` passed compile and 44-test suite | Self-hosted image publishing and GitOps workflows require the organization K3s runner and secrets |
| Hybrid Cloud architecture | Designed and documented | Helm/ArgoCD/Terraform manifests, deployment guide and readiness report | No claim is made that a production EKS/K3s cluster was provisioned in this laptop acceptance run |
| Multi-horizon forecasting | Partially parameterized | Horizon fields and T+3 serving contract | A complete T+1/T+5/T+10 benchmark matrix would require separate artifacts and evaluation runs |
| Quantile uncertainty | Not implemented as TFT quantile heads | Current API exposes a bounded uncertainty/disagreement field | Adding P10/P50/P90 changes training, artifacts and response contracts; it should be a separate controlled experiment |
| Production A/B testing | Not implemented | Registry/versioning primitives are available | A/B testing needs traffic routing, experiment assignment, exposure logs and a live labeled stream |
| Cost monitoring | Not implemented | Deployment manifests provide an extension point | Real cost data requires cloud billing access and a deployed public-cloud workload |
| Online/continual learning | Not implemented | Scheduled/manual retraining path exists | Online updates would require stronger data-quality, rollback and safety controls than the thesis local scope |

## Recommended defense statement

> “Đồ án đã hoàn thiện và kiểm chứng end-to-end ở phạm vi local-offline và CI acceptance: data, feature store, model serving, ensemble, drift policy, retraining gate, registry, RBAC, dashboard, backup và regression evidence đều chạy được. Với Hybrid Cloud, nhóm cung cấp kiến trúc, Helm/ArgoCD/Terraform manifests và deployment guide; không tuyên bố đã có production cluster nếu chưa có credential và hạ tầng mục tiêu. Các mục như quantile TFT, A/B testing production, cost monitoring và alert qua Telegram/Slack cần một giai đoạn triển khai hạ tầng tiếp theo.”

## Safe next steps if infrastructure becomes available

A cloud-enabled extension should first provision a non-production namespace, object storage and a managed secret. Then it should enable remote MLflow/artifact storage, deploy the same images through GitOps, route alerts to a test webhook, collect delayed labels, and run a shadow-only A/B experiment. Quantile TFT should be trained as a new model version with a versioned response schema and an evaluation gate; it should not replace the current champion in place.
