# MLOps Stock — Tài liệu ôn bảo vệ

## 1. Đề tài đóng góp gì?

Đề tài không chỉ train một mô hình dự báo giá. Đóng góp chính là xây dựng vòng đời MLOps có thể tái lập: dữ liệu được version hóa, feature có contract, experiment được tracking, artifact có registry/version, model được serving qua API, drift được monitoring, retraining tạo candidate và promotion/rollback có kiểm soát trên kiến trúc Hybrid Cloud.

Câu trả lời ngắn khi hội đồng hỏi “điểm mới là gì?” là: **sự kết hợp có kiểm soát giữa dự báo multi-model và vận hành model lifecycle, trong đó hệ thống không chỉ trả prediction mà còn phát hiện khi giả định dữ liệu/model không còn phù hợp và kích hoạt quy trình cập nhật an toàn.**

## 2. Vì sao chọn LightGBM và TFT?

LightGBM phù hợp với dữ liệu dạng bảng sau feature engineering vì huấn luyện nhanh, xử lý quan hệ phi tuyến và cho phép đo feature importance/SHAP. TFT phù hợp với chuỗi thời gian multi-horizon vì kết hợp biến selection, temporal processing và attention; kiến trúc này có thể cung cấp quantile forecast và các tín hiệu interpretability. Hai model có inductive bias khác nhau nên Ensemble có thể giảm phụ thuộc vào một họ mô hình, nhưng không mặc định rằng Ensemble luôn tốt hơn; đó là giả thuyết phải kiểm chứng bằng ablation.

## 3. Target T+3 và tránh leakage

Với mỗi thời điểm `t`, target là `close[t+3]`. Feature tại thời điểm t chỉ được tạo từ dữ liệu đã quan sát đến t. Scaler, feature selector và hyperparameter chỉ fit trên train window của mỗi fold. Validation/test không được dùng để tính mean/std, chọn feature hoặc fit meta-learner trước khi đánh giá cuối.

Một câu hỏi phản biện thường gặp là “Yahoo Finance có thể chỉnh dữ liệu quá khứ không?”. Câu trả lời là dữ liệu nguồn có thể được điều chỉnh hoặc thay đổi, vì vậy project lưu snapshot CSV, `data_version`, thời gian tải và hash/metadata để kết quả có thể tái lập tại một thời điểm.

## 4. Vì sao không dùng random split?

Random split làm các quan sát tương lai có thể xuất hiện trong train và phá vỡ thứ tự thời gian. Walk-forward validation mô phỏng cách hệ thống thật: train bằng quá khứ, có gap, kiểm tra trên tương lai, sau đó mở rộng train window. Kết quả cần báo cáo mean và standard deviation giữa các folds, không chỉ best fold.

## 5. Ensemble hiện tại hoạt động thế nào?

MVP sử dụng stacking. TFT và LightGBM tạo hai dự báo thành phần trong cùng target space; meta-learner Linear Regression học cách kết hợp hai dự báo trên dữ liệu out-of-fold/validation. Khi serving, component predictions phải được đưa về đúng input space của meta-learner; manifest hiện ghi `meta_input_space=scaled_target` để tránh lỗi scale-space. Nếu không có meta artifact, gateway fallback về weighted/equal average có kiểm soát.

## 6. Data drift và concept/performance drift khác nhau thế nào?

Data drift là phân phối input thay đổi, ví dụ volume hoặc volatility của cửa sổ hiện tại khác reference window; PSI/KL/JS đo sự thay đổi này. Concept drift là quan hệ giữa feature và target thay đổi; chỉ quan sát được sau khi delayed label xuất hiện, nên dùng rolling MAE, Directional Accuracy và Page-Hinkley trên error stream. Data drift không luôn đồng nghĩa model đã giảm chất lượng; vì vậy retraining không nên trigger chỉ từ một metric duy nhất.

## 7. Threshold có ý nghĩa gì?

