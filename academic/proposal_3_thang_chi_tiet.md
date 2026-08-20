# PROPOSAL ĐỒ ÁN CHUYÊN NGÀNH

## THIẾT KẾ VÀ TRIỂN KHAI NỀN TẢNG MLOps CHO DỰ BÁO CHUỖI THỜI GIAN CHỨNG KHOÁN VỚI ENSEMBLE LIGHTGBM–TEMPORAL FUSION TRANSFORMER, GIÁM SÁT DRIFT VÀ RETRAINING CÓ KIỂM SOÁT TRÊN HYBRID CLOUD

### Tên đề tài thay thế

**Xây dựng hệ thống dự đoán giá chứng khoán dựa trên kiến trúc MLOps với mô hình Ensemble LightGBM–TFT, phát hiện Model Drift và nền tảng Web trên Hybrid Cloud.**

### Thời gian thực hiện

**12 tuần, tương đương 03 tháng.**

### Định hướng của đề tài

Đề tài tập trung xây dựng một hệ thống nghiên cứu và vận hành machine learning có khả năng tái lập, quan sát và cập nhật model có kiểm soát. Hệ thống không được định vị là hệ thống giao dịch tự động, không đưa ra khuyến nghị đầu tư chính thức và không cam kết lợi nhuận. Kết quả chính cần chứng minh là một quy trình từ dữ liệu đến model serving, monitoring, phát hiện drift, retraining candidate và deployment Web có thể chạy lại, kiểm thử và audit.

---

## TÓM TẮT ĐỀ TÀI

Dự đoán giá chứng khoán là một bài toán chuỗi thời gian có độ nhiễu cao, chịu ảnh hưởng bởi nhiều yếu tố và có thể thay đổi phân phối theo từng giai đoạn thị trường. Một mô hình đạt sai số thấp trên một lần chia dữ liệu chưa đủ để kết luận mô hình hoạt động tốt trong vận hành. Nếu dữ liệu, feature, model artifact, experiment và môi trường triển khai không được quản lý đồng bộ, hệ thống dễ gặp các vấn đề như data leakage, không tái lập được kết quả, model degradation, không truy vết được model đang phục vụ và retraining thiếu kiểm soát.

Đề tài đề xuất xây dựng một nền tảng MLOps end-to-end cho dự báo giá đóng cửa cổ phiếu. Hệ thống sử dụng **LightGBM** để khai thác các feature dạng bảng như technical indicators, return và volatility; sử dụng **Temporal Fusion Transformer (TFT)** để học các quan hệ theo chuỗi thời gian và hỗ trợ dự báo nhiều chân trời. TFT là kiến trúc attention-based cho multi-horizon forecasting, kết hợp recurrent layers, interpretable self-attention, variable selection và gating [1]. LightGBM là một hiện thực gradient boosting decision tree sử dụng các kỹ thuật GOSS và EFB nhằm cải thiện hiệu quả huấn luyện [2]. Hai mô hình được đánh giá độc lập và kết hợp thành Ensemble bằng equal-weight, validation-weighted average; stacking meta-learner được xem là phương án mở rộng.

Horizon chính của đề tài là **dự báo giá đóng cửa T+3**. Để tận dụng thời gian 03 tháng, hệ thống có thể mở rộng benchmark sang T+1, T+5 và T+10, nhưng T+3 vẫn là nhiệm vụ trung tâm để tránh làm loãng mục tiêu. Dữ liệu đầu vào bắt buộc gồm OHLCV và technical indicators. Trong giai đoạn mở rộng, nhóm có thể bổ sung một số market/macro features có timestamp rõ ràng, đồng thời kiểm soát nghiêm ngặt khả năng sử dụng nhầm dữ liệu tương lai.

Điểm đóng góp quan trọng của đề tài là lớp **Model Monitoring và Drift Management**. Hệ thống theo dõi ba nhóm thay đổi: data drift của feature đầu vào; prediction drift của output; và concept/performance drift thông qua rolling MAE, RMSE, Directional Accuracy khi ground truth xuất hiện. Các phương pháp như PSI, Jensen–Shannon/KL divergence, ADWIN hoặc Page-Hinkley được sử dụng theo vai trò phù hợp. Drift event được phân loại theo mức độ và không tự động ghi đè model production. Khi điều kiện policy đạt ngưỡng, hệ thống tạo candidate retraining run, đánh giá candidate so với champion bằng walk-forward validation và chỉ promote nếu candidate vượt qua evaluation gate.

Hệ thống được triển khai theo kiến trúc Hybrid Cloud. Môi trường on-premise hoặc private environment đảm nhiệm data processing, feature engineering và training; public cloud đảm nhiệm model serving, Web dashboard, artifact storage và monitoring endpoint. Nhóm triển khai phương án lightweight hybrid làm đường chính để bảo đảm khả năng hoàn thành; K3s–EKS/Kubernetes–GitOps là phương án nâng cao nếu hạ tầng đã có đủ độ ổn định.

Sản phẩm cuối cùng gồm data pipeline có versioning, model training pipeline, MLflow Tracking và Model Registry, prediction services, drift monitoring, retraining gate, Web dashboard có RBAC và audit log, CI/CD, deployment Hybrid Cloud, bộ thực nghiệm walk-forward, báo cáo đánh giá, runbook và kịch bản demo. Với thời lượng 03 tháng, đề tài có thể đạt mức **prototype production-like**, nhưng chưa nên tuyên bố là hệ thống giao dịch hoặc production system tài chính hoàn chỉnh.

> **Tuyên bố phạm vi:** Đề tài đánh giá năng lực dự báo và năng lực vận hành model. Kết quả dự báo và quyết định BUY/SELL/HOLD nếu có chỉ mang tính minh họa học thuật, không phải tư vấn đầu tư và không phải căn cứ giao dịch thực tế.

---

## 1. BỐI CẢNH VÀ LÝ DO CHỌN ĐỀ TÀI

### 1.1. Bối cảnh bài toán

Dữ liệu chứng khoán có ba đặc điểm khiến việc xây dựng hệ thống dự báo trở nên khó khăn. Thứ nhất, dữ liệu có thứ tự thời gian và không thể chia ngẫu nhiên như dữ liệu bảng thông thường. Thứ hai, dữ liệu có nhiễu, outlier và biến động theo regime. Thứ ba, quan hệ giữa feature và target có thể thay đổi theo thời gian, khiến model được huấn luyện ở một giai đoạn có thể suy giảm khi thị trường chuyển sang trạng thái khác.

Các bài toán dự đoán giá thường được trình bày dưới dạng notebook hoặc script huấn luyện đơn lẻ. Cách tiếp cận này hữu ích cho thử nghiệm ban đầu nhưng chưa giải quyết các câu hỏi vận hành: dataset nào đã được dùng để train; model version nào đang phục vụ; feature có thay đổi hay không; khi nào model bị drift; model mới có tốt hơn model cũ không; ai được phép retrain hoặc promote; và có thể rollback khi candidate gây regression hay không.

MLOps được đưa vào đề tài để giải quyết khoảng cách giữa nghiên cứu mô hình và vận hành hệ thống. Theo cách tiếp cận này, code, data, feature, experiment, artifact, model version, serving configuration và infrastructure đều phải có trạng thái có thể truy vết. Báo cáo hiện có của nhóm đã xây dựng nền tảng gồm LightGBM, TFT rút gọn, Ensemble API, MLflow, DVC, Kubeflow Pipelines, Docker, CI/CD, ArgoCD và Hybrid Cloud. Proposal mới kế thừa nền tảng đó, đồng thời tổ chức lại theo phạm vi 03 tháng và bổ sung các phần còn thiếu về monitoring, drift, retraining, explainability và đánh giá dài hạn.

### 1.2. Vấn đề tồn tại

| Vấn đề | Hệ quả | Hướng giải quyết trong đề tài |
|---|---|---|
| Chia dữ liệu hoặc preprocessing sai theo thời gian | Metric validation lạc quan giả tạo | Walk-forward split, train-only preprocessing, leakage tests |
| Model chỉ được train một lần | Không phát hiện model degradation | Prediction logging và performance monitoring |
| Feature phân phối thay đổi | Input không còn giống training distribution | PSI/JS/KL và feature drift dashboard |
| Quan hệ input–target thay đổi | Sai số tăng dù feature drift chưa rõ | Rolling error, ADWIN/Page-Hinkley, performance drift |
| Retrain thủ công và ghi đè model | Không rollback, khó audit | Candidate/champion registry và evaluation gate |
| TFT và LightGBM đánh giá không thống nhất | Không biết Ensemble có thực sự có ích | Cùng protocol, cùng folds, cùng holdout |
| Dashboard chỉ hiển thị prediction | Không quản lý được vòng đời model | Web platform có model, drift, run, retrain, role |
| Hạ tầng nhiều thành phần nhưng thiếu tiêu chí | Dễ tốn thời gian cho Kubernetes | MVP trước, Hybrid Cloud theo hai tầng |

### 1.3. Khoảng trống cần nghiên cứu và triển khai

Khoảng trống của đề tài không phải là phát minh một mô hình dự báo hoàn toàn mới. Đóng góp nằm ở việc kết nối một bài toán chuỗi thời gian với một vòng đời MLOps có khả năng quan sát và thích ứng. Cụ thể, đề tài cần trả lời liệu việc kết hợp một mô hình tabular nhanh với một mô hình sequence có giúp kết quả ổn định hơn hay không; liệu các metric drift có thể dùng để hỗ trợ phát hiện suy giảm hay không; và liệu candidate retraining có thể được kiểm soát bằng registry, evaluation gate và rollback hay không.

