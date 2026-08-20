# Defense Gap Analysis and Demo Plan

## 1. Mục tiêu của tài liệu

Tài liệu này là checklist trung thực trước khi bảo vệ đề tài “Xây dựng hệ thống dự đoán giá chứng khoán dựa trên kiến trúc MLOps với mô hình Ensemble (LightGBM + Temporal Fusion Transformer), phát hiện Model Drift và nền tảng Web trên Hybrid Cloud”. Mọi tuyên bố trong slide cần được gắn với một trong ba loại evidence: **unit/evaluation evidence**, **runtime evidence** hoặc **architecture/design evidence**.

## 2. Ma trận yêu cầu và bằng chứng

| Yêu cầu | Trạng thái | Evidence được phép trình bày |
|---|---|---|
| Feature engineering OHLCV và technical indicators | Đã triển khai | Source code, FPT snapshot, feature contract |
| LightGBM inference | Đã kiểm thử | `/predict/lgbm`, Docker smoke output |
| TFT inference | Đã kiểm thử | `/predict/tft`, Docker smoke output |
| Stacking Ensemble | Đã triển khai và serving | Ensemble response, manifest `meta_input_space=scaled_target` |
| Walk-forward validation | Đã triển khai cho Naive/LightGBM | `FPT_walk_forward.json`, 7 expanding folds, gap=3 |
| Walk-forward TFT/Ensemble | Chưa phải evidence chính thức | Không tuyên bố đã có nếu chưa chạy evaluator chuyên biệt |
| Data drift | Đã kiểm thử | PSI, drift replay, Control API `/drift/evaluate` |
| Performance/concept drift | Đã triển khai primitive | Delayed-label metrics, Page-Hinkley; cần label thật theo thời gian để kết luận production |
| Automated retraining | Đã chạy thật | `retraining_final_evidence.txt`, job promoted |
| Champion/candidate gate | Đã chạy thật | `retraining_guard_evidence.json`, candidate version 2 promoted after metric improvement |
| Artifact rollback safety | Đã triển khai | Retraining worker backup/restore logic; nên demo bằng candidate reject fixture nếu cần |
| Model registry/audit | Đã triển khai | Control API `/models`, `/audit`, SQLite event store và filesystem registry |
| RBAC | Đã kiểm thử | Viewer retraining request trả HTTP 403 |
| Web Dashboard | Đã kiểm thử | HTTP 200, prediction/control-plane widgets |
| Hybrid Cloud | Đã thiết kế và có manifests | K3s/EKS architecture, Helm/GitOps; không tuyên bố cluster production đã chạy nếu chưa có cluster evidence |
| CI/CD | Đã cấu hình | GitHub Actions workflow; cần phân biệt workflow definition với deployed pipeline run |

## 3. Số liệu hiện có

Walk-forward report hiện có 7 expanding-window folds với train sizes từ 300 đến 660, validation size 60 và gap 3. Trên FPT snapshot, Naive baseline có mean MAE khoảng `2358.30`, mean RMSE khoảng `3018.64`, mean Directional Accuracy khoảng `42.56%`; LightGBM có mean MAE khoảng `3495.49`, mean RMSE khoảng `4227.16`, mean Directional Accuracy khoảng `50.42%`. Kết quả này **không cho phép nói LightGBM tốt hơn Naive trên MAE/RMSE**, nhưng cho thấy LightGBM có Directional Accuracy trung bình cao hơn trong snapshot này. Cần trình bày đúng cả điểm mạnh và điểm yếu.

Artifact holdout/retraining của Ensemble ghi nhận MAE và RMSE trong **scaled target space**, không phải đơn vị giá trực tiếp. Vì vậy không được đặt các metric này cạnh MAE giá của walk-forward mà không ghi rõ không gian đo. Docker serving evidence ghi nhận FPT current price `68800.0`, Ensemble prediction `72646.32186951733`, TFT component `91865.71875`, LightGBM component `70749.73788562209`, disagreement uncertainty `30.6918%`. Đây là evidence pipeline, không phải accuracy claim.

## 4. Kịch bản demo bảo vệ trong 7–10 phút

Đầu tiên, mở Dashboard tại `http://127.0.0.1:8081` và giải thích service graph: Data API cung cấp feature, TFT và LightGBM tạo component predictions, Ensemble áp dụng meta-learner, Redis cache và Control API ghi prediction event. Tiếp theo, mở Swagger của Ensemble tại `http://127.0.0.1:8080/docs` và gọi `GET /predict/FPT`.