PSI warning `0.10` và critical `0.25` là giá trị khởi đầu để demo, cần calibration trên baseline history. Hệ thống thêm sample minimum, consecutive critical checks, hysteresis và cooldown để tránh false alarm/retraining loop. Hội đồng có thể hỏi “tại sao không retrain ngay?”; câu trả lời là retraining tốn tài nguyên và candidate mới có thể kém hơn champion, nên phải qua evaluation gate.

## 8. Model Registry và champion/candidate

Registry lưu version, metric, artifact path, data/feature/code metadata và audit. Candidate chưa được serving. Champion là version đã pass gate. Promote thay đổi alias; rollback trỏ alias về version approved trước đó. Cách này tách training thành công khỏi production deployment an toàn.

## 9. Metrics cần giải thích

MAE biểu diễn sai số tuyệt đối trung bình và dễ diễn giải theo đơn vị giá. RMSE phạt mạnh lỗi lớn. MAPE dễ bất ổn khi target gần 0 nên sMAPE thường được báo cáo bổ sung. Directional Accuracy đo đúng hướng tăng/giảm. Sharpe và strategy return chỉ là mô phỏng có transaction cost, không phải bằng chứng lợi nhuận tương lai.

## 10. Uncertainty

Khoảng bất định không nên được gọi đơn giản là “độ chính xác”. Chênh lệch TFT–LightGBM là disagreement-based uncertainty, phản ánh bất đồng giữa model. Quantile TFT có thể tạo P10/P50/P90; khi đó cần kiểm tra coverage, pinball loss và calibration. Confidence trên dashboard là tín hiệu hỗ trợ quyết định, không phải xác suất chắc chắn giá sẽ xảy ra.

## 11. Vì sao Hybrid Cloud?

Private/on-prem phù hợp training nặng, dữ liệu nhạy cảm và kiểm soát lineage. Public cloud phù hợp serving, object storage và scale inference. Artifact promotion đi qua registry/object storage và service identity, thay vì gửi dữ liệu nhạy cảm lên cloud một cách tùy ý. Trong đồ án, có thể trình bày Lightweight Hybrid nếu không đủ hạ tầng; Full K3s–EKS là phương án nâng cao.

## 12. Các câu hỏi phản biện và câu trả lời gợi ý

| Câu hỏi | Trả lời trọng tâm |
|---|---|
| Ensemble có luôn tốt hơn model đơn không? | Không. Đó là giả thuyết; phải so sánh bằng ablation cùng fold/horizon và giữ Ensemble chỉ khi qua gate. |
| Drift có thể phát hiện ngay không? | Data drift gần real-time; concept/performance drift cần delayed label. Vì vậy replay lịch sử được dùng để kiểm thử trong thời gian đồ án. |
| Vì sao không dùng accuracy? | Đây là regression; dùng MAE/RMSE/sMAPE và Directional Accuracy. |
| Có thể dùng cho giao dịch thật không? | Không nên tuyên bố. Trading simulation chỉ là evaluation phụ có chi phí, slippage và giới hạn; hệ thống không đặt lệnh. |
| Tại sao không online learning? | Online learning dễ leakage, khó rollback và khó đánh giá; batch retrain có candidate/champion an toàn hơn trong phạm vi đồ án. |
| Nếu model mới tệ hơn thì sao? | Candidate bị reject; champion vẫn phục vụ. Có audit và rollback. |
| Vì sao cần MLflow nếu đã có file model? | MLflow lưu experiment/metadata/lineage; registry và artifact version giúp tái lập, so sánh và promotion. |
| SQLite có đủ production không? | Đủ cho local/demo; production nên thay bằng PostgreSQL/object storage và có backup/HA. |

## 13. Những tuyên bố không nên nói

Không nói “model dự đoán chính xác giá”, “hệ thống đảm bảo lợi nhuận”, “drift detector chứng minh concept drift production sau vài tuần” hoặc “TFT là mô hình TFT nguyên bản đầy đủ mọi thành phần nghiên cứu”. Code hiện dùng một TFT skeleton mở rộng theo hướng nghiên cứu; báo cáo cần trung thực về giới hạn.