---

## 2. MỤC TIÊU ĐỀ TÀI

### 2.1. Mục tiêu tổng quát

Thiết kế, triển khai và đánh giá một nền tảng MLOps cho dự báo giá chứng khoán có khả năng quản lý dữ liệu và feature version, huấn luyện Ensemble LightGBM–TFT, phục vụ dự báo qua API/Web, theo dõi drift và chất lượng dự báo, tạo candidate retraining khi cần, đồng thời triển khai tách biệt training và serving trên Hybrid Cloud.

### 2.2. Mục tiêu cụ thể

| Mã | Mục tiêu | Kết quả kỳ vọng |
|---|---|---|
| G1 | Xây dựng data pipeline | OHLCV được validate, version, lưu snapshot và tạo feature không leakage |
| G2 | Xây dựng multi-horizon target | T+3 là target chính; T+1/T+5/T+10 dùng cho benchmark mở rộng |
| G3 | Huấn luyện model đơn | Có Naïve baseline, LightGBM và TFT |
| G4 | Xây dựng Ensemble | So sánh equal-weight, validation-weighted và stacking nếu đủ điều kiện |
| G5 | Đánh giá nghiêm ngặt | Walk-forward, holdout cuối, phân tích theo ticker và regime |
| G6 | Bổ sung uncertainty | Quantile TFT hoặc residual-based interval; đánh giá coverage/calibration |
| G7 | Quản lý experiment/model | MLflow Tracking, Registry, lineage, alias candidate/champion và rollback |
| G8 | Phát hiện drift | Data drift, prediction drift và concept/performance drift |
| G9 | Tự động hóa retraining | Drift event tạo candidate; candidate chỉ promote sau evaluation gate |
| G10 | Xây dựng Web platform | Prediction, model comparison, drift, registry, retrain, RBAC và audit |
| G11 | Triển khai Hybrid Cloud | Training ở private/on-premise; serving và storage ở public cloud |
| G12 | Đánh giá tính vận hành | CI/CD, observability, security cơ bản, backup, restore và runbook |

### 2.3. Mục tiêu không thuộc phạm vi cam kết

Đề tài không cam kết model có khả năng dự đoán đúng mọi biến động, không cam kết lợi nhuận, không triển khai đặt lệnh thật, không chứng minh khả năng thắng thị trường và không xem Sharpe của một backtest ngắn là bằng chứng đầu tư. Online learning, high availability đa vùng, multi-tenant IAM, canary production đầy đủ và sentiment pipeline quy mô lớn chỉ là hướng phát triển nếu còn thời gian.

---

## 3. CÂU HỎI NGHIÊN CỨU VÀ GIẢ THUYẾT

### 3.1. Câu hỏi nghiên cứu

**RQ1.** Ensemble LightGBM–TFT có cải thiện ổn định MAE, RMSE, sMAPE/MAPE và Directional Accuracy so với Naïve baseline, LightGBM đơn và TFT đơn trên nhiều ticker, horizon và regime hay không?

**RQ2.** Validation-weighted average có tốt hơn equal-weight khi trọng số được chọn bằng dữ liệu validation theo thời gian hay không?

**RQ3.** Quantile TFT có cung cấp khoảng dự báo hữu ích hơn point forecast trong việc mô tả bất định không?

**RQ4.** PSI hoặc JS/KL trên feature và prediction có xuất hiện trước khi rolling performance suy giảm không?

**RQ5.** Policy kết hợp drift, rolling performance, sample size và cooldown có giảm retrain giả so với chính sách retrain ngay sau mọi cảnh báo không?

**RQ6.** Model Registry với candidate/champion, evaluation gate và rollback có làm quá trình triển khai model mới an toàn và truy vết tốt hơn không?

**RQ7.** Kiến trúc Hybrid Cloud lightweight có đáp ứng được yêu cầu tách biệt training–serving, bảo mật artifact và vận hành Web trong phạm vi đồ án hay không?

### 3.2. Giả thuyết nghiên cứu

**H1:** Ensemble có thể cải thiện độ ổn định nếu sai số của LightGBM và TFT không hoàn toàn tương quan, nhưng không nhất thiết thắng trên mọi ticker hoặc mọi giai đoạn.

**H2:** Validation-weighted Ensemble có thể phù hợp hơn equal-weight khi performance của hai base model khác nhau đáng kể trong từng dataset.

**H3:** Quantile forecast giúp hệ thống cung cấp thông tin bất định hữu ích hơn một point forecast đơn lẻ, nhưng phải được đánh giá bằng pinball loss và coverage thay vì chỉ vẽ khoảng dự báo.

**H4:** Policy drift kết hợp data drift với performance drift và hysteresis sẽ giảm số lần trigger retraining không cần thiết.

**H5:** Candidate/champion gate giúp tránh việc một model mới có regression ghi đè model đang phục vụ.

---

## 4. ĐỐI TƯỢNG VÀ PHẠM VI NGHIÊN CỨU

### 4.1. Đối tượng nghiên cứu

Đối tượng nghiên cứu gồm dữ liệu chuỗi thời gian chứng khoán, technical indicators, feature theo cửa sổ trượt, mô hình gradient boosting, mô hình deep learning cho forecasting, chiến lược ensemble, uncertainty quantification, walk-forward validation, drift detection, model registry, model serving, monitoring và Hybrid Cloud.

### 4.2. Phạm vi dữ liệu

MVP sử dụng dữ liệu OHLCV theo ngày của 04 mã cổ phiếu có tính đại diện và có dữ liệu tương đối ổn định, chẳng hạn FPT, VNM, VCB và HPG. Danh sách chính thức phải được khóa ở tuần đầu tiên. Nếu nguồn dữ liệu không ổn định, nhóm phải lưu snapshot, checksum và thời điểm thu thập để việc đánh giá không phụ thuộc vào kết quả tải lại trong tương lai.

| Nhóm dữ liệu | Phạm vi bắt buộc | Phạm vi mở rộng |
|---|---|---|
| OHLCV | Open, High, Low, Close, Volume theo ngày | Adjusted price, corporate action metadata |
| Technical | Return, log-return, SMA/EMA, RSI, MACD, Bollinger, volatility | ATR, stochastic oscillator, volume indicators |
| Market | Index return, market volatility, sector proxy nếu có | Foreign flow, breadth, liquidity measures |
| Macro | Lãi suất, tỷ giá, index vĩ mô có timestamp | Commodity, bond yield, global risk indicators |
| News/sentiment | Không bắt buộc trong MVP | News sentiment có timestamp và quality check |

Dữ liệu vĩ mô và market features chỉ được thêm khi nguồn có timestamp, tần suất và quy tắc công bố rõ ràng. Nếu một biến chỉ được biết sau thời điểm dự báo, biến đó không được đưa vào feature tại thời điểm tương ứng. Việc thêm nhiều nguồn dữ liệu không được xem là cải tiến nếu không thể kiểm soát leakage và lineage.

### 4.3. Phạm vi target và horizon

Target chính là giá đóng cửa tại `t+3`, trong đó `t` là phiên cuối cùng mà hệ thống được phép quan sát. Để đánh giá khả năng multi-horizon của TFT, hệ thống có thể tạo thêm target T+1, T+5 và T+10. Các horizon mở rộng được dùng để so sánh và phân tích, không làm thay đổi việc T+3 là kết quả chính.

Nhóm có thể thử hai cách target:

| Cách biểu diễn | Công thức ý tưởng | Ưu điểm | Hạn chế |
|---|---|---|---|
| Giá tương lai | `y_t = close[t+h]` | Dễ hiểu, trực tiếp cho dashboard | Phụ thuộc scale và mức giá |
| Return tương lai | `y_t = close[t+h]/close[t] - 1` | So sánh giữa ticker dễ hơn | Cần quy đổi lại sang giá |

Một cách được chọn làm protocol chính sau thực nghiệm tuần đầu; cách còn lại chỉ giữ ở mức ablation nếu thời gian cho phép. Không nên đồng thời thay đổi target, feature, model và split trong cùng một thí nghiệm vì sẽ không xác định được yếu tố tạo ra cải thiện.

### 4.4. Giới hạn diễn giải

T+3 là một horizon nghiên cứu, không phải tuyên bố về quy định thanh toán hoặc khuyến nghị giao dịch. Mô phỏng BUY/SELL/HOLD nếu được giữ lại phải sử dụng transaction cost, hold band, uncertainty penalty và position constraint. Các metric như net return và Sharpe chỉ được báo cáo ở phần simulation, tách khỏi kết luận về độ chính xác dự báo.

---

## 5. CƠ SỞ LÝ THUYẾT

### 5.1. Chuỗi thời gian tài chính

Trong chuỗi thời gian, thứ tự quan sát mang thông tin và dữ liệu tương lai không được sử dụng khi tạo input cho thời điểm quá khứ. Một hệ thống đánh giá đúng phải tách train, validation và test theo timeline. Việc shuffle toàn bộ dữ liệu trước khi chia có thể làm các quan sát gần nhau của cùng một regime xuất hiện ở cả train và validation, từ đó làm metric không phản ánh tình huống vận hành.

Dữ liệu tài chính thường có heteroscedasticity, outlier và regime change. Một giai đoạn xu hướng tăng có thể có đặc trưng khác hẳn giai đoạn đi ngang hoặc giảm mạnh. Do đó, báo cáo cần đánh giá theo từng giai đoạn thay vì chỉ cung cấp một metric trung bình trên toàn bộ dữ liệu.

