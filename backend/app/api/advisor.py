from fastapi import APIRouter, HTTPException, Body
import os
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
# from groq import Groq # Uncomment when installed

router = APIRouter()

from typing import Optional

class AdvisorRequest(BaseModel):
    symbol: str
    signals: Optional[dict] = {}

class AdvisorResponse(BaseModel):
    symbol: str
    recommendation: str
    rationale: str
    confidence: float
    signals: dict

from pipeline.inference import run_inference

@router.post("/consult", response_model=AdvisorResponse)
def consult_advisor(request: AdvisorRequest = Body(...)):
    """
    Get investment advice based on real-time model inference.
    """
    # 1. Run Inference to get latest signals
    try:
        inference_result = run_inference(request.symbol)
    except Exception as e:
        print(f"Inference failed: {e}")
        inference_result = None
        
    if not inference_result:
        return jsonable_encoder({
            "symbol": request.symbol,
            "recommendation": "NEUTRAL",
            "rationale": "Không đủ dữ liệu để tạo tín hiệu.",
            "confidence": 0.0,
            "signals": {}
        })
    
    signals = inference_result.get("signals", {})
    rec = inference_result.get("recommendation", "HOLD")
    
    # Extract confidence (using direction probability as proxy)
    # signals['predicted_direction_prob'] comes from inference.py
    # If direction is "Up", prob is prob(1). If "Down", prob is prob(0) = 1 - prob(1)?
    # actually inference.py returns 'pred_direction_prob' (prob of class 1).
    # If pred=1 (Up), conf = prob. If pred=0 (Down), conf = 1 - prob.
    
    raw_prob = signals.get("pred_direction_prob", 0.5)
    direction = signals.get("direction", "Unknown")
    
    if direction == "Up":
        confidence = raw_prob
    elif direction == "Down":
        confidence = 1.0 - raw_prob
    else:
        confidence = 0.5 # Neutral/Unknown
        
    # Scale to 0-100 for easy UI if needed, but float 0-1 is standard
    # Let's keep 0-1 float
    
    # 2. Generate Rationale (Mock or Groq) in Vietnamese
    # Construct a descriptive string
    rationale = (
        f"Dựa trên dữ liệu mới nhất (Ngày: {inference_result.get('date')}), hệ thống ghi nhận các tín hiệu sau:\n"
        f"- Lợi nhuận dự báo (21 ngày): {signals.get('predicted_return_21d', 0):.2%}\n"
        f"- Rủi ro biến động: {signals.get('predicted_volatility_21d', 0):.2%}\n"
        f"- Chế độ thị trường: {signals.get('regime')}\n"
        f"- Xu hướng giá: {signals.get('direction')} (Độ tin cậy: {confidence:.0%})\n\n"
        f"Kết luận: Hệ thống khuyến nghị {rec}."
    )
    
    # Optional: Enhance with Groq if API Key exists
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
             from groq import Groq
             client = Groq(api_key=api_key)
             
             prompt = (
                 f"Đóng vai trò là một chuyên gia tư vấn tài chính chuyên nghiệp. Hãy phân tích cổ phiếu {request.symbol} dựa trên các tín hiệu sau (Ngày: {inference_result.get('date')}):\n"
                 f"1. Dự báo Lợi nhuận (21 ngày): {signals.get('predicted_return_21d', 0):.2%}\n"
                 f"2. Rủi ro biến động (Volatility): {signals.get('predicted_volatility_21d', 0):.2%}\n"
                 f"3. Chế độ thị trường (Regime): {signals.get('regime')}\n"
                 f"4. Xu hướng giá (Direction): {signals.get('direction')} (Độ tin cậy mô hình: {confidence:.0%})\n"
                 f"Hệ thống gợi ý hành động: {rec}.\n\n"
                 f"Hãy viết một đoạn nhận định đầu tư ngắn gọn (khoảng 3-4 câu) bằng Tiếng Việt. "
                 f"Giải thích logic đằng sau khuyến nghị này. Tại sao độ tin cậy lại quan trọng ở đây? "
                 f"Văn phong chuyên nghiệp, bình tĩnh."
             )
             
             completion = client.chat.completions.create(
                 messages=[{"role": "user", "content": prompt}],
                 model="llama-3.3-70b-versatile"
             )
             rationale = completion.choices[0].message.content
        except Exception as e:
            print(f"Groq Error: {e}")
            rationale += f"\n(Lỗi kết nối Groq: {e})"

    return jsonable_encoder({
        "symbol": request.symbol,
        "recommendation": rec,
        "rationale": rationale,
        "confidence": round(confidence, 2),
        "signals": signals
    })
