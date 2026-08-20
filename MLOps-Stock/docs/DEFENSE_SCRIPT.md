# Defense Script — MLOps Stock

## 1. Câu mở đầu trong 45 giây

Đề tài xây dựng một hệ thống dự đoán giá cổ phiếu T+3 theo kiến trúc MLOps. Điểm trọng tâm không chỉ là huấn luyện một mô hình, mà là đưa mô hình qua một vòng đời có thể kiểm soát: thu thập dữ liệu, feature engineering, huấn luyện LightGBM và TFT, kết hợp dự báo, serving qua API, theo dõi drift, tạo retraining job, đánh giá candidate và promotion/rollback có audit. Hệ thống chạy được trên Windows Docker Desktop ở local-offline mode, đồng thời có Helm/GitOps manifests cho định hướng Hybrid Cloud.

Cần nhấn mạnh rằng đây là hệ thống nghiên cứu và demo MLOps, **không phải công cụ bảo đảm giá hoặc lợi nhuận**. Các số liệu được báo cáo theo snapshot dữ liệu và protocol cụ thể, không được diễn giải thành khả năng dự báo bất biến trong tương lai.

## 2. Luồng trình bày 10 slide

| Slide | Nội dung | Evidence mở khi cần |
|---:|---|---|
| 1 | Bài toán, mục tiêu và phạm vi T+3 | `README.md`, `docs/ARCHITECTURE.md` |
| 2 | Vì sao cần MLOps thay vì chỉ train model | `docs/DEFENSE_NOTES.md` |
| 3 | Data pipeline và 13 features | `data/FPT.csv`, `models/FPT_artifact_manifest.json` |
| 4 | LightGBM, TFT skeleton và stacking Ensemble | `src/training/ensemble_trainer.py` |
| 5 | Leakage-aware walk-forward evaluation | `docs/DEFENSE_METRICS.md`, `artifacts/evaluation/FPT_walk_forward_final.json` |
| 6 | Microservices và Docker Compose runtime | `docker-compose.yml`, Dashboard |
| 7 | Drift detection và policy hysteresis | `src/mlops_control/drift.py`, `artifacts/evaluation/FPT_drift_replay_final.json` |
| 8 | Control plane, registry, RBAC và retraining | `artifacts/defense_demo_evidence.txt`, `artifacts/retraining_guard_evidence.json` |
| 9 | Demo prediction và observability | `artifacts/post_retrain_smoke_output.txt` |
| 10 | Kết luận, giới hạn và hướng phát triển | `docs/DEFENSE_GAP_ANALYSIS.md` |

## 3. Kịch bản demo trực tiếp

Đầu tiên, chạy `scripts\start_local.ps1` và chờ readiness checks. Mở `http://127.0.0.1:8081` để giới thiệu Dashboard. Tiếp theo mở `http://127.0.0.1:8080/docs`, gọi endpoint prediction cho FPT và chỉ ra JSON có component prediction từ TFT/LightGBM, Ensemble output, uncertainty và decision policy.

Mở `http://127.0.0.1:8085/docs`, gọi health và registry. Với role `viewer`, gọi `GET /retrain/jobs?limit=10` để xem lịch sử job. Với role `analyst`, gọi drift evaluation bằng reference/current windows; chỉ ra `severity=critical`, `action=retrain` sau khi persistence policy đạt ngưỡng. Gọi `POST /retrain` bằng role `viewer` và chỉ ra HTTP `403`. Sau đó mở audit để chỉ ra event `register_candidate` và `promote`.

Nếu không muốn phụ thuộc thao tác Swagger, chạy `powershell -ExecutionPolicy Bypass -File scripts\defense_demo.ps1`. Script lưu evidence tại `artifacts/defense_demo_evidence.txt` và thực hiện cả official smoke test.

## 4. Số liệu phải nói đúng

Walk-forward final trên FPT snapshot sử dụng 7 expanding folds, validation size 60 và gap 3. Benchmark bounded gồm bốn model: Naive có mean MAE `2352.01`, RMSE `3012.89`, Directional Accuracy `42.86%`; LightGBM có MAE `4205.20`, RMSE `4990.57`, Directional Accuracy `47.38%`; TFT có MAE `8441.87`, RMSE `9401.15`, Directional Accuracy `50.00%`; equal-weight Ensemble có MAE `5897.04`, RMSE `6723.20`, Directional Accuracy `48.33%`.[1]