### 5.2. Feature engineering

Technical indicators được dùng để chuyển OHLCV thành các tín hiệu mô tả xu hướng, động lượng, biến động và thanh khoản. Các feature không được xem là thông tin độc lập hoặc bảo đảm có ý nghĩa dự báo. Mỗi feature phải có công thức, window, thời điểm khả dụng và phiên bản.

| Nhóm feature | Ví dụ | Diễn giải |
|---|---|---|
| Giá và tỷ lệ | close, high-low range, close/SMA | Trạng thái giá và biên độ |
| Return | return 1/3/5/10, log-return | Biến động tương đối |
| Trend | SMA10, SMA20, EMA12, EMA26 | Xu hướng ngắn/trung hạn |
| Momentum | RSI14, MACD, signal, histogram | Động lượng và đảo chiều |
| Volatility | rolling std, Bollinger width, ATR | Mức độ bất ổn |
| Volume | volume change, volume ratio | Thay đổi thanh khoản |
| Calendar | weekday, session index | Mẫu thời gian nếu có cơ sở |

### 5.3. LightGBM

LightGBM là nhánh tabular model, nhận vector feature tại thời điểm dự báo hoặc vector chứa các lag và rolling statistics. Các hyperparameter quan trọng gồm số lá, learning rate, số cây, min child samples, subsample và colsample. Trong 03 tháng, nhóm nên dùng Optuna với số trial giới hạn thay vì tìm kiếm quá lớn. Mỗi trial phải sử dụng time-series validation, không được random k-fold.

Bài báo LightGBM giới thiệu Gradient-based One-Side Sampling và Exclusive Feature Bundling nhằm nâng hiệu quả xử lý GBDT [2]. Trong đề tài, LightGBM có vai trò làm nhánh nhanh, dễ tái lập, dễ giải thích bằng SHAP và là đối chứng quan trọng cho TFT.

### 5.4. Temporal Fusion Transformer

TFT là kiến trúc attention-based cho multi-horizon forecasting. Kiến trúc gốc kết hợp recurrent layers cho quan hệ cục bộ, self-attention cho phụ thuộc dài hạn, variable selection để học vai trò feature và gating layers để loại bỏ thành phần không hữu ích [1].

Do giới hạn tài nguyên và phạm vi đồ án, nhóm triển khai TFT rút gọn gồm projection layer, sequence encoder, gated residual block, multi-head attention và output head. Input có dạng `[batch, window, features]`, với window đề xuất 30–60 phiên. Nếu đủ thời gian, output head dùng quantile loss cho các quantiles 0.1, 0.5 và 0.9. Nếu không, nhóm dùng point forecast và ước lượng interval bằng residual validation, đồng thời ghi rõ sự khác biệt.

### 5.5. Ensemble và stacking

Stacked generalization kết hợp nhiều learner thông qua một meta-learner [3]. Tuy nhiên, stacking dễ bị leakage nếu meta-learner học trên prediction in-sample. Vì vậy, MVP ưu tiên equal-weight và validation-weighted average. Stacking chỉ được triển khai khi nhóm tạo được prediction out-of-fold hoặc một validation layer tách biệt.

### 5.6. MLOps và technical debt

Hệ thống machine learning có technical debt không chỉ từ code mà còn từ phụ thuộc dữ liệu, feature, pipeline, artifact, configuration và môi trường [4]. Đề tài sử dụng MLOps để biến các phụ thuộc này thành artifact và metadata có thể truy vết. Mỗi model phải biết nó được train từ dataset nào, feature schema nào, code commit nào, config nào và được promote bằng điều kiện nào.

### 5.7. Drift

Data drift mô tả thay đổi phân phối của input; prediction drift mô tả thay đổi phân phối output; concept/performance drift được quan sát khi quan hệ input–target thay đổi, thường thể hiện qua sai số tăng. Không có một detector duy nhất phù hợp cho mọi loại drift. PSI/JS/KL phù hợp với so sánh phân phối theo cửa sổ; ADWIN hoặc Page-Hinkley phù hợp với chuỗi điểm số/lỗi theo thời gian khi có đủ quan sát.

---

## 6. THIẾT KẾ DATA PIPELINE

### 6.1. Data contract

Mỗi bản ghi tối thiểu có `timestamp`, `ticker`, `open`, `high`, `low`, `close`, `volume`. Pipeline phải kiểm tra schema, kiểu dữ liệu, timezone, tính tăng dần, duplicate, missing, giá trị âm, quan hệ High/Low và số dòng tối thiểu.

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `timestamp` | datetime | Không null, tăng dần theo ticker |
| `ticker` | string | Thuộc allow-list |
| `open/high/low/close` | float | Dương hoặc được xử lý theo policy |
| `volume` | float/int | Không âm |
| `data_version` | string | Bắt buộc trong manifest |
| `source_timestamp` | datetime | Ghi thời điểm dữ liệu được tải |

Pipeline phải fail fast khi dữ liệu không đạt contract. Không được mặc định `fillna(0)` cho các biến giá vì có thể tạo tín hiệu sai. Với missing ngắn, nhóm phải chọn rõ forward fill trong giới hạn, loại bỏ dòng hoặc thêm missing mask. Policy này phải áp dụng nhất quán giữa training và serving.

### 6.2. Các bước pipeline

```text
Source/snapshot
    -> normalize column names and timezone
    -> validate data contract
    -> sort by ticker and timestamp
    -> remove duplicates according to policy
    -> calculate historical-only features
    -> create target at horizon h
    -> drop rows without enough history/target
    -> generate schema + statistics + checksum
    -> save raw/processed version
    -> log dataset lineage
```

### 6.3. Versioning và lineage

Raw snapshot không nhất thiết commit trực tiếp vào Git. Nhóm dùng DVC hoặc manifest có checksum để liên kết Git commit với dataset file/object storage. Processed dataset phải có `schema_version`, `feature_version`, `target_version`, `source_version` và `created_at`. Dataset version phải được log vào MLflow ở mỗi training run.

DVC được đề xuất cho việc quản lý phiên bản dữ liệu lớn và liên kết metadata với repository [8]. Nếu triển khai Feast, nhóm phải tách offline feature generation và online feature retrieval, đồng thời kiểm tra rằng feature tại thời điểm inference có cùng định nghĩa với feature lúc training.

### 6.4. Chống data leakage

Checklist bắt buộc gồm: không shuffle time series; rolling feature chỉ sử dụng quá khứ; target được shift về tương lai; scaler fit riêng trên train của từng fold; threshold drift không tune trên test holdout; ensemble weight chỉ chọn trên validation; meta-learner chỉ dùng OOF prediction; macro/news feature phải có `available_at` không muộn hơn timestamp dự báo.

---

## 7. THIẾT KẾ MÔ HÌNH VÀ THÍ NGHIỆM

### 7.1. Baseline và ablation

Mọi thí nghiệm bắt đầu bằng Naïve baseline. Các cấu hình chính gồm:

| ID | Cấu hình | Mục đích |
|---|---|---|
| M0 | Last close hoặc zero-return | Baseline đơn giản |
| M1 | LightGBM | Đo hiệu quả tabular features |
| M2 | TFT point forecast | Đo hiệu quả sequence model |
| M3 | TFT quantile | Đo uncertainty và coverage |
| M4 | Equal-weight Ensemble | Kiểm tra kết hợp cơ bản |
| M5 | Validation-weighted Ensemble | Kiểm tra weighting có học |
| M6 | Stacking Linear/Ridge | Nâng cao, dùng OOF prediction |
| M7 | Ensemble có macro/market feature | Đánh giá đóng góp dữ liệu mở rộng |

Mỗi cấu hình phải ghi rõ dataset version, feature version, horizon, window, seed, training time, artifact size, metric và code commit. Không được chỉ lưu model file mà thiếu metadata.

### 7.2. LightGBM tuning

Optuna hoặc grid nhỏ dùng các tham số `num_leaves`, `learning_rate`, `n_estimators`, `min_child_samples`, `subsample` và `colsample_bytree`. Mỗi trial chạy trên cùng folds; optimization objective có thể là MAE hoặc RMSE, nhưng metric phụ vẫn phải báo cáo. Early stopping được bật trên validation. Tuning result phải được so sánh với default configuration để chứng minh tuning có giá trị.

### 7.3. TFT tuning

Các tham số cần kiểm soát gồm window size, hidden dimension, number of heads, dropout, learning rate, batch size và number of epochs. Nhóm dùng early stopping và giới hạn search space. Nếu tài nguyên hạn chế, ưu tiên ba thí nghiệm có lý do thay vì nhiều trial không phân tích. Quantile TFT phải báo cáo pinball loss, coverage và interval width, không chỉ MAE của median forecast.

### 7.4. Chiến lược Ensemble

MVP sử dụng:

```text
y_equal = 0.5 * y_lgbm + 0.5 * y_tft

y_weighted = w * y_lgbm + (1 - w) * y_tft
```

Trong đó `w` được chọn trên validation, giới hạn trong `[0,1]` và không được tối ưu trên test. Dynamic weighting chỉ dùng ở phần mở rộng, dựa trên performance rolling gần đây có smoothing và cooldown. Nếu hai model bất đồng lớn, hệ thống giảm confidence và ghi `model_disagreement_pct`; không biến sự bất đồng thành tín hiệu BUY/SELL mạnh hơn.

### 7.5. Multi-horizon

