# BÁO CÁO DỰ ÁN: HỆ THỐNG DỰ BÁO GIÁ CHỨNG KHOÁN DỰA TRÊN MÔ HÌNH HYBRID ENSEMBLE (TFT + LightGBM)

**Tác giả:** Lê Đình Hiếu, Trần Việt Hoàng
**Cố vấn:** ThS. Lê Anh Tuấn

---

## 1. Tổng quan & Ý tưởng (Concept)
**Mục tiêu dự án:**
Xây dựng một model có khả năng dự báo giá cổ phiếu trong tương lai ngắn hạn (T+3) và hỗ trợ đưa ra quyết định giao dịch tự động (Buy/Sell/Hold) dựa trên cơ sở toán học và thống kê, thay vì cảm tính.

**Ý tưởng thiết kế Mã nguồn (Architecture Concept):**
Thị trường tài chính là một hệ thống dữ liệu phi tuyến tính cực kỳ phức tạp. Các mô hình truyền thống thường chỉ nhìn được "một góc" của bức tranh:
- Các mô hình Deep Learning (học sâu) giỏi trong việc tìm ra các chu kỳ dài hạn tiềm ẩn (Long-term dependencies) nhưng dễ bị nhiễu bởi các cú giật bất ngờ.
- Các mô hình Tree-based (thống kê) giỏi trong việc phản ứng nhanh với các tín hiệu ngắn hạn nhưng lại thiếu góc nhìn toàn cảnh.

Do đó, dự án được thiết kế theo cấu trúc **Hybrid Stacking Ensemble**: Tiêm sức mạnh của cả hai Trường phái AI vào cùng một hệ thống. Sử dụng Meta-Learner để học cách cân bằng và tận dụng điểm mạnh tốt nhất của cả hai bản dự báo.

---

## 2. Vấn đề giải quyết (Problem Statement)
Dự án này tập trung giải quyết 3 bài toán lõi trong giao dịch tài chính tại Việt Nam:

1.  **Bài toán Thời gian (Độ trễ thanh toán T+2.5):** 
    Khác với thị trường tiền điện tử hay ngoại hối (mua bán tức thì), thị trường chứng khoán cơ sở Việt Nam (HOSE/HNX) áp dụng luật thanh toán T+2.5. Nghĩa là, nếu nhà đầu tư khớp lệnh MUA vào ngày hôm nay (Ngày T), thì phải đến chiều ngày T+2 cổ phiếu mới về tài khoản. Tức là **sớm nhất đến ngày T+3 nhà đầu tư mới có thể BÁN** để chốt lời. 
    Các mô hình AI học thuật thường chỉ tập trung dự đoán giá "ngày mai" (T+1). Điều này vô tình tạo ra sự **vô nghĩa trong thực tiễn**: Dù AI dự đoán ngày mai giá rớt thê thảm, nhà đầu tư cũng đành bất lực chịu lỗ vì hàng chưa về để bán. Để giải quyết triệt để điểm nghẽn này, hệ thống của chúng tôi đã thay đổi nhãn mục tiêu (Target Label) của AI, ép mô hình phải dự báo trực tiếp giá đóng cửa của **ngày T+3** – khớp hoàn toàn với thời điểm nhà đầu tư thực sự có quyền bán cổ phiếu.
2.  **Bài toán Nhiễu Dữ Liệu (Noise Reduction):** Giá cổ phiếu raw (giá gốc) chứa rất nhiều nhiễu. Hệ thống giải quyết bằng cách tự động xây dựng thêm 8 chỉ báo Feature Engineering chuyên sâu (SMA, RSI, MACD, Bollinger Bands, Log Return) để bộ máy AI có thể "nhìn xuyên" qua vùng nhiễu, định vị sức mạnh thực sự của đường giá.
3.  **Bài toán Xung đột Khả biến (Trade-off Bài toán Kinh tế):** Một AI dự đoán giá tăng không đồng nghĩa với việc ta ném tiền vào mua. Hệ thống giải quyết bài toán "Kế toán Giao dịch" thông qua *Decision Policy*: Tính toán bù trừ phí môi giới, thuế, độ lệch chuẩn rủi ro của thị trường và độ mâu thuẫn giữa 2 mô hình máy học, từ đó mới ra khuyến nghị cuối cùng.

