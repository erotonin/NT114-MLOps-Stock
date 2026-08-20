# Baseline assessment

## Repositories

The user supplied `NT114_manifests` twice. The GitHub account also contains the application repository `MLOps-Stock`, which was cloned alongside the manifests repository.

- `MLOps-Stock`: application code, training, services, tests, CI workflows and Terraform.
- `NT114_manifests`: GitOps repository with ArgoCD apps, infra manifests and deployment documentation.

## Existing strengths

The project already contains data ingestion from Yahoo Finance, technical indicators, T+3 target creation, a simplified TFT model, LightGBM, a stacking meta-learner, MLflow artifact logging, FastAPI services, Redis integration, dashboard UI, GitHub Actions, Dockerfiles, K3s/EKS/Tailscale/Terraform/ArgoCD manifests and 21 passing tests after dependencies were installed.

## Baseline test result

Command: `python3 -m pytest -q`

Result: **21 passed**.

The original unit tests cover dashboard, data API, decision policy, ensemble API, indicators, LightGBM API and TFT API contracts. They do not yet cover real training/evaluation, drift policy, delayed labels, retraining gate, model registry promotion/rollback, RBAC, audit, feature versioning or end-to-end service orchestration.

## Main gaps found

1. `docker-compose.yml` does not include Redis, MLflow, PostgreSQL, monitoring, training or a retraining service, so the advertised local stack is incomplete.
2. The application requirements do not fully declare all runtime dependencies used by monitor code, including Evidently and Prometheus client.
3. `monitor_api` currently computes only a periodic data drift report from fresh Yahoo data. It does not persist events, calculate concept/performance drift, use delayed labels, or trigger retraining.
4. `model_loader` selects the newest MLflow run by symbol rather than a registry alias or approved champion version.
5. Training uses one 80/20 split and a validation-derived meta learner; it does not yet provide strict multi-fold walk-forward evaluation or a leakage-safe OOF stacking protocol.
6. Serving contracts are tightly coupled to 13 hardcoded features, one 60-step window and T+3 only.
7. Dashboard is prediction-focused and lacks model registry, drift timeline, retrain control, user roles and audit.
8. Deployment documentation contains example plaintext credentials and must be rewritten to use placeholders/secrets safely.
9. The user did not provide personal-computer access; work is therefore being developed and verified in the sandbox, with a portable setup for local Docker/Kubernetes later.

## Initial implementation direction

Preserve existing API contracts and tests while adding a local, runnable control plane based on SQLite/JSON event storage for monitoring and retraining. Add versioned manifest/registry metadata, a deterministic drift policy, historical replay, evaluation reports and a management API/dashboard. Keep full Kubernetes manifests as deployment artifacts, but make local execution possible without requiring a cluster.