TFT có thể dự báo trực tiếp nhiều horizon trong cùng một output head hoặc dùng một model cho từng horizon. Phương án đầu tiên phản ánh tốt hơn mục tiêu multi-horizon nhưng phức tạp hơn. Trong 03 tháng, nhóm nên triển khai T+3 trước, sau đó mở rộng T+1/T+5/T+10 theo cùng pipeline. Báo cáo phải so sánh metric theo horizon, vì model tốt ở T+1 chưa chắc tốt ở T+10.

---

## 8. THIẾT KẾ ĐÁNH GIÁ VÀ BACKTESTING

### 8.1. Walk-forward validation

Đề xuất sử dụng expanding-window hoặc rolling-origin validation. Ở mỗi fold, train chỉ dùng quá khứ; validation nằm ngay sau train; test holdout cuối được khóa đến khi hoàn tất việc lựa chọn model. Tối thiểu có ba validation folds và một holdout cuối, tùy độ dài dữ liệu.

| Tập | Vai trò | Quyền sử dụng |
|---|---|---|
| Train | Fit preprocessing và model | Được học |
| Validation | Early stopping, chọn hyperparameter/weight | Được chọn |
| Test holdout | Đánh giá cuối cùng | Không được tune |
| Replay window | Mô phỏng inference/drift/retrain | Dùng đánh giá vận hành |

### 8.2. Metrics

| Metric | Vai trò | Ghi chú |
|---|---|---|
| MAE | Sai số tuyệt đối | Dễ diễn giải theo đơn vị giá |
| RMSE | Nhấn mạnh lỗi lớn | Nhạy với outlier |
| sMAPE | Sai số tỷ lệ ổn định hơn MAPE | Cần định nghĩa rõ epsilon |
| MAPE | Sai số tỷ lệ | Không dùng nếu mẫu gần 0 gây bất ổn |
| Directional Accuracy | Đúng hướng | Không đồng nghĩa với lợi nhuận |
| Pinball loss | Chất lượng quantile | Dùng cho TFT quantile |
| Coverage | Tỷ lệ target nằm trong interval | Đánh giá calibration |
| Interval width | Độ rộng khoảng | Khoảng quá rộng không hữu ích |
| Net return | Simulation sau cost | Chỉ minh họa |
| Sharpe | Risk-adjusted simulation | Không phải bằng chứng đầu tư |

Báo cáo phải có mean, median và độ phân tán theo folds, theo ticker, theo horizon và theo regime. Khi so sánh Ensemble với model đơn, nhóm cần báo cáo cả mức cải thiện tương đối và số fold mà Ensemble thực sự thắng.

### 8.3. Regime analysis

Regime được định nghĩa bằng quy tắc minh bạch, chẳng hạn dựa trên rolling return, volatility hoặc benchmark trend. Mục tiêu không phải tạo nhãn thị trường hoàn hảo mà là phân tích model hoạt động khác nhau thế nào trong giai đoạn tăng, giảm, đi ngang và biến động cao. Regime label không được dùng làm feature nếu không có sẵn tại thời điểm dự báo.

### 8.4. Simulation decision policy

Nếu hiển thị BUY/SELL/HOLD, hệ thống có thể tính:

```text
gross_return = (predicted_price - current_price) / current_price
net_return = gross_return - transaction_cost
uncertainty_penalty = disagreement + interval_risk
effective_edge = net_return - uncertainty_penalty
```

BUY chỉ khi `effective_edge` lớn hơn hold band; SELL chỉ khi nhỏ hơn âm hold band; còn lại HOLD. Decision policy phải tách khỏi model forecast để có thể đánh giá riêng. Không được sử dụng nhãn quyết định trong training target.

---

## 9. THIẾT KẾ DRIFT DETECTION VÀ MODEL MONITORING

### 9.1. Mục tiêu monitoring

Monitoring không chỉ kiểm tra service còn sống. Hệ thống phải trả lời được bốn câu hỏi: dữ liệu hiện tại có còn giống dữ liệu model đã học không; output model có thay đổi bất thường không; khi ground truth xuất hiện, sai số có suy giảm không; và model version nào đang tạo ra prediction. Vì vậy, mỗi prediction phải được log cùng ticker, timestamp, model version, dataset/feature version, input snapshot hoặc feature hash, output, latency, status và request id.

### 9.2. Các loại drift

| Loại | Định nghĩa vận hành | Thời điểm đo | Metric đề xuất |
|---|---|---|---|
| Data drift | Phân phối feature hiện tại khác reference | Ngay khi có feature | PSI, JS/KL, Wasserstein nếu cần |
| Prediction drift | Phân phối output hoặc return dự báo thay đổi | Sau inference | PSI, JS/KL, mean/variance shift |
| Concept/performance drift | Quan hệ input–target suy giảm | Sau khi có T+3 ground truth | Rolling MAE/RMSE/DA, ADWIN/Page-Hinkley |
| Service drift | Latency/error/resource thay đổi | Mỗi request/batch | p50/p95 latency, error rate, CPU/memory |

Evidently hỗ trợ so sánh reference và current data, drift ở cấp cột, prediction/target và tổng hợp dataset [6]. Trong đề tài, lớp này có thể dùng cho report hoặc custom implementation. Concept drift không thể đo tại thời điểm dự báo nếu target tương lai chưa xuất hiện; hệ thống phải có cơ chế delayed label để cập nhật performance sau T+3.

### 9.3. Reference và current window

Reference window là dữ liệu training hoặc cửa sổ production đã được đánh giá ổn định. Current window đề xuất 20–30 phiên gần nhất, tùy số lượng quan sát. Đối với prediction drift, reference có thể là prediction distribution của champion trong giai đoạn calibration. Reference phải được version hóa vì nếu thay đổi reference không kiểm soát, metric drift giữa các thời điểm không còn so sánh được.

Khi current window chưa đủ sample, hệ thống trả trạng thái `insufficient_sample` và không tạo alert critical. Ngưỡng phải được calibrate bằng reference-to-reference comparison: chia một giai đoạn ổn định thành nhiều cửa sổ, tính metric và chọn phân vị 95% hoặc threshold phù hợp với alert rate mục tiêu.

### 9.4. Metric và ngưỡng khởi đầu

| Đối tượng | Metric | Ngưỡng prototype | Cách hiệu chỉnh |
|---|---|---:|---|
| Feature numeric | PSI | `<0.10` ổn định; `0.10–0.25` cảnh báo; `>0.25` nghiêm trọng | Reference-to-reference và replay |
| Feature distribution | JS/KL | Theo phân vị calibration | Smoothing và cùng binning |
| Prediction | PSI/JS/KL | Theo prediction baseline | Calibration theo ticker/horizon |
| Performance | Rolling MAE/RMSE | Tăng ít nhất 20% so với champion | Cùng horizon và cùng window |
| Direction | Rolling DA | Giảm dưới ngưỡng baseline | Cần đủ sample |
| Error stream | ADWIN/Page-Hinkley | Theo alert rate cho phép | Historical replay |

Các giá trị PSI 0.10 và 0.25 chỉ là mức khởi đầu phục vụ prototype, không phải chuẩn đúng cho mọi thị trường. Proposal phải ghi rõ cách threshold được chọn và sensitivity analysis. Khi dùng KL, cần xử lý bin có xác suất 0 bằng smoothing; khi dùng JS, cần ghi rõ cách tính và log base.

### 9.5. Drift severity và alert policy

| Mức | Điều kiện minh họa | Hành động |
|---|---|---|
| INFO | Một feature drift nhẹ hoặc sample chưa đủ | Ghi log, hiển thị dashboard |
| WARNING | Nhiều feature quan trọng drift hoặc prediction drift | Alert cho analyst, chưa retrain |
| CRITICAL | Drift bền vững hoặc drift kèm performance degradation | Tạo retrain candidate |
| PROMOTED | Candidate pass evaluation gate | Chuyển alias champion, lưu audit |
| REJECTED | Candidate fail gate hoặc regression | Giữ champion, ghi lý do |

Policy cần có hysteresis và cooldown. Một feature vượt ngưỡng một lần không đủ để retrain. Đề xuất trigger khi một trong hai điều kiện xảy ra:

```text
Condition A:
    at least k critical features drift
    in two consecutive checks
    and sample size is sufficient

Condition B:
    rolling MAE increases >= 20%
    or Directional Accuracy falls below policy threshold
    in two consecutive windows
    and data/prediction drift or regime shift is present
```

Sau khi trigger, hệ thống khóa retrain cùng ticker/horizon trong một khoảng cooldown để tránh chạy lặp. Mỗi event có `event_id`, `ticker`, `model_version`, `metric`, `value`, `threshold`, `reference_window`, `current_window`, `severity`, `policy_version`, `created_at` và `action`.

### 9.6. Historical replay

Do 03 tháng không đủ để quan sát nhiều drift production, nhóm xây dựng replay runner. Replay đọc dữ liệu lịch sử theo thứ tự thời gian như một stream; tại mỗi mốc, hệ thống tạo prediction, cập nhật current window, delayed ground truth, drift metrics và policy state. Replay phải hỗ trợ các kịch bản:

| Kịch bản | Mục tiêu |
|---|---|
| Reference stable | Đo false alert rate |
| Regime tăng | Kiểm tra prediction/performance drift |
| Regime giảm | Kiểm tra khả năng cảnh báo suy giảm |
| Sideway kéo dài | Kiểm tra drift nhẹ và alert flapping |
| Volatility shock | Kiểm tra critical policy và retrain gate |
| Candidate regression | Kiểm tra reject và rollback |

