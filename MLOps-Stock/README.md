# MLOps-Stock - Hệ thống Dự đoán Giá Cổ phiếu

Kho lưu trữ này chứa mã nguồn và luồng tích hợp liên tục (Continuous Integration - CI) cho hệ thống MLOps-Stock. Dự án tập trung vào việc áp dụng các mô hình học máy để phân tích và dự báo chuỗi thời gian dữ liệu chứng khoán.

## Kiến trúc Hệ thống & Công nghệ (Microservices)

Hệ thống được thiết kế theo kiến trúc vi dịch vụ (Microservices), bao gồm các thành phần cốt lõi sau:

- **Data API**: Đảm nhiệm việc thu thập, tiền xử lý và cung cấp dữ liệu chứng khoán theo thời gian thực.
- **Model APIs**:
  - **LightGBM API**: Phục vụ dự báo bằng mô hình Machine Learning truyền thống (LightGBM).
  - **TFT API**: Phục vụ dự báo bằng mô hình Deep Learning chuyên dụng cho chuỗi thời gian (Temporal Fusion Transformer).
- **Ensemble API**: Hoạt động như một Aggregation Layer, nhận kết quả từ các Model APIs và áp dụng logic kết hợp (Ensemble) để tối ưu hóa độ chính xác cuối cùng. Sử dụng Redis để caching.
- **Dashboard UI**: Giao diện người dùng trực quan để theo dõi các chỉ số và kết quả dự đoán.

## Luồng Tích hợp Liên tục (CI Pipeline)

Quy trình phát triển được tự động hóa hoàn toàn thông qua **GitHub Actions** với các Pipeline độc lập:
1. **Source Control & Trigger**: Kích hoạt khi có thay đổi trên mã nguồn, sử dụng cơ chế phát hiện thay đổi (path filtering) để chỉ build những dịch vụ bị ảnh hưởng (Monorepo strategy).
2. **Build & Package**: Đóng gói các dịch vụ thành các Docker Image bằng Docker Buildx.
3. **Security Scanning**: Tích hợp **Trivy** để quét các lỗ hổng bảo mật (CVEs) trên ảnh Docker trước khi phát hành.
4. **Image Signing**: Tích hợp **Cosign** để ký xác thực tính toàn vẹn của ảnh Docker.
5. **Registry Push**: Đẩy ảnh đã xác thực lên Docker Hub.
6. **Manifest Update**: Tự động cập nhật mã định danh ảnh (Image Hash) sang kho lưu trữ GitOps để kích hoạt quy trình triển khai (CD).

**Contributors:**
- Trần Việt Hoàng
- Lê Đình Hiếu


## Phiên bản hoàn thiện — Control Plane và Drift-aware MLOps

Project đã được mở rộng từ prediction microservices thành một control plane có thể chạy local và triển khai trên Kubernetes. Các phần mới gồm:

- PSI-based feature drift, performance drift và Page-Hinkley primitive.
- SQLite event store cho prediction logs, delayed ground truth, drift events và retrain jobs.
- Candidate/champion model registry có promotion, rejection, rollback và audit.
- Control API với RBAC demo (`viewer`, `analyst`, `admin`).
- Monitor API có Prometheus metrics và drift-triggered retraining policy.
- Dashboard hiển thị prediction, performance, drift, registry, retrain jobs và audit.
- Walk-forward evaluator so sánh Naïve baseline với LightGBM trên dữ liệu thật.
- Docker Compose mở rộng với Redis, MLflow, Control API và Monitor API.
- Helm/GitOps templates và CI workflow cho Control API/Monitor API.

## Quick start

```bash
pip install -r requirements.txt
python3 -m src.data_pipeline.download_latest
MODEL_VERSION=local-fpt-v1 DATA_VERSION=download-YYYY-MM-DD \
  python3 -m src.training.final_ensemble_train --symbol FPT
./scripts/start_local.sh
```

Mở Dashboard tại `http://127.0.0.1:8081`. API documentation nằm tại `http://127.0.0.1:8080/docs` và Control API tại `http://127.0.0.1:8085/docs`.

## Tài liệu bắt buộc

| Tài liệu | Nội dung |
|---|---|
| [`docs/SETUP.md`](docs/SETUP.md) | Cài đặt local, Compose, training, walk-forward và Kubernetes |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Drift, alert, retrain, promotion, rollback, backup và incident |
| [`docs/DEFENSE_NOTES.md`](docs/DEFENSE_NOTES.md) | Lý thuyết, câu hỏi phản biện và giới hạn cần trình bày |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Kiến trúc logical, lifecycle và Hybrid Cloud |
| [`scripts/run_walk_forward.py`](scripts/run_walk_forward.py) | Benchmark leakage-aware trên dữ liệu thật |

## Kiểm thử

```bash
python3 -m pytest -q
```

Các test hiện có kiểm tra API contracts cũ, decision policy, indicators, drift metrics, policy, registry và event store. Trước khi demo, cần chạy test, tải snapshot dữ liệu và kiểm tra health của các service.
