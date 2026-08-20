# MLOps Stock — Operations Runbook

## 1. Trạng thái model

Hệ thống duy trì hai khái niệm: **candidate** là model vừa train, chưa được phép phục vụ production; **champion** là version đã qua evaluation gate và đang được serving. Mọi promotion, rejection và rollback phải xuất hiện trong audit log.

```text
data snapshot -> training -> candidate -> evaluation gate -> champion
                                      \-> rejected
champion -> rollback(previous approved version)
```

## 2. Drift policy

Data drift dùng PSI theo từng feature, với ngưỡng mặc định warning `0.10` và critical `0.25`. Đây là điểm khởi đầu cần hiệu chỉnh theo dữ liệu, không phải chuẩn bất biến. Performance drift dùng rolling MAE, Directional Accuracy và Page-Hinkley trên error stream khi delayed labels đã xuất hiện.

Policy có bốn cơ chế bảo vệ. Cửa sổ phải đủ mẫu; critical signal phải lặp lại đủ số lần; hệ thống có hysteresis/cooldown để tránh oscillation; và retraining luôn tạo candidate trước khi promote.

| Severity | Điều kiện khái quát | Hành động |
|---|---|---|
| Stable | Không vượt ngưỡng | Tiếp tục observe |
| Warning | Một hoặc nhiều feature/performance metric vượt warning | Alert, chưa retrain ngay |
| Critical pending | Có critical nhưng chưa đủ consecutive checks | Alert và tiếp tục theo dõi |
| Critical | Critical kéo dài hoặc Page-Hinkley phát hiện | Tạo candidate retrain |
| Critical cooldown | Đang trong thời gian cooldown | Alert, không tạo job lặp |

## 3. Xử lý alert

Khi nhận cảnh báo, analyst kiểm tra `/drift/events`, `/performance`, thời gian reference/current window và nguồn dữ liệu. Nếu event do lỗi upstream hoặc thiếu mẫu, đánh dấu operational issue thay vì retrain. Nếu event xuất phát từ distribution shift thật, để worker tạo candidate.

```bash
curl -H 'X-Role: viewer' http://127.0.0.1:8085/drift/events?limit=20
curl -H 'X-Role: viewer' http://127.0.0.1:8085/performance?ticker=FPT
curl -H 'X-Role: viewer' http://127.0.0.1:8085/retrain/jobs?limit=20
```

## 4. Manual retrain

Manual retrain cần role analyst hoặc admin. Job chạy nền, tải snapshot dữ liệu, train model, đọc manifest, đăng ký candidate và chạy gate so với champion.

```bash
curl -X POST http://127.0.0.1:8085/retrain \
  -H 'Content-Type: application/json' -H 'X-Role: analyst' \
  -d '{"ticker":"FPT","horizon":3,"trigger_type":"manual","epochs":5}'
```

Theo dõi job:

```bash
curl -H 'X-Role: viewer' http://127.0.0.1:8085/retrain/jobs
```

## 5. Promotion và rollback

Admin chỉ promote candidate khi report chứng minh candidate không làm MAE/RMSE xấu hơn quá ngưỡng cho phép, Directional Accuracy không giảm vượt mức cho phép và artifact có đúng feature/data/code metadata.

```bash
curl -X POST http://127.0.0.1:8085/models/promote \
  -H 'Content-Type: application/json' -H 'X-Role: admin' \
  -d '{"model_name":"stock-ensemble-FPT-t3","version":"2","reason":"manual review approved"}'

curl -X POST http://127.0.0.1:8085/models/rollback \
  -H 'Content-Type: application/json' -H 'X-Role: admin' \
  -d '{"model_name":"stock-ensemble-FPT-t3","version":"1","reason":"post-deploy regression"}'
```

## 6. Ground-truth updater

Prediction của T+3 chỉ được đánh giá sau khi giá thật của ngày đích xuất hiện. Control API cung cấp endpoint cập nhật ground truth; job scheduler hoặc data pipeline có thể gọi endpoint này bằng prediction ID. Khi có nhãn, hệ thống tính absolute error và directional correctness để phục vụ performance drift.

```bash
curl -X POST http://127.0.0.1:8085/predictions/<PREDICTION_ID>/label \
  -H 'Content-Type: application/json' -H 'X-Role: analyst' \
  -d '{"ground_truth":70000}'
```

## 7. Backup và khôi phục

Các file cần backup trong local demo là `artifacts/control_plane.sqlite3`, `artifacts/registry/registry.json`, `models/`, `mlruns/`, `data/` và các evaluation report. Trong Kubernetes, artifact nên nằm trong object storage versioned; SQLite chỉ phù hợp local hoặc demo, production nên chuyển event store sang PostgreSQL.

```bash
mkdir -p backups/$(date +%Y%m%d)
cp -a artifacts models mlruns data backups/$(date +%Y%m%d)/
```

## 8. Incident response

Nếu prediction API lỗi, kiểm tra health và logs Data/TFT/LightGBM/Ensemble theo thứ tự. Nếu model trả kết quả bất thường, kiểm tra model version, feature version, scaler và meta input space trong manifest; không promote model mới nếu chưa có rollback version. Nếu drift job lỗi, giữ champion cũ, ghi operational event và sửa data pipeline trước khi trigger retrain lại.

## 9. Bảo mật

`X-Role` hiện là RBAC tối giản cho local demo, không phải authentication production. Khi triển khai thật, thay bằng OIDC/JWT, phân quyền ở ingress/API gateway, TLS, secret manager, NetworkPolicy, non-root containers và IAM/IRSA. Không dùng các mật khẩu xuất hiện trong tài liệu cũ; tất cả credential phải được tạo từ Kubernetes Secret hoặc cloud secret manager.