Kết quả replay không được trình bày như dữ liệu live. Nó là bằng chứng kiểm thử logic monitor và retrain policy.

---

## 10. MODEL REGISTRY, RETRAINING VÀ PROMOTION GATE

### 10.1. Model Registry

MLflow Model Registry là nơi tập trung quản lý model lifecycle, cung cấp versioning, lineage, alias, tags và metadata [5]. Convention đề xuất như sau:

| Metadata | Nội dung |
|---|---|
| `model_name` | `stock-ensemble-{ticker}-{horizon}` |
| `version` | Số version tăng dần |
| `dataset_version` | Snapshot/hash dataset |
| `feature_schema_hash` | Hash của feature contract |
| `code_commit` | Git SHA |
| `training_window` | Khoảng thời gian train |
| `model_type` | LGBM/TFT/Ensemble |
| `metrics` | MAE, RMSE, DA, pinball/coverage nếu có |
| `drift_policy_version` | Version policy tạo retrain |
| `approval_status` | pending/approved/rejected |
| `alias` | candidate/champion/rollback |

Alias `champion` trỏ tới version đang phục vụ; `candidate` trỏ tới version đang đánh giá. Khi promote, thay alias thay vì hardcode đường dẫn model trong image. Cách này hỗ trợ rollback bằng cách trỏ champion về version trước.

### 10.2. Retraining modes

| Mode | Trigger | Mục đích |
|---|---|---|
| Scheduled retrain | Theo tuần hoặc theo chu kỳ | Cập nhật dữ liệu định kỳ |
| Drift-triggered | Policy critical | Phản ứng với thay đổi dữ liệu/performance |
| Manual retrain | Admin/analyst yêu cầu | Thí nghiệm có kiểm soát |
| Code-triggered | Feature/model code thay đổi | Bảo đảm artifact tương thích |

Scheduled retrain không được mặc định promote. Mọi mode đều tạo candidate, chạy validation và ghi run. Manual retrain phải có reason, requester và audit event.

### 10.3. Evaluation gate

Candidate được promote khi đạt các điều kiện:

| Gate | Điều kiện |
|---|---|
| Data gate | Data contract pass, không thiếu schema bắt buộc |
| Leakage gate | Time split, train-only preprocessing và future-safe feature pass |
| Metric gate | MAE/RMSE không kém champion quá margin cho phép |
| Direction gate | DA không giảm dưới ngưỡng policy |
| Uncertainty gate | Coverage và interval width đạt yêu cầu nếu có quantile |
| Stability gate | Không chỉ thắng một fold; không regression nghiêm trọng ở ticker/horizon khác |
| Serving gate | Signature, load time, latency và artifact compatibility pass |
| Security gate | Image/dependency scan không có lỗi critical chưa xử lý |

Nếu candidate không đạt, registry gắn `rejected`, lưu metric chênh lệch và giữ champion. Nếu đạt, candidate được promote sau approval phù hợp. Một candidate tốt hơn MAE nhưng kém nghiêm trọng về latency hoặc coverage vẫn có thể bị giữ lại để phân tích.

### 10.4. Rollback

Rollback phải là một thao tác registry/config có thể thực hiện nhanh, không cần train lại. Dashboard admin hiển thị champion hiện tại, version trước và lý do rollback. Mọi rollback ghi audit: user, timestamp, from_version, to_version, reason. Artifact của version cũ không được xóa ngay vì cần phục vụ audit và reproducibility.

---

## 11. KIẾN TRÚC HỆ THỐNG

### 11.1. Kiến trúc logic tổng thể

```text
+-------------------------------------------------------------------+
|                         WEB PLATFORM                             |
| Prediction | Model Comparison | Drift | Registry | Retraining  |
+-------------------------------+-----------------------------------+
                                |
                         API Gateway / Auth
                                |
       +------------------------+-------------------------+
       |                        |                         |
+------v------+         +-------v--------+        +-------v--------+
| Prediction  |         | Registry and   |        | Monitoring and |
| Services    |         | Artifact       |        | Alert Service  |
| LGBM/TFT/  |         | MLflow + S3    |        | Drift + Perf   |
| Ensemble   |         +----------------+        +----------------+
+------+------+                                           |
       |                                      +------------v----------+
       |                                      | Retrain Orchestrator  |
       |                                      | candidate + gate      |
       |                                      +------------+----------+
       |                                                   |
       +------------------- Prediction Logs ---------------+
                                                           |
                                      +--------------------v-------------------+
                                      | Private / On-prem Training Environment|
                                      | ingest -> feature -> train -> eval  |
                                      +--------------------+-------------------+
                                                           |
                                      +--------------------v-------------------+
                                      | Versioned Object Storage / Registry  |
                                      | raw, processed, models, reports      |
                                      +----------------------------------------+
```

### 11.2. Các service chính

| Service | Trách nhiệm | Endpoint mẫu |
|---|---|---|
| `data-service` | Đọc dữ liệu/snapshot và feature | `GET /data/{ticker}` |
| `feature-service` | Tạo hoặc truy xuất feature | `GET /features/{ticker}` |
| `lgbm-service` | Load LightGBM và infer | `POST /predict` |
| `tft-service` | Load TFT và infer | `POST /predict` |
| `ensemble-service` | Gọi model, blend, uncertainty, policy | `GET /predict/{ticker}` |
| `monitoring-service` | Drift, performance, alert | `GET /drift`, `GET /performance` |
| `training-service` | Tạo và theo dõi retrain job | `POST /retrain`, `GET /runs/{id}` |
| `registry-service` | Metadata và promote/rollback | `GET /models`, `POST /promote` |
| `dashboard-ui` | Web UI, role và audit view | Browser |

Với 03 tháng, nhóm có thể bắt đầu bằng modular monolith hoặc ít service hơn, sau đó tách các thành phần có ranh giới rõ. Không nên tạo microservice chỉ để tăng số lượng container. Ranh giới ưu tiên là inference, monitoring/retraining và UI/management.

### 11.3. Luồng prediction

```text
User selects ticker/horizon
       -> API auth and validation
       -> check cache and model alias
       -> load current feature window
       -> call LightGBM and TFT in parallel
       -> weighted ensemble
       -> uncertainty and disagreement
       -> decision policy (optional)
       -> write prediction log
       -> return forecast + metadata + interval
```

Response phải chứa ticker, horizon, current value, forecast, interval hoặc confidence, model version, feature version, generated_at, latency, drift status và disclaimer. Không trả về decision BUY/SELL/HOLD nếu thiếu current price, cost policy hoặc model health.

### 11.4. Luồng training

```text
trigger scheduled/manual/drift
       -> create run_id and freeze config
       -> resolve dataset and feature versions
       -> validate data
       -> generate folds
       -> train LGBM/TFT
       -> fit Ensemble
       -> evaluate
       -> log MLflow params/metrics/artifacts
       -> register candidate
       -> evaluation gate
       -> promote or reject
       -> notify and update dashboard
```

### 11.5. Luồng monitoring và delayed label

Prediction log được lưu ngay sau inference. Sau khi đủ T+3 phiên, một label updater tìm prediction tương ứng, gắn ground truth, tính error và cập nhật rolling metrics. Nếu prediction bị thiếu ground truth do dữ liệu lỗi, event phải mang trạng thái `label_pending` hoặc `label_unavailable`, không coi là model error.

---

## 12. NỀN TẢNG WEB

### 12.1. Mục tiêu Web platform

Web platform không chỉ là trang hiển thị giá dự đoán. Đây là lớp quản trị giúp người dùng quan sát model lifecycle và tác động có kiểm soát vào pipeline. Dashboard phải phân biệt rõ dữ liệu quan sát, kết quả dự đoán, trạng thái drift, trạng thái model và hành động retraining.

### 12.2. Các màn hình chính

| Màn hình | Chức năng bắt buộc | Dữ liệu hiển thị |
|---|---|---|
| Prediction Dashboard | Chọn ticker/horizon, xem forecast | Current value, T+3 forecast, interval, model version, timestamp |
| Model Comparison | So sánh model và version | MAE, RMSE, sMAPE, DA, fold, ticker, regime |
| Drift Monitoring | Theo dõi drift theo thời gian | PSI/JS/KL, rolling error, alert severity, threshold |
| Registry | Quản lý model version | Candidate/champion, lineage, artifact, approval status |
| Training Runs | Theo dõi experiment/retrain | Run id, params, metrics, status, logs |
| Retraining Control | Manual trigger và xem job | Reason, requester, policy, job status, gate result |
| User & Audit | Quản lý quyền và hành động | User, role, action, timestamp, before/after |
| System Health | Quan sát service | Latency, error rate, last data update, pipeline health |

### 12.3. Prediction Dashboard

Trang prediction hiển thị giá hiện tại, dự báo T+3, các horizon phụ nếu có, hướng thay đổi, prediction interval, confidence đã calibration hoặc residual-based, model version, feature version và thời điểm sinh kết quả. Nếu prediction được cache, phải hiển thị thời điểm cache và TTL để tránh người dùng nhầm kết quả mới.

Biểu đồ cần có actual versus predicted trên lịch sử holdout hoặc replay, không chỉ hiển thị một con số hiện tại. Khi ground truth T+3 đã xuất hiện, dashboard cho phép xem lỗi của prediction tương ứng.

### 12.4. Model Comparison và Explainability

