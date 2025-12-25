1. models/return_model/ (Dự báo lợi nhuận)

return_xgb_fullfit.joblib (hoặc ridge_fullfit.joblib nếu dùng Ridge)
feature_cols_used_fullfit.json (File chứa danh sách features)
2. models/risk_model/ (Dự báo rủi ro/biến động)

risk_model_xgb.pkl (Model dự báo volatility)
config.json (Chứa các tham số config và features)
3. models/regime_model/ (Phân loại xu hướng thị trường)

regime_xgb_model.joblib (Model phân loại Bull/Bear/Sideway)
config.json hoặc file chứa features tương ứng (nếu có riêng).
4. models/direction_model/ (Dự báo hướng tăng/giảm ngắn hạn)

direction_xgb_model.joblib (Model Binary Classification)
File chứa danh sách features (thường là json hoặc nằm trong config chung).
