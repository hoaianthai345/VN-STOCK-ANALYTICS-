# VN Advisor – Quantitative Bank Stock Analysis Platform

VN Advisor là một hệ thống phân tích cổ phiếu ngân hàng tại Việt Nam, được xây dựng theo hướng **data-driven** và **decision-support**, kết hợp giữa các mô hình học máy định lượng và tầng diễn giải bằng mô hình ngôn ngữ lớn (LLM).  
Mục tiêu của dự án không phải là dự đoán giá chính xác, mà là **ước lượng lợi suất kỳ vọng, rủi ro và trạng thái thị trường**, từ đó hỗ trợ nhà đầu tư ra quyết định một cách có kiểm soát.

* * *

## 1. Mục tiêu dự án

Dự án được thiết kế để giải quyết ba câu hỏi cốt lõi trong đầu tư cổ phiếu ngân hàng:

1. Trong ngắn hạn (≈ 21 ngày), cổ phiếu nào có **kỳ vọng lợi suất tương đối tốt hơn**?
    
2. Mức **rủi ro biến động** của cổ phiếu trong giai đoạn tới là bao nhiêu?
    
3. Thị trường hiện tại đang ở **regime** nào (Bull / Sideway / Bear), và điều đó ảnh hưởng ra sao đến quyết định đầu tư?
    

Hệ thống đóng vai trò **cung cấp tín hiệu định lượng** và **diễn giải có bối cảnh**, không thay thế nhà đầu tư hay thực hiện giao dịch tự động.

* * *

## 2. Kiến trúc tổng thể

Hệ thống được triển khai theo kiến trúc client–server, tách biệt rõ ràng giữa tầng tính toán và tầng hiển thị.

* **Backend**: FastAPI  
    Chịu trách nhiệm xử lý dữ liệu, huấn luyện và suy luận mô hình, cung cấp API cho frontend.
    
* **Frontend**: React  
    Hiển thị dashboard, explorer dữ liệu, AI Advisor và trạng thái mô hình.
    
* **Model layer**:  
    Các mô hình XGBoost huấn luyện theo chiến lược walk-forward trên dữ liệu time-series.
    
* **LLM layer**:  
    Nhận đầu vào là kết quả định lượng từ các mô hình và diễn giải thành nhận định dễ hiểu cho người dùng.
    

* * *

## 3. Các mô hình chính

### 3.1. Return Forecasting (Regression)

* **Mục tiêu**: Ước lượng log-return 21 ngày tiếp theo.
    
* **Mô hình**: XGBoost Regressor (cấu hình bảo thủ, depth nhỏ).
    
* **Đặc trưng sử dụng**:
    
    * Market & Technical
        
    * Sentiment (lagged)
        
    * Macro (lagged)
        
    * Bank fundamentals (quarterly)
        
* **Đánh giá**: Walk-forward theo năm (2015 → hiện tại).
    
* **Vai trò**: So sánh tương đối giữa các cổ phiếu, làm input cho AI Advisor.
    

* * *

### 3.2. Direction Classification

* **Mục tiêu**: Phân loại hướng đi của lợi suất (Up / Down) với ngưỡng trung lập.
    
* **Mô hình**: XGBoost Classifier.
    
* **Đánh giá**: Accuracy, ROC-AUC, Precision, Recall, F1 theo walk-forward.
    
* **Vai trò**: Bổ sung góc nhìn định hướng cho mô hình hồi quy.
    

* * *

### 3.3. Risk Model (Volatility Forecast)

* **Mục tiêu**: Dự báo độ biến động (volatility) trong 21 ngày tiếp theo.
    
* **Target**: Realized volatility tương lai.
    
* **Mô hình**: XGBoost Regressor.
    
* **Đặc trưng chính**: Volatility lịch sử, ATR, Bollinger width.
    
* **Kết quả**: Tương quan rất cao giữa dự báo và thực tế, phù hợp làm thước đo rủi ro.
    

* * *

### 3.4. Market Regime Classification

* **Mục tiêu**: Phân loại trạng thái thị trường thành Bear / Sideway / Bull.
    
* **Labeling**: Dựa trên lợi suất và volatility quá khứ (past-only, tránh look-ahead bias).
    
* **Mô hình**: XGBoost multi-class.
    
* **Vai trò**: Cung cấp bối cảnh thị trường cho AI Advisor và nhà đầu tư.
    

* * *

## 4. Chiến lược huấn luyện và đánh giá

Tất cả các mô hình đều được huấn luyện theo **walk-forward (expanding window)**:

* Train: từ 2015 → năm $t-1$
    
* Test: năm $t$
    

Chiến lược này giúp:

* Tránh look-ahead bias
    
* Phản ánh sát kịch bản đầu tư thực tế
    
* Đánh giá độ ổn định của mô hình qua nhiều giai đoạn thị trường
    

* * *

## 5. Tính năng ứng dụng

Ứng dụng cung cấp bốn nhóm chức năng chính:

### 5.1. Dashboard

Hiển thị tổng quan thị trường, các chỉ số chính, tín hiệu nổi bật và trạng thái hệ thống.

### 5.2. Stock Explorer

Cho phép người dùng xem chi tiết từng mã ngân hàng:

* Giá, lợi suất, volatility
    
* Các đặc trưng kỹ thuật và cơ bản
    
* So sánh cross-section giữa các ngân hàng
    

### 5.3. AI Advisor

Người dùng chọn một mã cổ phiếu, hệ thống sẽ:

* Tổng hợp kết quả từ các mô hình (return, risk, regime)
    
* Tính độ tin cậy dựa trên mức độ đồng thuận
    
* Diễn giải bằng ngôn ngữ tự nhiên (LLM), giải thích **vì sao** khuyến nghị được đưa ra
    

### 5.4. Model Monitoring

Hiển thị:

* Trạng thái huấn luyện
    
* Kết quả walk-forward
    
* Feature importance
    
* Phiên bản mô hình đang được sử dụng
    

* * *

## 6. Triết lý thiết kế

* Không tối ưu cho trading ngắn hạn hay timing chính xác
    
* Ưu tiên:
    
    * Tính ổn định
        
    * Khả năng giải thích
        
    * Phù hợp dữ liệu bảng tài chính
        
* Mô hình đóng vai trò **hỗ trợ quyết định**, không thay thế con người
    

* * *

## 7. Công nghệ sử dụng

* Python, Pandas, NumPy
    
* FastAPI
    
* XGBoost
    
* scikit-learn
    
* React
    
* LLM API (Groq / OpenAI compatible)
    

* * *

## 8. Trạng thái dự án

Dự án hiện ở mức **research prototype**, tập trung vào:

* Kiểm chứng khung mô hình
    
* Đánh giá tính hợp lý kinh tế
    
* Minh họa khả năng tích hợp ML + LLM trong đầu tư tài chính
    

* * *