Trang comparison cho phép chọn ticker, horizon, regime và model version. Các metric được hiển thị cùng số fold và khoảng phân tán. Không xếp hạng model chỉ bằng một metric tổng hợp nếu không có thông tin trade-off.

SHAP được dùng cho LightGBM để hiển thị feature contribution của một prediction hoặc importance tổng thể. Với TFT, nhóm có thể hiển thị variable selection weights, attention summary hoặc feature ablation. Cần ghi rõ attention/feature weight là công cụ hỗ trợ diễn giải, không phải bằng chứng nhân quả.

### 12.5. Drift Dashboard

Drift dashboard gồm bốn lớp:

1. Tổng quan severity theo ticker/horizon/model version.
2. Timeline của PSI/JS/KL theo feature.
3. Prediction drift và performance drift theo rolling window.
4. Danh sách event với nguyên nhân, threshold, action và retrain status.

Dashboard cần có filter reference version, current window, ticker, horizon và model. Người dùng phải phân biệt được `data drift detected`, `performance degradation detected`, `retrain pending`, `candidate rejected` và `champion promoted`.

### 12.6. Role-based access control

| Role | Quyền |
|---|---|
| Viewer | Xem prediction, metric, drift và model metadata |
| Analyst | Tạo manual retrain request, xem logs và candidate |
| Admin | Quản lý user, policy, promote, rollback, secrets/config reference |

MVP có thể dùng JWT hoặc token nội bộ. Password không lưu plaintext; token có expiration; endpoint retrain/promote/rollback phải kiểm tra role. Dashboard không được coi việc ẩn nút là cơ chế bảo mật; backend phải enforce permission.

### 12.7. Audit log và alert

Các hành động cần audit gồm manual retrain, threshold change, promote, rollback, user change, policy change và data source change. Mỗi audit event có actor, role, action, target, before, after, timestamp, request id và reason.

Alert MVP có thể bắt đầu bằng Web dashboard và email/webhook demo. Alert nên có deduplication, cooldown và link đến event. Nội dung phải nêu ticker, model version, metric, threshold, window, severity và action. Slack/Telegram chỉ là kênh delivery; logic severity và retraining nằm ở backend.

---

## 13. MLOps PIPELINE, CI/CD VÀ OPERATIONS

### 13.1. Pipeline stages

| Stage | Input | Output |
|---|---|---|
| Ingest | Nguồn OHLCV/macro | Raw snapshot |
| Validate | Raw snapshot | Contract report |
| Feature | Validated data | Feature dataset/registry |
| Split | Feature + target | Time folds |
| Train | Folds + config | LGBM/TFT artifacts |
| Ensemble | Base predictions | Ensemble artifact |
| Evaluate | Predictions + targets | Metric report |
| Track | Params/metrics/artifacts | MLflow run |
| Register | Candidate artifact | Model version |
| Gate | Candidate/champion | Promote/reject |
| Serve | Champion alias | Prediction API |
| Monitor | Logs/reference | Drift/performance event |
| Retrain | Event + config | New candidate |

Kubeflow Pipelines có thể dùng để chạy workflow containerized trên Kubernetes [9]. Tuy nhiên, nếu dựng KFP làm chậm MVP, training orchestrator có thể bắt đầu bằng GitHub Actions job, container job hoặc scheduled workflow; sau đó chuyển sang KFP ở tuần 9–12. Điều quan trọng là pipeline có step, input/output, version và log rõ ràng.

### 13.2. Experiment tracking

Mỗi MLflow run ghi params, metrics, artifact, tag và dataset metadata. Các artifact tối thiểu gồm model file, scaler, feature list, model signature, config, evaluation report, prediction file và confusion/error analysis nếu có. Run name nên bao gồm ticker/horizon/model/config; tags gồm `git_sha`, `data_version`, `feature_version`, `trigger_type` và `environment`.

### 13.3. CI/CD

CI chạy khi pull request hoặc push code. Các bước gồm formatting/lint, unit test, data contract test, leakage test, integration test, dependency scan, secret scan và build check. CD deploy staging sau khi image build và scan. Production chỉ được promote sau approval hoặc registry gate.

| Workflow | Trigger | Nội dung |
|---|---|---|
| `pr-gate` | Pull request | Lint, unit, leakage, security |
| `data-pipeline` | Schedule/manual | Ingest, validate, version data |
| `training-pipeline` | Data/model change | Train, evaluate, register candidate |
| `drift-monitor` | Schedule/event | Compute drift, create alerts |
| `retrain-pipeline` | Drift/manual | Candidate retrain và gate |
| `service-build` | Service change | Test, build, scan, push image |
| `deploy-staging` | Approved build | Deploy staging |
| `promote-production` | Manual/gate | Update champion/config |

### 13.4. Observability

Observability tối thiểu gồm request count, p50/p95 latency, error rate, timeout, model load failure, cache hit rate, last successful data update, training duration, pipeline failure, drift event count và current champion version. Có thể dùng Prometheus/Grafana hoặc custom metrics trong dashboard. Không nên triển khai Grafana trước khi schema metrics và event đã ổn định.

### 13.5. Reliability

API cần health check, readiness check, timeout, retry có giới hạn, circuit breaker đơn giản và graceful failure khi Redis/monitoring tạm thời không khả dụng. Prediction service không được trả về model version rỗng. Khi model artifact không tải được, service phải trả lỗi rõ ràng và không tự động dùng model ngẫu nhiên hoặc model cũ mà không ghi log.

---

## 14. HYBRID CLOUD VÀ HẠ TẦNG TRIỂN KHAI

### 14.1. Nguyên tắc phân tách

Training nặng và dữ liệu nội bộ đặt ở on-premise/private environment. Serving Web và API đặt ở public cloud để dễ truy cập và mở rộng. Artifact store là điểm giao tiếp có version và access control. MLflow có thể đặt ở private hoặc cloud tùy yêu cầu; nếu đặt cloud, không mở giao diện quản trị public trực tiếp.

### 14.2. Phương án A — Lightweight Hybrid, khuyến nghị

On-premise chạy Docker Compose hoặc K3s tối giản cho data pipeline, training và evaluation. Public cloud chạy một VM hoặc managed container service cho FastAPI, dashboard, monitoring và registry proxy. Object storage lưu raw/processed snapshot, model artifact và report. CI/CD build image, deploy staging và promote bằng tag/manifest.

| Thành phần | Vị trí | Vai trò |
|---|---|---|
| Data ingestion/feature | On-prem/private | Xử lý và kiểm soát dữ liệu |
| Training/tuning | On-prem/private | CPU/GPU và candidate run |
| MLflow/registry | Private hoặc cloud có access control | Tracking, version, alias |
| Object storage | Public cloud/private S3-compatible | Artifact và snapshot |
| Prediction API | Public cloud | Serving |
| Web dashboard | Public cloud | Người dùng truy cập |
| Monitoring | Public cloud hoặc shared | Drift và service metrics |

### 14.3. Phương án B — Full Hybrid Kubernetes

K3s on-premise đảm nhiệm KFP, self-hosted runner và training. EKS/GKE/AKS đảm nhiệm serving, MLflow, PostgreSQL, object storage integration, monitoring và ingress. Tailscale hoặc private network kết nối hai môi trường. Helm và ArgoCD quản lý desired state; Terraform tạo VPC, cluster và addon nếu cần.

Phương án B thể hiện tốt năng lực cloud-native nhưng có nhiều điểm lỗi: network, IAM, storage, ingress, certificate và version compatibility. Vì vậy, nhóm chỉ dùng full Kubernetes khi cluster đã có sẵn hoặc sau khi lightweight hybrid đã hoàn thành.

### 14.4. So sánh phương án

| Tiêu chí | Lightweight Hybrid | Full Kubernetes |
|---|---|---|
| Khả năng hoàn thành | Cao hơn | Thấp hơn nếu dựng từ đầu |
| Chi phí | Thấp–trung bình | Trung bình–cao |
| Autoscaling | Hạn chế | Tốt |
| GitOps | Có thể dùng tag/manifest | ArgoCD đầy đủ |
| Debug | Dễ hơn | Khó hơn |
| Giá trị demo MLOps | Đủ | Rất cao |
| Rủi ro ảnh hưởng model | Thấp hơn | Cao hơn |

### 14.5. Bảo mật

Security cơ bản gồm API authentication, RBAC, secret management, TLS, least privilege, network restriction, dependency scan, image scan, secret scan và audit log. Training job chỉ được quyền đọc dữ liệu cần thiết và ghi artifact vào prefix riêng. Serving chỉ có quyền đọc champion artifact. MLflow/PostgreSQL không public trực tiếp nếu không có lớp bảo vệ.

### 14.6. Backup và restore

Backup tối thiểu gồm model artifact, MLflow metadata, dataset manifest, registry metadata, deployment manifest và audit log. Restore drill phải được chạy ít nhất một lần trong tuần 10–11: khôi phục champion cũ, khởi động serving và kiểm tra prediction signature. Backup không được coi là hoàn thành chỉ vì đã có file; phải có bằng chứng restore.

---

## 15. CẤU TRÚC REPOSITORY ĐỀ XUẤT