Cách diễn giải đúng là không model nào thắng toàn diện: Naive tốt nhất trên MAE/RMSE, TFT có Directional Accuracy cao nhất trong run bounded một epoch, còn equal-weight Ensemble chưa chứng minh ưu thế tổng thể. Đây là ablation result hợp lệ; không được nói Ensemble luôn tốt hơn.[2]

Automated retraining run đã tạo candidate version `2` cho `stock-ensemble-FPT-t3`. MAE giảm từ `0.2872670182790942` xuống `0.2867988409553559`, RMSE giảm từ `0.3548542435466494` xuống `0.35435845756971923`, Directional Accuracy giữ ở `46.875`; evaluation gate passed và candidate được promote.[3] Các MAE/RMSE này thuộc scaled target holdout space, không được so sánh trực tiếp với MAE giá trong walk-forward.

## 5. Hỏi đáp phản biện trọng điểm

### Hội đồng: “Ensemble có luôn tốt hơn model đơn không?”

Không. Ensemble là giả thuyết cần kiểm chứng. Trong implementation, TFT và LightGBM tạo component predictions, meta-learner học cách kết hợp trong target space được ghi ở manifest. Benchmark bounded mới đã chạy đủ Naive/LightGBM/TFT/equal-weight Ensemble; kết quả không cho thấy Ensemble thắng toàn diện. Vì vậy hệ thống giữ evaluation gate và không mặc định promote chỉ vì candidate là Ensemble.

### Hội đồng: “PSI critical có nghĩa là concept drift không?”

Không. PSI đo thay đổi phân phối input, tức data drift. Concept/performance drift cần delayed target và error stream. Hệ thống có rolling performance metrics và Page-Hinkley primitive, nhưng historical PSI replay không tự nó chứng minh concept drift production. Chính sách yêu cầu persistence và cooldown để tránh một cảnh báo đơn lẻ gây retrain loop.

### Hội đồng: “Nếu model mới xấu hơn thì sao?”

Candidate không tự động trở thành champion. Evaluation gate so sánh MAE, RMSE và Directional Accuracy với champion. Worker snapshot các artifact trước retraining và khôi phục nếu candidate bị reject. Registry lưu audit event để biết ai, lúc nào và vì sao promotion hoặc rejection xảy ra.

### Hội đồng: “Tại sao retraining đầu tiên từng thất bại?”

Trong quá trình nghiệm thu đã phát hiện hai lỗi triển khai thực tế: local-offline Control API vẫn trỏ tới hostname MLflow tùy chọn và experiment cũ có artifact location không writable. Hai lỗi đã được sửa bằng SQLite local, artifact root writable và experiment isolation. Đây là evidence của quá trình hardening thật, không phải lỗi bị che giấu.

### Hội đồng: “SQLite và local Docker có production-ready không?”

SQLite/local Docker phù hợp cho demo, development và reproducible acceptance trên laptop. Production Hybrid Cloud cần PostgreSQL hoặc database managed, object storage versioned, secrets management, HA, backup, network policy và observability platform. Project có Helm/GitOps design nhưng không tuyên bố cluster production đã được triển khai nếu chưa có cluster evidence.

### Hội đồng: “TFT trong đề tài có phải Temporal Fusion Transformer nguyên bản đầy đủ không?”

Không nên gọi như vậy. Code sử dụng một TFT skeleton nghiên cứu với variable selection, gated residual blocks, LSTM, Transformer encoder và output head. Đây là một implementation rút gọn phù hợp phạm vi đồ án, không phải tuyên bố tái tạo toàn bộ paper implementation.

## 6. Kết luận 30 giây

Đóng góp chính của đề tài là chứng minh một vòng đời MLOps hoàn chỉnh ở mức có thể chạy và kiểm thử: prediction path hoạt động, drift policy tạo retrain decision, retraining worker tạo candidate, evaluation gate kiểm tra candidate, registry promotion có audit, RBAC giới hạn hành động và artifact được bảo vệ khi candidate không đạt. Các giới hạn về snapshot, benchmark TFT/Ensemble và Hybrid Cloud production được nói rõ để kết luận có cơ sở và trung thực.

## References

[1]: ../artifacts/evaluation/FPT_walk_forward_ensemble_final.json "Final bounded walk-forward report for Naive, LightGBM, TFT and Ensemble"
[2]: ../docs/DEFENSE_GAP_ANALYSIS.md "Defense gap analysis and evidence matrix"
[3]: ../artifacts/retraining_guard_evidence.json "Champion evaluation gate regression evidence"