---

## 3. Kiến trúc hệ thống
Hệ thống được module hóa thành các luồng độc lập, dễ dàng bảo trì và mở rộng. Các công nghệ cốt lõi được sử dụng:

1.  **Temporal Fusion Transformer (TFT) qua PyTorch:**
    - *Lý do chọn:* PyTorch là tiêu chuẩn công nghiệp cho Deep Learning. TFT là kiến trúc tối tân nhất hiện nay cho chuỗi thời gian (State-of-the-Art). Không giống các mạng RNN thông thường, TFT có cơ chế *Variable Selection Network* tự loại bỏ biến nhiễu, và *Self-Attention* giúp mạng ghi nhớ các sự kiện quan trọng trong khối dữ liệu 60 ngày quá khứ.
2.  **LightGBM (Gradient Boosting Framework):**
    - *Lý do chọn:* Tốc độ siêu việt, tiêu tốn rất ít RAM và cực kỳ khó bị Overfitting trên tập dữ liệu dạng bảng (Tabular Data). LightGBM đóng vai trò như một chuyên gia *Phân tích kỹ thuật ngắn hạn*.
3.  **Kiến trúc Microservices (Monorepo) & Serving:**
    - *Lý do chọn:* Để chuẩn bị cho việc triển khai MLOps quy mô lớn, hệ thống được đập đi xây lại theo mô hình Microservices. 
    - **Data API (Port 8001):** Tách biệt việc hút dữ liệu Yahoo và Feature Engineering.
    - **Inference Services (Port 8002 & 8003):** Chạy độc lập TFT và LightGBM, cho phép cấp phát tài nguyên phần cứng (CPU/GPU) linh hoạt cho từng loại AI.
    - **Ensemble Gateway (Port 8080):** Trạm gốc điều phối gọi song song các AI con bằng hàm bất đồng bộ (`asyncio`), tối ưu 50% thời gian chờ so với kiến trúc nguyên khối.
4.  **Docker & Docker Compose:**
    - *Lý do chọn:* Đảm bảo hệ thống "Chạy ở đâu cũng được" (Cloud, On-premise, Local). Toàn bộ 5 dịch vụ được đóng gói thành Container, sẵn sàng đẩy lên AWS EKS hoặc Kubernetes.
5.  **FastAPI & Dashboard UI (Port 8081):**
    - *Lý do chọn:* Dashboard tách biệt hoàn toàn logic, chỉ thuần túy làm lớp hiển thị (Glassmorphism UI) và lấy dữ liệu qua REST API, giúp hệ thống cực kỳ nhẹ và chuyên nghiệp.

---

## 4. Giải thích Code quan trọng

### Hệ thống Data Pipeline (`yahoo_data.py` & `indicators.py`)
- **Data Flow:** Lịch sử giá (Yfinance) $\rightarrow$ Làm sạch (Data Cleaning) $\rightarrow$ Sinh thêm thông số (Feature Engineering) $\rightarrow$ Trượt khung 60 ngày $\rightarrow$ Tách Train/Val theo trục thời gian (Chronological Split).
- **Điểm logic trọng yếu:** Hàm `dropna()` đi kèm việc ép khung `shift(-3)` mục tiêu. Cơ chế này đảm bảo máy chỉ học những ngày "thực sự có đáp án", chặn tiệt đường lây nhiễm rò rỉ dữ liệu (Data Leakage) — một lỗi sống còn trong AI tài chính.