```text
stock-mlops/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── manifests/
│   └── snapshots/
├── src/
│   ├── data_pipeline/
│   ├── features/
│   ├── models/
│   │   ├── lgbm/
│   │   ├── tft/
│   │   └── ensemble/
│   ├── evaluation/
│   ├── monitoring/
│   ├── retraining/
│   └── policies/
├── feature_store/
│   ├── definitions/
│   └── materialization/
├── services/
│   ├── data_api/
│   ├── prediction_api/
│   ├── monitoring_api/
│   ├── training_api/
│   └── dashboard_ui/
├── pipelines/
│   ├── data_pipeline.py
│   ├── training_pipeline.py
│   ├── drift_pipeline.py
│   ├── replay_pipeline.py
│   └── retrain_pipeline.py
├── configs/
│   ├── data.yaml
│   ├── features.yaml
│   ├── models.yaml
│   ├── drift.yaml
│   ├── security.yaml
│   └── deployment.yaml
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── leakage/
│   ├── integration/
│   └── replay/
├── infra/
│   ├── docker-compose.yml
│   ├── k8s/
│   ├── helm/
│   └── terraform/
├── .github/workflows/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── data_dictionary.md
│   ├── experiment_protocol.md
│   ├── drift_policy.md
│   └── runbook.md
├── README.md
└── CHANGELOG.md
```

---

## 16. KẾ HOẠCH THỰC HIỆN 12 TUẦN

### 16.1. Giai đoạn 1 — Xây dựng MVP tái lập, tuần 1–4

| Tuần | Mục tiêu | Công việc | Sản phẩm bàn giao |
|---:|---|---|---|
| 1 | Khóa bài toán và dữ liệu | Chốt ticker, target T+3, horizon phụ, data contract, source, snapshot, metric, repository convention | Scope document, data dictionary, raw snapshot, manifest |
| 2 | Data và baseline | Validate, feature engineering, target generation, Naïve, LightGBM baseline, leakage tests | Processed dataset, feature pipeline, baseline report |
| 3 | TFT và Ensemble | TFT point forecast, window tuning nhỏ, equal-weight, validation-weighted, MLflow logging | TFT/Ensemble artifacts, experiment runs |
| 4 | API và release MVP | FastAPI prediction, registry version, Docker Compose, dashboard prediction cơ bản, integration test | MVP release từ data đến prediction |

**Mốc nghiệm thu G1:** Có thể chạy lại từ snapshot và code; có Naïve/LightGBM/TFT/Ensemble; có metric cơ bản; API trả prediction kèm model version; MLflow lưu run.

### 16.2. Giai đoạn 2 — Nâng chất lượng nghiên cứu, tuần 5–8

| Tuần | Mục tiêu | Công việc | Sản phẩm bàn giao |
|---:|---|---|---|
| 5 | Multi-horizon | Tạo T+1/T+5/T+10, thống nhất evaluator, so sánh direct/multi-output nếu khả thi | Multi-horizon dataset và report |
| 6 | Uncertainty | Quantile TFT, pinball loss, coverage, interval width; residual interval fallback | Quantile artifact và calibration report |
| 7 | Tuning và regime | Optuna giới hạn cho LGBM/TFT, expanding-window, regime labeling và error analysis | Tuning matrix, regime report |
| 8 | Data/feature mở rộng | Thêm market/macro features có timestamp; Feature Registry hoặc Feast tối giản; SHAP/attention summary | Feature lineage, explainability screens |

**Mốc nghiệm thu G2:** Có benchmark theo ticker, horizon và regime; có ít nhất một phương án uncertainty được đánh giá; tuning có protocol; feature mở rộng không gây leakage; explainability có bằng chứng.

### 16.3. Giai đoạn 3 — Production-like operations, tuần 9–12

| Tuần | Mục tiêu | Công việc | Sản phẩm bàn giao |
|---:|---|---|---|
| 9 | Prediction logging và drift | Log feature/prediction/version, delayed label updater, PSI/JS/KL, rolling performance | Monitoring data model và drift service |
| 10 | Historical replay và retraining | Replay theo regime, ADWIN/Page-Hinkley, threshold calibration, severity/cooldown, candidate retrain | Replay report, drift policy, candidate runs |
| 11 | Web quản trị và reliability | RBAC, audit, registry UI, manual retrain, promote/reject/rollback, alert, backup/restore | Web management release, restore evidence |
| 12 | Hybrid Cloud và final | Deploy serving/public cloud, training/private, CI/CD, observability, security scan, demo, report | Final release, architecture evidence, report, video/demo |

**Mốc nghiệm thu G3:** Hệ thống có thể mô phỏng drift, tạo candidate, reject/promote đúng policy, rollback được, có Web/RBAC/audit, có deployment hybrid và runbook.

### 16.4. Lịch kiểm tra hàng tuần

| Thời điểm | Hoạt động |
|---|---|
| Đầu tuần | Chốt mục tiêu, task, risk và tiêu chí tuần |
| Giữa tuần | Integration checkpoint, phát hiện blocker, cắt giảm sớm nếu cần |
| Cuối tuần | Demo vertical slice, lưu evidence, cập nhật changelog và report |
| Cuối mỗi giai đoạn | Release tag, freeze artifact, review chéo và nghiệm thu gate |

### 16.5. Phân công cho nhóm 02 người

| Vai trò | Trách nhiệm chính | Sản phẩm chủ trì |
|---|---|---|
| Thành viên A — ML/Data/MLOps | Data contract, feature, target, LGBM, TFT, Ensemble, evaluation, tuning, drift/retrain logic, MLflow | Dataset, model, experiment, drift service, evaluation report |
| Thành viên B — Platform/Web/Cloud | FastAPI, registry integration, dashboard, RBAC, audit, Docker, CI/CD, monitoring, deployment, backup | API, UI, infrastructure, workflows, runbook |
| Cả hai | Leakage review, protocol, integration test, replay, report, demo và bảo vệ | Release, evidence, final report |

Quy tắc review chéo: mọi thay đổi target, split, preprocessing, metric, drift threshold, promotion gate hoặc security policy phải được thành viên còn lại review. Không được để một người vừa thay đổi protocol vừa tự xác nhận kết quả cuối.

---

## 17. TIÊU CHÍ NGHIỆM THU

### 17.1. Nghiệm thu dữ liệu và reproducibility

| ID | Tiêu chí | Bằng chứng |
|---|---|---|
| D01 | Dữ liệu có source, timestamp, snapshot/hash | Manifest và raw snapshot |
| D02 | Data contract có pass/fail rõ | Contract report |
| D03 | Feature có công thức, window, version | Data dictionary và test |
| D04 | Target/horizon được định nghĩa nhất quán | Config và schema |
| D05 | Pipeline chạy lại từ môi trường sạch | Re-run log |

### 17.2. Nghiệm thu mô hình và đánh giá

| ID | Tiêu chí | Bằng chứng |
|---|---|---|
| M01 | Có Naïve, LightGBM, TFT và Ensemble | Model artifacts |
| M02 | Có walk-forward/rolling-origin validation | Evaluation script/report |
| M03 | Có holdout cuối không dùng để tune | Split manifest |
| M04 | Có metric MAE, RMSE, sMAPE/MAPE, DA | Bảng kết quả |
| M05 | Có phân tích theo ticker/horizon/regime | Charts và report |
| M06 | Quantile/interval được đánh giá nếu triển khai | Pinball/coverage report |
| M07 | Không có leakage trong test bắt buộc | Test output và review |

### 17.3. Nghiệm thu MLOps và registry

| ID | Tiêu chí | Bằng chứng |
|---|---|---|
| O01 | MLflow run có params/metrics/artifacts | MLflow UI/API |
| O02 | Model version có lineage và dataset hash | Registry metadata |
| O03 | Có alias candidate/champion | Registry screenshot/API |
| O04 | Có evaluation gate | Gate log |
| O05 | Candidate reject không thay champion | Negative test |
| O06 | Rollback về version trước được | Rollback evidence |
| O07 | CI/CD có test/build/scan/deploy | Workflow run |

### 17.4. Nghiệm thu drift và retraining

| ID | Tiêu chí | Bằng chứng |
|---|---|---|
| R01 | Có feature data drift | PSI/JS/KL report |
| R02 | Có prediction drift | Prediction distribution report |
| R03 | Có delayed-label performance drift | Rolling MAE/RMSE/DA |
| R04 | Có ADWIN/Page-Hinkley hoặc detector tương đương | Replay log |
| R05 | Có sample minimum, hysteresis và cooldown | Policy test |
| R06 | Có alert-only scenario | Replay scenario A |
| R07 | Có critical retrain scenario | Replay scenario B |
| R08 | Có candidate promotion/rejection | Registry history |
| R09 | Có historical replay | Replay report |

### 17.5. Nghiệm thu Web, cloud và security

| ID | Tiêu chí | Bằng chứng |
|---|---|---|
| W01 | Prediction dashboard hoạt động | Screenshot/video |
| W02 | Model comparison và drift chart hoạt động | UI evidence |
| W03 | Manual retrain có quyền và audit | API/UI test |
| W04 | Viewer không promote/rollback | RBAC negative test |
| W05 | Training và serving tách môi trường | Architecture/deployment log |
| W06 | Artifact đọc theo version/alias | Serving log |
| W07 | Health, latency, error metrics có theo dõi | Metrics dashboard |
| W08 | Secret không commit, image/dependency scan | CI report |
| W09 | Backup và restore được kiểm thử | Restore evidence |

### 17.6. Definition of Done

Một user story chỉ hoàn thành khi code đã được review, có test, có log/screenshot chứng minh, được ghi trong README hoặc runbook và chạy lại được từ môi trường sạch. Các phần chưa đáp ứng phải ghi rõ `deferred` trong báo cáo. Không đánh giá mức độ hoàn thành bằng số lượng file, container hoặc workflow.

---

