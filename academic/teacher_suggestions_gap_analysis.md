# Đối chiếu đề xuất của giảng viên với báo cáo nền và proposal 3 tháng

## Quy ước đánh giá

- **Đã có/đã triển khai:** Đã xuất hiện rõ trong báo cáo `NT114_report.docx` và/hoặc đã được thiết kế thành nội dung bắt buộc trong proposal 3 tháng.
- **Đã có nhưng cần hoàn thiện:** Đã có ý tưởng, một phần code hoặc thiết kế, nhưng cần bổ sung tiêu chí, thực nghiệm, policy hoặc bằng chứng.
- **Mới ở mức mở rộng:** Đã được đưa vào proposal như hướng nâng cao, chưa phải phần bắt buộc hoặc chưa có bằng chứng triển khai.
- **Chưa có rõ:** Chưa được đặc tả đủ để xem là một hạng mục nghiệm thu.

## Ma trận tổng hợp

| Đề xuất của giảng viên | Trong báo cáo nền | Trong proposal 3 tháng | Đánh giá hiện tại | Việc cần làm để xác nhận hoàn thành |
|---|---|---|---|---|
| Tên đề tài Ensemble LightGBM + TFT + Drift + Web + Hybrid Cloud | Có LightGBM, TFT, Ensemble, Web, Hybrid Cloud; Drift chưa hoàn chỉnh | Có đầy đủ trong tên và mục tiêu | **Đã có về định hướng** | Chốt tên chính thức và không tuyên bố hệ thống giao dịch thật |
| Data drift | Chưa triển khai hoàn chỉnh | Có PSI, JS/KL, reference/current window, threshold, dashboard | **Đã có nhưng cần hiện thực** | Tạo drift job, lưu metric theo thời gian, test stable/drift scenario |
| Concept drift | Báo cáo chỉ nêu là hướng phát triển | Có rolling MAE/RMSE/DA, ADWIN/Page-Hinkley và delayed label | **Đã có trong proposal, chưa có bằng chứng** | Có ground-truth updater, replay lịch sử và report detector |
| PSI/KL/ADWIN/Page-Hinkley | Chưa có monitoring hoàn chỉnh | Có metric, calibration, hysteresis, cooldown | **Đã có thiết kế** | Chọn metric chính cho MVP; detector còn lại làm so sánh/replay |
| Threshold + alert + retrain trigger | Có decision policy, chưa có drift trigger | Có INFO/WARNING/CRITICAL, threshold, alert, candidate retrain | **Đã có thiết kế rõ** | Viết policy YAML/config và negative test chống retrain giả |
| Dashboard dự đoán | Đã có dashboard demo dự đoán | Có prediction dashboard, interval, version, timestamp | **Đã có** | Bổ sung actual-vs-predicted, multi-horizon và uncertainty |
| Visualization | Có hiển thị kết quả cơ bản | Có model comparison, drift timeline, performance chart | **Đã có nhưng cần mở rộng** | Chuẩn hóa chart, filter ticker/horizon/regime và lưu snapshot |
| Quản lý model version | Có MLflow và artifact, chưa đầy đủ champion/candidate | Có Registry, version, lineage, alias candidate/champion | **Có nền tảng, cần hoàn thiện** | Đăng ký model thật, metadata, promote/reject/rollback |
| Trigger retrain | Có training pipeline nhưng chủ yếu theo workflow/schedule | Có manual, scheduled và drift-triggered retrain | **Đã có một phần** | Endpoint/UI, job state, cooldown, audit và evaluation gate |
| Theo dõi drift | Chưa có hoàn chỉnh | Có Drift Dashboard và Monitoring API | **Mới ở mức thiết kế** | Logging feature/prediction, reference/current windows, event store |
| Quản lý Feature Store | Có feature engineering; chưa có Feature Store đầy đủ | Có Feature Registry/Feast tối giản | **Đã đưa vào, nhưng là phần cần triển khai** | Chọn Feast hoặc registry nội bộ; schema, version, offline/online consistency |
| User management cơ bản | Chưa có rõ | Có viewer/analyst/admin, JWT/token và audit | **Mới ở mức proposal** | Auth middleware, RBAC backend, test quyền và audit log |
| Fine-tune TFT theo chu kỳ | Có training TFT nhưng chưa có fine-tuning policy rõ | Có scheduled retrain/candidate và tuning | **Có ý tưởng, chưa đặc tả đầy đủ** | Phân biệt retrain from scratch với fine-tune; lưu parent version và config |
| Fine-tune LightGBM | Có training lại LightGBM | Có tuning/candidate retrain | **Có thể làm, nhưng không nên gọi online learning** | Dùng retrain/tuning theo batch; không cập nhật từng mẫu nếu chưa kiểm chứng |
| Optuna/Ray Tune | Chưa có rõ | Có Optuna giới hạn; Ray Tune là nâng cao | **Đã có kế hoạch** | Time-series CV, giới hạn trial, log search space và best trial |
| Online/continual learning | Chưa có | Chỉ nêu là stretch/không ưu tiên | **Chưa có bắt buộc** | Không đưa vào mục tiêu chính; nếu làm phải có chống leakage và rollback |
| Pipeline MLOps hoàn chỉnh | Đã có data/training/model-sync workflows, MLflow, KFP, CI/CD | Có ingest–validate–feature–train–evaluate–register–serve–monitor–retrain | **Đã có nền tảng tốt** | Nối thành một lifecycle có evidence và failure handling |
| Experiment Tracking MLflow | Đã có triển khai MLflow, PostgreSQL, S3 artifact | Có params, metrics, artifact, lineage | **Đã có** | Chuẩn hóa tags: data version, code SHA, feature version, horizon |
| Model Registry + Versioning | MLflow/artifact đã có; registry chưa mô tả đầy đủ | Có candidate/champion, alias, gate, rollback | **Đã có định hướng, cần bằng chứng** | Tạo version thật và demo promotion/rejection/rollback |
| CI/CD training và serving | Có GitHub Actions, build, scan, sign, staging/prod workflow | Có pr-gate, data, training, drift, retrain, deploy | **Đã có** | Bổ sung integration test, data test và production approval |
| Monitoring Prometheus/Grafana hoặc custom | Có metrics-server/monitoring hạ tầng; model monitoring chưa hoàn chỉnh | Có custom metrics và Prometheus/Grafana là lựa chọn | **Có một phần** | Chọn một phương án chính, định nghĩa metric/alert/runbook |
| Automated retraining khi drift | Có training pipeline, chưa có drift trigger | Có drift policy, candidate retrain, evaluation gate | **Mới được thiết kế** | Historical replay, trigger test, candidate/champion test |
| Hybrid Cloud thực tế | Đã có K3s on-premise + EKS AWS + Tailscale + Terraform | Có lightweight và full hybrid options | **Đã có nền tảng mạnh** | Đóng gói architecture evidence, access control, backup/restore |
| On-prem/private cho training | Đã có K3s on-premise cho KFP/training/CI | Có private training environment | **Đã có** | Chứng minh workload và data boundary |
| Public cloud cho serving/storage/scaling | Đã có EKS, S3, model APIs | Có public serving và object storage | **Đã có** | Chứng minh serving lấy đúng champion artifact, test scaling/health |
| Kubernetes hybrid + object storage | Đã có hướng K3s/EKS, Helm, ArgoCD, S3 | Có full Kubernetes là phương án nâng cao | **Đã có, nhưng cần ưu tiên** | Không để dựng cluster làm trễ model/drift; dùng lightweight nếu cần |
| Ensemble strategy rõ ràng | Đã có stacking Linear Regression, bất định disagreement | Có equal-weight, weighted average, stacking, dynamic weighting | **Đã có tốt** | Chốt weighted average là MVP; stacking dùng OOF; dynamic là nâng cao |
| Dynamic weighting theo performance | Chưa có rõ | Có dynamic weighting ở phần nâng cao | **Mới ở mức mở rộng** | Rolling metric, smoothing, cooldown và ablation |
| Technical indicators | Đã có SMA, RSI, MACD, Bollinger, log return | Có mở rộng volatility, volume, EMA/ATR | **Đã có** | Data dictionary, feature version, leakage test |
| Sentiment | Báo cáo nêu là hạn chế/chưa tích hợp | Có thể làm hướng mở rộng | **Chưa có bắt buộc** | Chỉ làm nếu nguồn có timestamp, quality và tránh leakage |
| Macro features | Chưa có đầy đủ | Có đưa vào phạm vi mở rộng tháng 2 | **Mới ở mức kế hoạch** | Chọn 1–3 nguồn, ghi available_at, ablation trước/sau |
| Multi-horizon 1/5/10 ngày | Báo cáo chính là T+3 | Proposal có T+1/T+5/T+10 benchmark | **Đã có kế hoạch** | Viết target/evaluator multi-horizon và báo cáo theo horizon |
| Uncertainty quantification | Có uncertainty từ disagreement giữa model | Có quantile TFT, pinball, coverage, residual fallback | **Có nền tảng, cần nâng cấp** | Phân biệt disagreement với calibrated interval; đánh giá coverage |
| Backtesting | Có mô tả decision policy, benchmark còn hạn chế | Có walk-forward, holdout, regime analysis, replay | **Đã có yêu cầu rõ** | Chạy thật tối thiểu 3 folds + holdout cuối |
| Walk-forward validation nghiêm ngặt | Chưa đầy đủ trong báo cáo | Là tiêu chí bắt buộc | **Đã có trong proposal** | Freeze test holdout, train-only preprocessing, report variance |
| So sánh Ensemble vs LGBM vs TFT | Có model riêng và Ensemble | Có bảng ablation M0–M7 | **Đã có** | Chạy cùng dataset/folds/horizon và công bố kết quả |
| Trước/sau fine-tuning | Chưa có benchmark rõ | Có tuning matrix và candidate comparison | **Đã có kế hoạch** | So sánh default vs tuned, không chỉ báo best run |
| Trước/sau drift detection + retrain | Chưa có | Có replay scenario và candidate/champion | **Đã có thiết kế, cần thực nghiệm** | So sánh static champion với drift-aware retraining |
| MAE/RMSE/MAPE | Có đề cập một số metric | Có MAE/RMSE/sMAPE/MAPE | **Đã có** | Chốt sMAPE là metric chính nếu MAPE bất ổn gần 0 |
| Directional Accuracy | Có trong đề xuất/báo cáo hướng đánh giá | Có trong metrics và gate | **Đã có** | Định nghĩa hướng và xử lý trường hợp return bằng 0 |
| Sharpe trading simulation | Có decision policy, chưa có benchmark thực | Có nhưng chỉ là metric phụ | **Có giới hạn** | Chỉ mô phỏng có transaction cost; không dùng làm claim đầu tư |
| SHAP cho LightGBM | Chưa có | Có trong tháng 2/Explainability | **Mới ở mức mở rộng** | Tạo global/local explanation và lưu model version |
| Attention của TFT | Chưa có đầy đủ | Có attention/variable selection summary | **Mới ở mức mở rộng** | Chỉ trình bày như interpretability aid, không claim causal |
| A/B testing production | Chưa có | Chỉ đề xuất shadow/canary/A-B simulation | **Chưa có bắt buộc** | Là stretch; có thể mô phỏng traffic trước |
| Cost monitoring Hybrid Cloud | Chưa có rõ | Có ở phần nâng cao | **Chưa có bắt buộc** | Theo dõi CPU, storage, runtime, request và ước tính chi phí |
| Alert email/Slack/Telegram | Chưa có hoàn chỉnh | Có Web alert và webhook/email demo | **Đã có hướng** | Chọn một kênh chính; làm dedup/cooldown |