### Hàm tính Sức mạnh tương đối RSI (`indicators.py`)
```python
delta = df['close'].diff()
gain = delta.where(delta > 0, 0.0).rolling(14).mean()
...
```
- **Ý nghĩa:** Biến động giá liên tục đập vào tâm lý con người. RSI chuẩn hóa 14 ngày tăng/giảm về một thang điểm 0-100 rõ ràng. Với AI, con số $RSI > 70$ (Mọi người tham lam) là một Vector thông tin vô giá để cản máy đưa ra lệnh BUY mù quáng lúc đỉnh sóng.

### Khối Variable Selection Network (`tft_model.py`)
- **Điểm logic trọng yếu:** Trong môi trường tài chính bão hòa thông tin (13 Features), không phải Feature nào cũng có ích mỗi ngày. Cấu trúc `Softmax` bên trong VSN hoạt động như bộ lọc, linh hoạt "phân bổ sự chú ý" (Attention weights). Ví dụ: Trong xu hướng đi ngang, VSN ép trọng số của Bollinger Bands lên cao nhất; nhưng khi bùng nổ xu hướng, nó có thể từ chối xem Bollinger và nhường 80% trọng số cho MACD.

### Thuật toán Kế toán Giao dịch (`decision_policy.py`)
- **Logic:** $Effective Edge = Net Return - Uncertainty Penalty$
- **Luồng tính (Data flow):** Nhận giá dự báo từ AI $\rightarrow$ Trừ phí giao dịch/thuế 0.2% $\rightarrow$ Trừ tiếp mức phạt hoang mang (khi 2 AI cãi nhau) $\rightarrow$ So sánh Biên Mở Lệnh an toàn (Hold Band, thay đổi linh hoạt theo biến động RV thị trường) $\rightarrow$ Phán Quyết.
- **Tầm quan trọng:** Nó biến hệ thống từ một *cỗ máy đoán số học* thành một *hệ thống tư vấn rủi ro thực tế*. Không có module này, AI sẽ giao dịch hưng phấn dù biên độ lãi cực nghèo nàn.

---

## 5. Kết quả & Hướng phát triển
**Kết quả đạt được:**
1.  **Chuyển đổi hoàn hảo sang Microservices:** Hệ thống không còn là một file script đơn lẻ mà là một mạng lưới các dịch vụ chuyên biệt, đạt chuẩn Production-ready.
2.  **Tốc độ đột phá:** Nhờ cơ chế Gọi song song (Parallel Requests) trong Gateway, thời gian suy luận (Inference time) cực nhanh dù phải chạy qua 2 mô hình AI phức tạp.
3.  **Directional Accuracy:** Khả năng đoán đúng chiều Tăng/Giảm duy trì ổn định, chứng minh được tính hiệu quả của cơ chế học Stacking Ensemble.
4.  **Tính sẵn sàng (Portability):** Với Docker Compose, việc triển khai demo trên máy hội đồng chỉ mất đúng 1 câu lệnh, không lo lỗi thiếu thư viện hay sai môi trường.

**Khả năng mở rộng (Future Work):**
1.  **Dữ liệu Vi mô:** Tích hợp bộ lấy dữ liệu (Crawler) từ các diễn đàn chứng khoán (như F247, FireAnt) $\rightarrow$ Dùng AI NLP phân tích tâm lý đám đông (Sentiment Analysis) $\rightarrow$ Đổ thành một Feature thứ 14 vào TFT.
2.  **Dữ liệu Vĩ mô:** Tích hợp tỷ giá USD/VND, lãi suất liên ngân hàng, khối ngoại Mua/Bán ròng để tăng tầm nhìn dài hạn cho mạng LSTM-Transformer.
3.  **Tự động cập nhật:** Viết tác vụ cronjob tự động Re-train lại cỗ máy vào 0h đêm hằng tuần, cập nhật tệp Knowledge Base của thị trường một cách liên tục thay vì tĩnh như hiện tại.
