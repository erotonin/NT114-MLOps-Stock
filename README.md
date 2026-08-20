# NT114-MLOps-Stock

Hệ thống dự đoán giá chứng khoán dựa trên MLOps với Ensemble LightGBM–Temporal Fusion Transformer, drift detection, Web dashboard và Hybrid Cloud deployment.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `MLOps-Stock/` | Mã nguồn data pipeline, training, TFT/LightGBM/Ensemble API, Control API, Monitor API, Dashboard, tests và Docker Compose |
| `NT114_manifests/` | Helm, ArgoCD, Kubernetes/GitOps và hướng dẫn Hybrid Cloud |
| `academic/` | Proposal 3 tháng và ma trận đối chiếu góp ý của giảng viên |

## Bắt đầu nhanh

```powershell
cd MLOps-Stock
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.data_pipeline.download_latest
python -m src.training.final_ensemble_train --symbol FPT
.\scripts\start_local.sh
```

Trên Windows, nếu shell không chạy file `.sh`, có thể dùng Git Bash/WSL hoặc chạy từng service theo `MLOps-Stock/docs/SETUP.md`.

Dashboard: `http://127.0.0.1:8081`.

## Tài liệu chính

- [`MLOps-Stock/docs/SETUP.md`](MLOps-Stock/docs/SETUP.md): setup, training, local stack, Compose và Kubernetes.
- [`MLOps-Stock/docs/RUNBOOK.md`](MLOps-Stock/docs/RUNBOOK.md): drift, retrain, registry, rollback và backup.
- [`MLOps-Stock/docs/DEFENSE_NOTES.md`](MLOps-Stock/docs/DEFENSE_NOTES.md): lý thuyết và câu hỏi bảo vệ.
- [`MLOps-Stock/docs/ARCHITECTURE.md`](MLOps-Stock/docs/ARCHITECTURE.md): kiến trúc và lifecycle.
- [`MLOps-Stock/docs/IMPLEMENTATION_STATUS.md`](MLOps-Stock/docs/IMPLEMENTATION_STATUS.md): bằng chứng kiểm thử và giới hạn.

> Hệ thống phục vụ nghiên cứu, không phải khuyến nghị đầu tư và không tự động đặt lệnh thật.