## Kết luận nhanh

### Đã có tương đối đầy đủ

Các phần đã có nền tảng mạnh gồm tên đề tài, LightGBM, TFT rút gọn, Ensemble, technical indicators, MLflow, artifact storage, CI/CD, Hybrid Cloud, training pipeline, Web prediction dashboard và các API serving. Báo cáo nền đã triển khai nhiều thành phần hạ tầng thực tế như K3s on-premise, EKS, S3, Tailscale, Terraform, GitHub Actions, Helm và ArgoCD.

### Đã có trong proposal nhưng cần biến thành bằng chứng thực nghiệm

Các phần này đã được thiết kế rõ nhưng chưa thể coi là hoàn thành nếu chưa chạy thật: data drift, concept/performance drift, threshold, alert, retrain trigger, candidate/champion registry, promotion gate, rollback, walk-forward validation, historical replay, multi-horizon, quantile uncertainty, RBAC, audit, Feature Registry/Feast, explainability và backup/restore.

### Chưa nên coi là đã có

Online/continual learning, A/B testing production, canary production đầy đủ, sentiment pipeline, cost monitoring chi tiết và full security production chưa nên ghi là đã triển khai. Chúng chỉ nên nằm trong mục “hướng phát triển” hoặc “stretch goal” cho đến khi có code, test và evidence.

## Danh sách việc cần bổ sung ưu tiên

1. Chọn một detector chính cho MVP: PSI cho data drift, rolling MAE/DA cho performance drift; ADWIN hoặc Page-Hinkley dùng trong historical replay.
2. Xây prediction log và delayed-label updater để khi T+3 xuất hiện có thể nối prediction với ground truth.
3. Hiện thực drift policy có sample minimum, threshold, hysteresis, cooldown và severity.
4. Xây candidate/champion registry với evaluation gate, promotion, rejection và rollback.
5. Chạy walk-forward benchmark thống nhất cho Naïve, LightGBM, TFT và Ensemble.
6. Bổ sung historical replay để chứng minh drift-triggered retraining thay vì chỉ mô tả trên giấy.
7. Chọn Feast hoặc Feature Registry nội bộ; không triển khai song song cả hai.
8. Bổ sung RBAC backend và audit log; không chỉ ẩn nút trên giao diện.
9. Thêm SHAP và attention/variable summary nếu phần lõi đã ổn định.
10. Đưa sentiment, online learning, A/B production và cost monitoring vào phần nâng cao, không dùng làm tiêu chí bắt buộc ban đầu.
