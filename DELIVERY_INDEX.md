# MLOps Stock — Delivery Index

## Chọn repository

Project được tiếp tục từ hai repository public. Repository canonical hiện tại là `erotonin/NT114-MLOps-Stock`; trong checkout này, mã nguồn ứng dụng nằm ở `MLOps-Stock/` và GitOps manifests nằm ở `NT114_manifests/`. ArgoCD hiện trỏ về repository canonical này tại path `NT114_manifests/argocd/apps/mlops-stock`.

## Thứ tự đọc và chạy

| Thứ tự | File/thư mục | Mục đích |
|---:|---|---|
| 1 | `MLOps-Stock/README.md` | Tổng quan và quick start |
| 2 | `MLOps-Stock/docs/SETUP.md` | Cài đặt, tải dữ liệu, train và chạy local/Compose/Kubernetes |
| 3 | `MLOps-Stock/docs/ARCHITECTURE.md` | Kiến trúc và MLOps lifecycle |
| 4 | `MLOps-Stock/docs/RUNBOOK.md` | Drift, retraining, registry, rollback và incident |
| 5 | `MLOps-Stock/docs/DEFENSE_NOTES.md` | Lý thuyết và câu hỏi bảo vệ |
| 6 | `MLOps-Stock/docs/IMPLEMENTATION_STATUS.md` | Evidence đã kiểm thử và giới hạn trung thực |
| 7 | `MLOps-Stock/artifacts/feature_store/catalog.json` | Catalog feature store versioned cho bốn ticker |
| 8 | `MLOps-Stock/artifacts/evaluation/FPT_lgbm_tuning.json` | Bounded LightGBM fine-tuning trên temporal holdout |
| 9 | `MLOps-Stock/scripts/defense_demo.ps1` | Thu thập evidence tự động trước bảo vệ |
| 10 | `.github/workflows/acceptance-tests.yml` | Hosted CI acceptance workflow ở repository root |
| 11 | `MLOps-Stock/docs/REMAINING_LIMITATIONS.md` | Phân biệt phần đã kiểm chứng và phần cần hạ tầng/credentials |
| 12 | `NT114_manifests/DEPLOYMENT.md` | K3s/Kubeflow/ArgoCD và Hybrid Cloud |
| 13 | `NT114_manifests/docs/GITOPS_VALIDATION.md` | Kết quả Helm lint/template và giới hạn kiểm chứng cluster |

## Evidence đã kiểm tra

- **49 unit/API contract tests passed** trên Windows host.
- Python compileall và actionlint acceptance workflow passed.
- GitHub Actions hosted acceptance runs `32449547945`, `32451716049`, `32452225372`, `32558949856` và `32559770677` passed.
- Real Yahoo Finance snapshots downloaded for four Vietnamese tickers.
- FPT Ensemble trained and served through Data → TFT/LightGBM → Ensemble.
- Walk-forward report and historical drift replay report generated.
- Drift evaluation endpoint passed on real historical windows.
- RBAC denial for viewer retraining passed.
- Automated retraining smoke test passed: job promoted a candidate into the local registry with model metrics and `meta_input_space=scaled_target`.
- Versioned local feature store materialized for FPT, VCB, VNM and HPG; catalog exposed by Control API and Dashboard.
- Bounded LightGBM tuning completed with three candidates and selected candidate report.
- Docker Compose health/readiness passed for all application services and Redis; Dashboard feature-store panel returned HTTP 200.

## Lưu ý

Docker Desktop trên máy Windows đã được dùng để build/restart images và chạy Compose runtime evidence. Helm lint/template và offline YAML structural validation đã passed cho chart dev; Kubernetes API-server validation, ArgoCD sync và production deployment vẫn cần cluster mục tiêu, nên không được trình bày local Compose hoặc Helm render là Hybrid Cloud production. Không commit credential, API key hoặc file `.env` thật.