Sau đó mở Control API tại `http://127.0.0.1:8085/docs`. Gọi drift evaluation với hai cửa sổ reference/current và `X-Role: analyst`; chỉ ra PSI critical, consecutive-check policy và action `retrain`. Gọi cùng endpoint retraining với `X-Role: viewer` để chứng minh RBAC trả `403`. Cuối cùng, mở `/retrain/jobs`, `/models` và `/audit` để chỉ ra job lifecycle, candidate/champion và audit trail.

Nếu hội đồng hỏi retraining có thật không, mở `artifacts/retraining_final_evidence.txt`: job đã download dữ liệu, train artifact, ghi MLflow offline, register candidate và promote. Nếu hỏi model mới kém thì sao, mở `retraining_guard_evidence.json` và giải thích evaluation gate, champion comparison cùng cơ chế backup/restore.

## 5. Các câu hỏi khó cần trả lời nhất quán

**“Vì sao LightGBM có MAE walk-forward tốt hơn TFT/Ensemble không?”** Câu trả lời phải dựa trên evidence đã có, không giả định. Hiện walk-forward chính thức chỉ benchmark Naive và LightGBM; TFT/Ensemble có holdout và runtime evidence. Đây là giới hạn evaluation cần nói rõ và là hướng mở rộng, không được bù bằng lời khẳng định.

**“Model drift có phải concept drift không?”** Không. PSI là input/data drift. Concept hoặc performance drift cần delayed labels và error stream. Hệ thống có performance drift primitive và Page-Hinkley, nhưng replay PSI không tự động chứng minh concept drift production.

**“Tại sao candidate được promote?”** Vì candidate phải qua evaluation gate so với champion. Ở run đầu, registry được seed từ local artifact hoặc không có champion nên gate có lý do riêng. Ở run sau, candidate version 2 có MAE/RMSE cải thiện so với version 1 nên passed. Nếu fail, worker khôi phục artifact backup.

**“Đây có phải TFT nguyên bản đầy đủ không?”** Không nên nói như vậy. Code hiện là TFT skeleton nghiên cứu có variable selection, LSTM, Transformer encoder và output head. Báo cáo phải gọi đúng là simplified/research TFT implementation.

**“Hybrid Cloud đã chạy production chưa?”** Có kiến trúc, Helm/GitOps và phân tách training/serving; evidence local Docker đã chạy thật. Nếu chưa có log cluster K3s/EKS, phải gọi phần cloud là deployment design/manifest readiness, không gọi là production deployment.

## 6. Những điều không được trình bày quá mức

Không nói hệ thống dự đoán chính xác giá, không nói đảm bảo lợi nhuận, không gọi disagreement là xác suất, không gọi drift replay là bằng chứng production concept drift, không gọi Docker local-offline là full Hybrid Cloud production, và không nói Ensemble luôn thắng model đơn. Cách trình bày trung thực này làm đề tài đáng tin cậy hơn trước phản biện.

## 7. Checklist trước ngày bảo vệ

Chạy `python -m pytest -q` và lưu kết quả 28 passed. Chạy `python scripts/smoke_test.py` trên Compose stack. Kiểm tra `docker-compose ps` có đủ project services. Mở Dashboard, Ensemble Swagger và Control Swagger. Chuẩn bị sẵn `IMPLEMENTATION_STATUS.md`, `SETUP.md`, `DEFENSE_NOTES.md`, `FPT_walk_forward.json`, `FPT_drift_replay.json`, `final_smoke_output.txt` và `retraining_guard_evidence.json`. Cuối cùng, tắt background retraining jobs không cần thiết và giữ một snapshot backup của `models/`, `data/`, `artifacts/control_plane.sqlite3` trước buổi demo.

## Update: TFT/Ensemble walk-forward evaluator

The project now includes `scripts/run_walk_forward_ensemble.py`, which evaluates Naive, LightGBM, TFT and an equal-weight Ensemble on the same seven expanding folds with gap 3 and a 60-step temporal window. The final report is stored at `artifacts/evaluation/FPT_walk_forward_ensemble_final.json`.

The benchmark is intentionally labeled **bounded** because TFT uses one CPU epoch per fold to keep the acceptance run reproducible on a laptop. Results are now available for defense, but they should not be presented as a tuned or production-quality TFT study. In the current run, Naive remains strongest on MAE/RMSE, while TFT reaches the highest Directional Accuracy among the four at 50.00%; the equal-weight Ensemble does not dominate all metrics. This is a valid negative/ablation result and supports the thesis claim that model lifecycle and evaluation gates are necessary rather than assuming Ensemble superiority.
