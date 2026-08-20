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
| 7 | `NT114_manifests/DEPLOYMENT.md` | K3s/Kubeflow/ArgoCD và Hybrid Cloud |

## Evidence đã kiểm tra

- 28 unit tests passed.
- Python compileall passed.
- Real Yahoo Finance snapshots downloaded for four Vietnamese tickers.
- FPT Ensemble trained and served through Data → TFT/LightGBM → Ensemble.
- Walk-forward report and historical drift replay report generated.
- Drift evaluation endpoint passed on real historical windows.
- RBAC denial for viewer retraining passed.
- Automated retraining smoke test passed: job promoted a candidate into the local registry with model metrics and `meta_input_space=scaled_target`.

## Lưu ý

Docker, Kubernetes và Helm không có sẵn trong sandbox nên image build và Helm render phải được chạy lại trên máy cá nhân/CI/cluster. Code, compose, Dockerfiles, Helm templates và setup guide đã được chuẩn bị cho các môi trường đó. Không commit credential, API key hoặc file `.env` thật.