## 18. RỦI RO VÀ PHƯƠNG ÁN GIẢM THIỂU

| Rủi ro | Mức ảnh hưởng | Phương án giảm thiểu |
|---|---|---|
| Dữ liệu nguồn thay đổi hoặc không tải được | Cao | Snapshot, cache, checksum, fallback file và contract |
| TFT thiếu GPU/chạy quá chậm | Cao | TFT rút gọn, window nhỏ, early stopping, giới hạn trial |
| Overfitting do dataset nhỏ | Cao | Walk-forward, regularization, đơn giản hóa model, báo cáo variance |
| Data leakage | Rất cao | Checklist, unit test, review chéo, holdout bất biến |
| PSI false positive | Trung bình | Sample minimum, calibration, hysteresis, replay |
| Concept drift không đủ label | Cao | Delayed label updater và historical replay |
| Ensemble không tốt hơn model đơn | Trung bình | Không ép kết luận; giữ ablation và phân tích sai số |
| Macro/news gây leakage | Cao | `available_at`, snapshot timestamp, bỏ feature nếu không kiểm soát |
| Full Kubernetes chiếm thời gian | Cao | Lightweight hybrid là đường chính; K8s là stretch |
| Candidate model regression | Cao | Champion/candidate, gate, rollback |
| Dashboard mở rộng quá mức | Trung bình | Khóa 6 màn hình chính, ưu tiên API/evidence |
| Cloud phát sinh chi phí | Trung bình | Resource limit, auto-shutdown, lightweight VM/container |
| Security cấu hình sai | Cao | Least privilege, scan, secret management, không public MLflow |
| Thành viên phụ thuộc lẫn nhau | Trung bình | Contract API sớm, stub/mock, review hàng tuần |

### 18.1. Quy tắc cắt giảm phạm vi

Nếu hết tuần 2 chưa có baseline và data pipeline, bỏ macro/news và Feast khỏi MVP. Nếu hết tuần 4 chưa có TFT ổn định, nghiệm thu TFT rút gọn point forecast và chuyển quantile thành stretch. Nếu hết tuần 6 chưa có walk-forward, dừng tuning và ưu tiên đánh giá. Nếu hết tuần 8 chưa có feature store, dùng feature registry nội bộ có schema/version. Nếu hết tuần 10 chưa có historical replay, bỏ canary/A-B và tập trung vào drift/retrain gate. Không được cắt leakage tests, baseline, model comparison, registry, drift logic hoặc rollback evidence.

---

## 19. SẢN PHẨM BÀN GIAO

### 19.1. Sản phẩm kỹ thuật

| Sản phẩm | Mô tả |
|---|---|
| Source code | Data, feature, model, service, monitoring, training |
| Dataset manifest | Source, snapshot, checksum, schema, version |
| Model artifacts | LGBM, TFT, Ensemble, scaler, signature |
| MLflow workspace | Runs, params, metrics, artifacts, registry |
| Feature Registry/Feast | Feature definition và lineage nếu triển khai |
| API services | Prediction, model, drift, retrain, health |
| Web dashboard | Prediction, comparison, drift, registry, retrain, RBAC |
| Pipelines | Data, training, drift, replay, retraining |
| Infrastructure | Docker Compose hoặc K8s/Helm/Terraform |
| CI/CD | Test, build, scan, staging, promotion |
| Monitoring | Drift/performance/service metrics, alert events |
| Runbook | Operate, retrain, promote, rollback, restore |

### 19.2. Sản phẩm học thuật

Báo cáo gồm tổng quan, cơ sở lý thuyết, phân tích yêu cầu, kiến trúc, thiết kế dữ liệu, thiết kế model, phương pháp đánh giá, Drift policy, MLOps pipeline, Web/Cloud deployment, kết quả thực nghiệm, bàn luận, hạn chế, kết luận và hướng phát triển.

Phụ lục gồm data dictionary, API schema, config mẫu, bảng hyperparameter, split manifest, MLflow screenshots, drift replay logs, test report, deployment diagram, threat model cơ bản và demo script.

### 19.3. Kịch bản demo cuối

Người dùng đăng nhập với role analyst, chọn FPT và horizon T+3, xem forecast P50 hoặc point forecast, interval, model version và timestamp. Người dùng mở Model Comparison để xem Naïve, LightGBM, TFT và Ensemble trên cùng protocol. Sau đó mở Drift Dashboard, xem historical replay tạo WARNING và CRITICAL event. Với CRITICAL event, analyst tạo retrain request; pipeline chạy candidate, log MLflow, evaluation gate reject hoặc promote. Nếu promote, alias champion thay đổi; nếu candidate fail, champion giữ nguyên. Admin thực hiện rollback thử nghiệm; audit log ghi actor, version và reason. Cuối cùng, nhóm trình bày đường đi training private environment đến serving public cloud.

---

## 20. KẾT QUẢ KỲ VỌNG VÀ ĐÓNG GÓP

### 20.1. Kết quả kỳ vọng

Kết quả kỳ vọng thứ nhất là một benchmark có protocol rõ ràng, cho biết LightGBM, TFT và Ensemble hoạt động thế nào theo ticker, horizon và regime. Kết quả kỳ vọng thứ hai là một pipeline MLOps có versioning, registry, serving và CI/CD. Kết quả thứ ba là một Drift Management loop được kiểm thử bằng historical replay, có alert, candidate retraining, evaluation gate và rollback. Kết quả thứ tư là Web platform cho phép theo dõi prediction và tác động có kiểm soát lên vòng đời model. Kết quả thứ năm là deployment Hybrid Cloud tách training và serving, kèm bằng chứng bảo mật và reproducibility ở mức prototype.

### 20.2. Đóng góp kỹ thuật

Đề tài đóng góp một kiến trúc tích hợp giữa tabular model, sequence model và MLOps lifecycle; một protocol đánh giá không leakage cho forecasting; một policy kết hợp data drift và performance drift; một retraining gate dựa trên candidate/champion; và một nền tảng Web quản trị model lifecycle. Đóng góp không phải là một claim rằng Ensemble luôn tốt nhất, mà là phương pháp kiểm chứng và vận hành model trong điều kiện dữ liệu thay đổi.

### 20.3. Đóng góp học thuật

Đề tài giúp minh họa cách chuyển một bài toán dự báo tài chính từ mức notebook sang hệ thống có thể tái lập và quan sát. Báo cáo cũng làm rõ sự khác nhau giữa model accuracy, prediction uncertainty, data drift, concept drift và service observability; đồng thời chỉ ra giới hạn của việc suy luận từ backtest ngắn sang khả năng giao dịch thực tế.

---

## 21. KẾT LUẬN

Trong thời lượng 03 tháng, đề tài có thể được xây dựng ở mức sâu hơn đáng kể so với prototype 01 tháng, nhưng chỉ khả thi nếu nhóm khóa rõ MVP và không để hạ tầng che khuất phần nghiên cứu. Phần bắt buộc nên gồm T+3, Naïve/LightGBM/TFT/Ensemble, walk-forward validation, MLflow Registry, drift/performance monitoring, historical replay, candidate/champion retraining gate, Web có RBAC/audit, CI/CD, backup/rollback và lightweight Hybrid Cloud. Multi-horizon, quantile forecast, tuning, macro features, feature registry và explainability là các phần nên triển khai trong tháng thứ hai. Full Kubernetes, canary, sentiment và online learning chỉ nên triển khai sau khi các tiêu chí cốt lõi đã đạt.

Đề tài chỉ nên tuyên bố rằng hệ thống **có khả năng dự báo, theo dõi chất lượng, phát hiện thay đổi và cập nhật model có kiểm soát**. Không nên tuyên bố hệ thống có thể dự đoán chính xác tuyệt đối, tạo lợi nhuận ổn định hoặc sẵn sàng cho giao dịch thật. Cách định vị này vừa trung thực về mặt khoa học, vừa phù hợp với đóng góp MLOps và khả năng nghiệm thu trong 12 tuần.

---

## TÀI LIỆU THAM KHẢO

[1]: https://research.google/pubs/temporal-fusion-transformers-for-interpretable-multi-horizon-time-series-forecasting/ "Google Research — Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting"

[2]: https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree "NeurIPS — LightGBM: A Highly Efficient Gradient Boosting Decision Tree"

[3]: https://papers.nips.cc/paper/1992/stacked-generalization "NeurIPS — Stacked Generalization"

[4]: https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems "NeurIPS — Hidden Technical Debt in Machine Learning Systems"

[5]: https://mlflow.org/docs/latest/ml/model-registry/ "MLflow Documentation — Model Registry"

[6]: https://docs.evidentlyai.com/metrics/preset_data_drift "Evidently Documentation — Data Drift"

[7]: https://riverml.xyz/dev/api/drift/ADWIN/ "River Documentation — ADWIN"

[8]: https://dvc.org/doc "DVC Documentation — Data Version Control"

[9]: https://www.kubeflow.org/docs/components/pipelines/ "Kubeflow Documentation — Kubeflow Pipelines"

[10]: https://argo-cd.readthedocs.io/ "Argo CD Documentation — Declarative GitOps CD for Kubernetes"

[11]: https://fastapi.tiangolo.com/ "FastAPI Documentation"

[12]: https://docs.docker.com/compose/ "Docker Documentation — Docker Compose"

[13]: https://feast.dev/ "Feast Documentation — Feature Store"

[14]: https://optuna.readthedocs.io/ "Optuna Documentation — Hyperparameter Optimization Framework"
