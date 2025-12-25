import pandas as pd
import numpy as np
import os
import joblib
import json
from . import config
from .data_loader import gather_data
from .feature_engineering import (
    build_market_features,
    build_technical_features,
    build_sentiment_features,
    build_macro_features,
    build_bank_features,
    make_quarter_date
)

def load_models():
    """Load all 4 models and feature list."""
    models = {}
    try:
        models["return"] = joblib.load(os.path.join(config.ARTIFACTS_DIR, "return_model.joblib"))
        models["risk"] = joblib.load(os.path.join(config.ARTIFACTS_DIR, "risk_model.joblib"))
        models["regime"] = joblib.load(os.path.join(config.ARTIFACTS_DIR, "regime_model.joblib"))
        models["direction"] = joblib.load(os.path.join(config.ARTIFACTS_DIR, "direction_model.joblib"))
        
        with open(os.path.join(config.ARTIFACTS_DIR, "feature_cols.json"), "r") as f:
            models["features"] = json.load(f)
            
        print("Models loaded successfully.")
        return models
    except FileNotFoundError as e:
        print(f"Error loading models: {e}")
        return None

def prepare_latest_data(symbol=None):
    """
    Load data and generate features for the latest available date.
    Returns a DataFrame with 1 row per symbol (latest date).
    """
    # 1. Gather Data (Re-using loader logic)
    print("Loading raw data...")
    data_dict = gather_data()
    market_df = data_dict.get("market")
    micro_df = data_dict.get("micro")
    sentiment_df = data_dict.get("sentiment")
    
    # Load FX
    fx_df = None
    if os.path.exists(config.FX_DATA_PATH):
        try:
           fx_df = pd.read_csv(config.FX_DATA_PATH)
           fx_df.columns = fx_df.columns.str.lower().str.replace(' ', '_')
           if 'date' in fx_df.columns:
               fx_df['date'] = pd.to_datetime(fx_df['date'])
           if 'price' in fx_df.columns:
               fx_df = fx_df.rename(columns={'price': 'close'})
        except Exception:
            pass

    if market_df is None or market_df.empty:
        return pd.DataFrame()

    # 2. Build Features
    print("Building features...")
    # Group A & B
    market_feat = build_market_features(market_df)
    market_feat = build_technical_features(market_feat)
    
    # Group C
    sentiment_feat = None
    if sentiment_df is not None:
        sentiment_feat = build_sentiment_features(sentiment_df)
        
    # Group D
    macro_quarterly = None
    fx_daily = None
    if micro_df is not None:
        if fx_df is None:
             fx_df = pd.DataFrame({"close": [0]*len(market_df), "date": market_df["date"]})
        macro_quarterly, fx_daily = build_macro_features(micro_df, fx_df)
        
    # Group E
    bank_quarterly = None
    if micro_df is not None:
        bank_quarterly = build_bank_features(micro_df)
        
    # 3. Merge
    print("Merging data...")
    df = market_feat.copy()
    if "date" in df.columns:
        df = df.rename(columns={"date": "time"})
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values(["symbol", "time"])
    
    # Merge Sentiment
    if sentiment_feat is not None:
        if "date" in sentiment_feat.columns:
            sentiment_feat = sentiment_feat.rename(columns={"date": "time"})
        sentiment_feat["time"] = pd.to_datetime(sentiment_feat["time"])
        df = df.merge(sentiment_feat, on=["symbol", "time"], how="left")
        
    # Merge FX
    if fx_daily is not None:
        if "date" in fx_daily.columns:
            fx_daily = fx_daily.rename(columns={"date": "time"})
        fx_daily["time"] = pd.to_datetime(fx_daily["time"])
        df = df.merge(fx_daily, on="time", how="left")
        
    # Merge Quarterly
    if bank_quarterly is not None:
        df["quarter_date"] = make_quarter_date(df["time"])
        q_data = bank_quarterly.copy()
        if macro_quarterly is not None:
             for c in macro_quarterly.columns:
                 if c not in q_data.columns:
                     q_data[c] = macro_quarterly[c]
        
        df = df.merge(q_data, on=["symbol", "quarter_date"], how="left")
        
    # 4. Filter Latest
    # If symbol is provided, filter first
    if symbol and symbol != "ALL":
        df = df[df["symbol"] == symbol]
        
    # Drop rows without features (na)
    # Actually, we might want to fillNA or tolerate some missing
    # But models need exact columns.
    
    # Get latest date per symbol
    latest_df = df.sort_values("time").groupby("symbol").tail(1)
    
    return latest_df

def run_inference(symbol=None):
    """
    Run inference for a specific symbol or all.
    Returns dict or list of dicts with signals.
    """
    models = load_models()
    if not models:
        return None
        
    df_latest = prepare_latest_data(symbol)
    if df_latest.empty:
        return None
        
    feature_cols = models["features"]
    
    # Ensure all columns exist
    missing_cols = [c for c in feature_cols if c not in df_latest.columns]
    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
        # Add them as NaN or 0? 0 is safer for XGBoost than fail
        for c in missing_cols:
            df_latest[c] = np.nan
            
    X = df_latest[feature_cols]
    
    # Predict
    results = []
    
    # Batch predict
    try:
        p_return = models["return"].predict(X)
        p_risk = models["risk"].predict(X)
        p_regime = models["regime"].predict(X) # 0,1,2
        p_direction = models["direction"].predict(X) # 0 or 1
        
        # Get probabilities for Direction
        if hasattr(models["direction"], "predict_proba"):
            p_direction_prob = models["direction"].predict_proba(X)[:, 1] # Prob of class 1 (Up)
        else:
            p_direction_prob = p_direction.astype(float) # Fallback

        
        # Determine Recommendation Logic (Rule-based)
        # Buy: High Return (> 2%), Low Risk (< 1%), Bull Regime, Up Direction
        # Sell: Negative Return (< -2%), Bear Regime
        
        for i, (idx, row) in enumerate(df_latest.iterrows()):
            ret = float(p_return[i])
            risk = float(p_risk[i])
            regime = int(p_regime[i])
            direction = int(p_direction[i])
            prob = float(p_direction_prob[i])
            
            # Simple heuristic
            rec = "HOLD"
            score = 0
            
            if ret > 0.02: score += 1
            if ret < -0.02: score -= 1
            if direction == 1: score += 1
            else: score -= 1
            
            # Regime: assume 1 is Bull? We need to know label encoding.
            # Assuming 1 is high volatility (Bear?) or just Direction?
            # Let's assume Regime 1 = Bull/Positive for MVP or just ignore if unsure.
            
            if score >= 1:
                rec = "BUY"
            elif score <= -1:
                rec = "SELL"
                
            # Sanitize NaNs for JSON
            def sanitize(v, precision=4):
                if pd.isna(v) or np.isnan(v):
                    return None
                return round(float(v), precision)

            res = {
                "symbol": row["symbol"],
                "date": str(row["time"].date()),
                "signals": {
                    "predicted_return_21d": sanitize(ret),
                    "predicted_volatility_21d": sanitize(risk),
                    "regime": regime, 
                    "direction": "Up" if direction == 1 else "Down",
                    "pred_direction_prob": sanitize(prob) or 0.5 # Default to 0.5 if NaN
                },
                "recommendation": rec
            }
            results.append(res)
            
    except Exception as e:
        print(f"Inference Error: {e}")
        return None
        
    if symbol and symbol != "ALL" and len(results) == 1:
        return results[0]
        
    return results

if __name__ == "__main__":
    res = run_inference("VCB")
    print(res)
