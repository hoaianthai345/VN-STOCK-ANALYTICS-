import pandas as pd
import numpy as np
import os
import joblib
import json
import math
from datetime import datetime
from sklearn.metrics import mean_squared_error, accuracy_score

from . import config
from .data_loader import gather_data
from .feature_engineering import (
    build_market_features,
    build_technical_features,
    build_sentiment_features,
    build_macro_features,
    build_bank_features,
    build_target,
    make_quarter_date
)
from .model_factory import (
    create_return_model,
    create_risk_model,
    create_regime_model,
    create_direction_model
)

def run_training():
    print("--- Starting Training Pipeline ---")
    
    # 1. Load Data
    print("Loading raw data...")
    # gather_data returns: {"market": df, "micro": df, "sentiment": df}
    # Note: "micro" usually implies Fundamental + Macro merged
    data_dict = gather_data()
    
    market_df = data_dict.get("market")
    micro_df = data_dict.get("micro")
    sentiment_df = data_dict.get("sentiment")
    
    # Load FX separately if possible (not in gather_data default)
    fx_df = None
    if os.path.exists(config.FX_DATA_PATH):
        try:
            print(f"Loading FX data from {config.FX_DATA_PATH}...")
            fx_df = pd.read_csv(config.FX_DATA_PATH)
            # Ensure standard columns
            fx_df.columns = fx_df.columns.str.lower().str.replace(' ', '_')
            if 'date' in fx_df.columns:
                fx_df['date'] = pd.to_datetime(fx_df['date'])
            # Assuming 'close' exists or rename appropriately if needed (Price -> close)
            if 'price' in fx_df.columns:
                fx_df = fx_df.rename(columns={'price': 'close'})
        except Exception as e:
            print(f"Warning: Failed to load FX data: {e}")

    if market_df is None or market_df.empty:
        print("Error: Market data missing. Aborting.")
        return

    # 2. Feature Engineering (Per Group)
    print("Building features...")
    
    # Group A & B: Market + Technical (on Daily Price)
    print("  - Market & Technical features...")
    market_feat = build_market_features(market_df)
    market_feat = build_technical_features(market_feat)
    
    # Group C: Sentiment (on Daily News)
    sentiment_feat_daily = None
    if sentiment_df is not None and not sentiment_df.empty:
        print("  - Sentiment features...")
        sentiment_feat_daily = build_sentiment_features(sentiment_df)
    
    # Group D: Macro & FX
    # Extract Macro from 'micro_df' if possible, or load separately?
    # In data_loader, micro already has GDP/INF merged.
    # We'll calculate lags on micro_df directly or splitting it.
    # build_macro_features expects (macro_df, fx_df).
    # We can pass micro_df as macro_df if it contains the columns.
    
    fx_feat_daily = None
    if micro_df is not None and not micro_df.empty:
        print("  - Macro/FX context features...")
        # We pass micro_df as the macro source. It has quarter_date.
        # If fx_df is None, create dummy
        if fx_df is None:
             fx_df = pd.DataFrame({"close": [0]*len(market_df), "date": market_df["date"]})
             
        macro_feat_quarterly, fx_feat_daily = build_macro_features(micro_df, fx_df)
        
    # Group E: Bank Fundamentals
    bank_feat_quarterly = None
    if micro_df is not None and not micro_df.empty:
        print("  - Bank Fundamental features...")
        bank_feat_quarterly = build_bank_features(micro_df)

    # 3. Merge Consolidated DataFrame (Walk-forward style merge)
    print("Merging datasets...")
    
    # Start with Market (Daily)
    df = market_feat.copy()
    if "date" in df.columns:
        df = df.rename(columns={"date": "time"})
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values(["symbol", "time"])

    # Merge Sentiment (Daily)
    if sentiment_feat_daily is not None:
        if "date" in sentiment_feat_daily.columns:
            sentiment_feat_daily = sentiment_feat_daily.rename(columns={"date": "time"})
        sentiment_feat_daily["time"] = pd.to_datetime(sentiment_feat_daily["time"])
        
        df = df.merge(sentiment_feat_daily, on=["symbol", "time"], how="left")

    # Merge FX (Daily, broad market)
    if fx_feat_daily is not None:
        if "date" in fx_feat_daily.columns:
            fx_feat_daily = fx_feat_daily.rename(columns={"date": "time"})
        fx_feat_daily["time"] = pd.to_datetime(fx_feat_daily["time"])
        
        # Merge on time only (same for all symbols)
        df = df.merge(fx_feat_daily, on="time", how="left")

    # Merge Quarterly Data (Macro + Bank)
    # Use merge_asof or simple join on quarter_date column
    if bank_feat_quarterly is not None:
        # Create mapping column in daily
        df["quarter_date"] = make_quarter_date(df["time"])
        
        # Prepare quarterly data
        q_data = bank_feat_quarterly.copy()
        # q_data contains bank features AND macro features (since we passed micro_df to both builders and used copy)
        # Actually, build_bank_features returned a copy of micro_df with extra cols.
        # And build_macro_features returned (macro, fx). The macro part is just lags.
        
        # Let's start with bank_feat_quarterly and add macro lags if they exist
        if macro_feat_quarterly is not None:
             # Merge lags into q_data
             cols_to_use = [c for c in macro_feat_quarterly.columns if c not in q_data.columns and c != "quarter_date"]
             # If mapping key is quarter_date?
             # macro_feat_quarterly derived from micro_df, so indexes/dates might match.
             # Ideally join on quarter_date.
             # However, macro_feat_quarterly might have duplicated rows if derived from micro (one per bank).
             # Wait, macro data source is usually one per quarter (unique).
             # But micro_df is merged (Symbol x Quarter).
             # So macro lags are just columns in micro_df already?
             # build_macro_features: `macro = macro_df.copy(); macro["GDP_t_1Q"]...`
             # If we passed micro_df (Symbol x Quarter), then it calculated lags per row?
             # Yes, effectively.
             
             # So just merge q_data (Bank Features) with macro_feat_quarterly (Macro Lags)?
             # Or simply: bank_feat_quarterly IS derived from micro_df, check if it has macro cols.
             # If we ran build_macro first, maybe we should have merged?
             
             # Simplification: Merge macro lags into q_data on index or common keys
             # Since both come from micro_df, they align.
             # Just combine columns.
             for c in macro_feat_quarterly.columns:
                 if c not in q_data.columns:
                     q_data[c] = macro_feat_quarterly[c]

        # Merge Q-data to Daily
        # Left merge on [symbol, quarter_date]
        df = df.merge(q_data, on=["symbol", "quarter_date"], how="left")

    # 4. Filter Timeline & Finalize Features
    if config.START_TRAIN_DATE:
        df = df[df["time"] >= pd.Timestamp(config.START_TRAIN_DATE)].copy()

    # 5. Generate Targets
    print(f"Generating Target: {config.TARGET_COL}")
    df = build_target(df, horizon=config.PREDICTION_HORIZON)
    
    # 6. Select Features
    feature_cols = [c for c in config.FEATURE_COLS if c in df.columns]
    print(f"Features available: {len(feature_cols)} / {len(config.FEATURE_COLS)}")
    
    # Save feature list used
    os.makedirs(config.ARTIFACTS_DIR, exist_ok=True)
    with open(os.path.join(config.ARTIFACTS_DIR, "feature_cols.json"), "w") as f:
        json.dump(feature_cols, f)

    # 7. Training Loop (All Targets)
    targets = [config.TARGET_COL] # For now focusing on main target
    # Or map 4 models?
    # The requirement is 4 models: Return, Risk, Regime, Direction.
    # Group A-E are INPUT features.
    # Targets need to be created for Risk/Regime/Direction?
    # build_target only created log_return_21d.
    # I should add others or reuse log_return for direction?
    # The notebook calculated `log_return_21d` and `target_risk`?
    # Let's stick to the existing `model_factory` usage if possible, 
    # but model_factory creates models, not targets.
    # I will construct targets dynamically here or assume simple proxies for MVP:
    # - Return: log_return_21d (Regression)
    # - Risk: Volatility 21d future? (Regression)
    # - Direction: Sign of log_return_21d (Classification)
    # - Regime: ? (Clustering/Classification) -> Placeholder or simple Quantile?
    
    # Constructing these proxy targets on the fly
    df["target_return"] = df["log_return_21d"]
    df["target_direction"] = (df["log_return_21d"] > 0).astype(int)
    
    # Future Volatility (proxy for Risk)
    # Calculate future 21d vol: rolling std shifted back
    df["target_risk"] = df.groupby("symbol")["ret_1d"].transform(
        lambda x: x.shift(-config.PREDICTION_HORIZON).rolling(config.PREDICTION_HORIZON).std()
    )
    
    # Regime (proxy: 0=Bear, 1=Neutral, 2=Bull)
    # Thresholds: return < -0.02 (Bear), return > 0.02 (Bull), else Neutral
    def get_regime(r):
        if r < -0.02: return 0
        elif r > 0.02: return 2
        else: return 1
        
    df["target_regime"] = df["log_return_21d"].apply(get_regime) 

    models_config = [
        ("return", create_return_model(), "target_return", False),
        ("risk", create_risk_model(), "target_risk", False),
        ("direction", create_direction_model(), "target_direction", True),
        ("regime", create_regime_model(), "target_regime", True)
    ]
    
    all_metrics = []
    comparison_points = []

    for name, model, target, is_class in models_config:
        print(f"\nTraining {name} model (Target: {target})...")
        
        # Prepare Data
        cols = feature_cols + [target]
        train_df = df.dropna(subset=cols).replace([np.inf, -np.inf], np.nan).dropna()
        
        if train_df.empty:
            print(f"Skipping {name}: No valid data.")
            continue
            
        X = train_df[feature_cols]
        y = train_df[target]
        
        # Split (Time-based 80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Train
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        
        # Metrics
        metric_res = {"model": name}
        if is_class:
            acc = accuracy_score(y_test, y_pred)
            metric_res["accuracy"] = acc
            print(f"  Accuracy: {acc:.4f}")
        else:
            mse = mean_squared_error(y_test, y_pred)
            rmse = math.sqrt(mse)
            metric_res["rmse"] = rmse
            print(f"  RMSE: {rmse:.4f}")
            
        all_metrics.append(metric_res)
        
        # Save Model
        joblib.dump(model, os.path.join(config.ARTIFACTS_DIR, f"{name}_model.joblib"))
        
        # Save Comparison Data (Sample)
        # Predict Full
        y_full = model.predict(X)
        meta = train_df[["time", "symbol"]].copy()
        meta["true"] = y
        meta["pred"] = y_full
        meta["model"] = name
        meta["split"] = ["train"]*split_idx + ["test"]*(len(X)-split_idx)
        meta["time"] = meta["time"].astype(str)
        
        comparison_points.extend(meta.to_dict(orient="records"))

    # Save Artifacts
    with open(os.path.join(config.ARTIFACTS_DIR, "metrics.json"), "w") as f:
        json.dump(all_metrics, f)
        
    with open(os.path.join(config.ARTIFACTS_DIR, "comparison_data.json"), "w") as f:
        json.dump(comparison_points, f)
        
    print("\nTraining Pipeline Completed Successfully.")

if __name__ == "__main__":
    run_training()
