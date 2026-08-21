# MLOps Stock — Delivery Index

## Chọn repository

Project được tiếp tục từ hai repository public. `MLOps-Stock` là repository mã nguồn ứng dụng, training, inference, dashboard, monitoring, tests và CI. `NT114_manifests` là repository GitOps chứa Helm chart, ArgoCD applications, infra manifests và deployment guide.

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
| 11 | `NT114_manifests/DEPLOYMENT.md` | K3s/Kubeflow/ArgoCD và Hybrid Cloud |

## Evidence đã kiểm tra

- **44 unit/API contract tests passed** trên Windows host.
- Python compileall và actionlint acceptance workflow passed.
- GitHub Actions hosted acceptance run `32449547945` passed.
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

Docker Desktop trên máy Windows đã được dùng để build/restart images và chạy Compose runtime evidence. Helm/Kubernetes cluster render và production deployment vẫn phải được xác nhận trong CI/cluster mục tiêu; không được trình bày local Compose là Hybrid Cloud production. Không commit credential, API key hoặc file `.env` thật.
