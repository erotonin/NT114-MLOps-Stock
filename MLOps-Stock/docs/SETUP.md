# MLOps Stock — Setup and Run Guide

## 1. Phạm vi

Project gồm hai lớp. Lớp ứng dụng nằm trong repository `MLOps-Stock`; lớp GitOps nằm trong `NT114_manifests`. Chế độ local chạy được mà không cần Kubernetes, còn Docker Compose và Helm phục vụ demo triển khai gần production.

> Hệ thống phục vụ mục đích nghiên cứu và minh họa MLOps. Dự báo không phải khuyến nghị đầu tư và không được dùng để tự động đặt lệnh thật.

## 2. Yêu cầu

Môi trường local cần Python 3.11 trở lên, pip, Git, khoảng 4 GB RAM cho API và 6 GB trở lên nếu chạy TFT training. Docker Compose là tùy chọn. Kubernetes, Helm, ArgoCD và AWS CLI chỉ cần khi dựng Hybrid Cloud.

## 3. Cài đặt local

```bash
git clone https://github.com/Quackusarle/MLOps-Stock.git
cd MLOps-Stock
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Nếu môi trường dùng Python được quản lý bởi hệ điều hành, có thể dùng `pip install --user` hoặc package manager tương ứng; không commit virtual environment vào Git.

## 4. Tải dữ liệu thật và huấn luyện

```bash
python3 -m src.data_pipeline.download_latest
MODEL_VERSION=local-fpt-v1 DATA_VERSION=download-YYYY-MM-DD \
  python3 -m src.training.final_ensemble_train --symbol FPT
```

Script tải dữ liệu OHLCV từ Yahoo Finance, tạo technical indicators, tạo target `close[t+3]`, fit scaler trên train split, train TFT và LightGBM, fit stacking meta-learner, lưu artifact vào `models/`, log experiment vào MLflow local và ghi manifest.

Để train các mã mặc định:

```bash
python3 -m src.training.final_ensemble_train
```

## 5. Chạy local stack không cần Docker

```bash
./scripts/start_local.sh
```

Các URL chính:

| Thành phần | URL |
|---|---|
| Dashboard | http://127.0.0.1:8081 |
| Ensemble API Swagger | http://127.0.0.1:8080/docs |
| Data API Swagger | http://127.0.0.1:8001/docs |
| TFT API Swagger | http://127.0.0.1:8002/docs |
| LightGBM API Swagger | http://127.0.0.1:8003/docs |
| Control API Swagger | http://127.0.0.1:8085/docs |
| MLflow local tracking | `./mlflow.db` (SQLite) |

Gọi thử prediction:

```bash
curl http://127.0.0.1:8080/predict/FPT
curl -H 'X-Role: viewer' http://127.0.0.1:8085/predictions?limit=10
curl -H 'X-Role: viewer' http://127.0.0.1:8085/models
```

Dừng các process do script khởi tạo:

```bash
./scripts/stop_local.sh
```

## 6. Docker Compose

```bash
docker compose up --build -d

docker compose ps
docker compose logs -f control-api
```

Compose khởi tạo Redis, MLflow, Data API, TFT API, LightGBM API, Ensemble API, Control API, Monitor API và Dashboard UI. Trước khi dự đoán, cần có model artifact. Có thể chạy training container riêng hoặc mount artifact đã train vào `models/`.

```bash
docker compose down
# Xóa dữ liệu demo, chỉ dùng khi muốn reset hoàn toàn
# docker compose down -v
```

## 7. Drift evaluation thủ công

Control API nhận hai cửa sổ dữ liệu cùng schema. Ví dụ tối giản:

```bash
curl -X POST http://127.0.0.1:8085/drift/evaluate \
  -H 'Content-Type: application/json' -H 'X-Role: analyst' \
  -d '{
    "ticker":"FPT",
    "reference":[{"close":68000,"volume":1000},{"close":68200,"volume":1100}],
    "current":[{"close":82000,"volume":1800},{"close":82500,"volume":1900}],
    "columns":["close","volume"],
    "consecutive_critical_checks":2
  }'
```

Trong thực tế, `min_samples` mặc định là 20; ví dụ trên chỉ minh họa contract. Monitor API định kỳ lấy reference/current windows từ dữ liệu thật, ghi drift event vào SQLite và tạo retraining job khi policy cho phép.

## 8. Walk-forward evaluation

```bash
python3 scripts/run_walk_forward.py --symbol FPT \
  --train-size 300 --validation-size 60 --step-size 60
```

Báo cáo được ghi vào `artifacts/evaluation/FPT_walk_forward.json`. Preprocessing được fit trong từng train fold; validation fold có gap để hạn chế nhìn trước target.

## 9. Kubernetes/ArgoCD

Sử dụng repository `NT114_manifests`. Cần build và push các image `data-api`, `tft-api`, `lgbm-api`, `ensemble-api`, `dashboard`, `control-api` và `monitor-api`; không lưu credential trong Git. Cập nhật tag image trong `values-dev.yaml` hoặc để GitHub Actions cập nhật tự động.

```bash
helm lint argocd/apps/mlops-stock
helm template mlops-stock argocd/apps/mlops-stock -f argocd/apps/mlops-stock/values-dev.yaml
kubectl apply -f argocd/apps/mlops-stock/...
```

Trong kiến trúc Hybrid Cloud, K3s/private cluster giữ training, dữ liệu nhạy cảm và control plane; EKS/public cluster phục vụ inference có giới hạn. Artifact phải đi qua object storage, IAM/IRSA và model promotion gate; không copy secret vào image hoặc manifest plaintext.

## 10. Environment variables quan trọng

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `LOCAL_MODELS_DIR` | `models` | Thư mục artifact local |
| `MODELS_CACHE_DIR` | `/tmp/models` | Cache artifact MLflow trong container |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | Tracking server; local nên dùng `sqlite:///absolute/path/mlflow.db` |
| `CONTROL_DB_PATH` | `artifacts/control_plane.sqlite3` | SQLite event store |
| `REGISTRY_PATH` | `artifacts/registry/registry.json` | Local model registry |
| `MONITOR_SYMBOLS` | `VNM,FPT,VCB,HPG` | Danh sách ticker monitor |
| `CHECK_INTERVAL_SECONDS` | `3600` | Chu kỳ drift check |
| `DRIFT_MIN_SAMPLES` | `20` | Số mẫu tối thiểu mỗi cửa sổ |
| `CONTROL_ALLOWED_ORIGINS` | `*` local | CORS; production phải giới hạn domain |

## 11. Troubleshooting

Nếu API trả lỗi model chưa train, kiểm tra `models/{TICKER}_artifact_manifest.json` và bốn artifact scaler/TFT/LightGBM/meta-learner. Nếu API cố kết nối `localhost:5000` dù đã có artifact local, đặt `LOCAL_MODELS_DIR` tuyệt đối vào thư mục `models`.

Nếu Docker build fail ở TFT, kiểm tra RAM và cache pip. Nếu ArgoCD OutOfSync, kiểm tra image tag, namespace, service account, PVC và logs của pod. Nếu drift luôn là `insufficient_sample`, tăng cửa sổ dữ liệu hoặc giảm threshold chỉ trong môi trường replay; không hạ threshold tùy tiện trên production.
