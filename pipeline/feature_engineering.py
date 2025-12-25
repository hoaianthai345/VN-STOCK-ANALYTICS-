import pandas as pd
import numpy as np

def safe_log_return(series, horizon=1):
    """Calculate log return: ln(P_t / P_{t-k})"""
    return np.log(series / series.shift(horizon))

def make_quarter_date(date_series):
    """Convert daily dates to quarter start dates (for merging with quarterly data)."""
    return date_series.dt.to_period("Q").dt.start_time

# --- Helpers for Technical Indicators ---
def compute_rsi(series, window=14):
    """Relative Strength Index (RSI) using Wilder's smoothing."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).abs()
    loss = (delta.where(delta < 0, 0)).abs()
    
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_atr_pct(high, low, close, window=14):
    """Average True Range (ATR) scaled by Close price."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window, min_periods=window).mean()
    return atr / close

def compute_bb_width(close, window=20, n_std=2):
    """Bollinger Band Width: (Upper - Lower) / Middle"""
    ma = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std()
    
    upper = ma + n_std * std
    lower = ma - n_std * std
    
    # Avoid division by zero
    return (upper - lower) / ma.replace(0, np.nan)

# --- Feature Groups ---

def build_market_features(df):
    """Group A: Market Features (Momentum, Volatility, Trend)"""
    df = df.copy()
    
    # Momentum
    df["ret_1d"] = df.groupby("symbol")["close"].pct_change(1)
    df["ret_5d"] = df.groupby("symbol")["close"].pct_change(5)
    df["ret_21d"] = df.groupby("symbol")["close"].pct_change(21)
    
    # Volatility
    df["vol_5d"] = (
        df.groupby("symbol")["ret_1d"]
        .rolling(5).std()
        .reset_index(level=0, drop=True)
    )
    df["vol_21d"] = (
        df.groupby("symbol")["ret_1d"]
        .rolling(21).std()
        .reset_index(level=0, drop=True)
    )
    df["high_low_range"] = (df["high"] - df["low"]) / df["close"]
    
    # Trend (Distance to MA)
    ma21 = df.groupby("symbol")["close"].rolling(21).mean().reset_index(level=0, drop=True)
    ma63 = df.groupby("symbol")["close"].rolling(63).mean().reset_index(level=0, drop=True)
    
    df["close_vs_ma21"] = (df["close"] - ma21) / ma21
    df["close_vs_ma63"] = (df["close"] - ma63) / ma63
    
    return df

def build_technical_features(df):
    """Group B: Technical Indicators (RSI, ATR, BB)"""
    df = df.copy()
    
    # RSI
    df["RSI_14"] = df.groupby("symbol")["close"].transform(lambda x: compute_rsi(x, 14))
    
    # ATR %
    # Need to group by symbol first to align indexes correctly
    # transform doesn"t work easily with multiple columns, so we iterate
    # A faster vectorised way for multi-index might be complex, so we rely on apply or per-group ops.
    # Simple workaround: calculate per group
    
    def _calc_atr(g):
        return compute_atr_pct(g["high"], g["low"], g["close"], 14)
    
    df["ATR_14_pct"] = df.groupby("symbol", group_keys=False).apply(_calc_atr)
    
    # BB Width
    df["BB_width"] = df.groupby("symbol")["close"].transform(lambda x: compute_bb_width(x, 20, 2))
    
    return df

def build_sentiment_features(news_df):
    """Group C: Sentiment Features (Lagged)"""
    # Assuming news_df has [symbol, date, daily_sentiment, sentiment_7d_avg, buzz_7d, sentiment_decay]
    # And is ALREADY daily.
    
    df = news_df.copy()
    if "date" in df.columns:
        df = df.rename(columns={"date": "time"})
    
    df = df.sort_values(["symbol", "time"])
    
    # Lags for daily_sentiment
    for lag in [1, 3, 7]:
        df[f"sentiment_lag_{lag}"] = df.groupby("symbol")["daily_sentiment"].shift(lag)
        
    # Lags for other metrics
    df["sentiment_7d_avg_lag1"] = df.groupby("symbol")["sentiment_7d_avg"].shift(1)
    df["buzz_7d_lag1"] = df.groupby("symbol")["buzz_7d"].shift(1)
    df["sentiment_decay_lag1"] = df.groupby("symbol")["sentiment_decay"].shift(1)
    
    return df

def build_macro_features(macro_df, fx_df):
    """Group D: Macro & FX Context"""
    # 1. Macro (Quarterly -> Daily Mapping will happen in merge)
    # Just prepare the lags here
    macro = macro_df.copy()
    macro["GDP_t_1Q"] = macro["GDP"].shift(1) # Shift 1 row (quarter)
    macro["INF_t_1Q"] = macro["INF"].shift(1)
    macro["DC_t_1Q"] = macro["DC"].shift(1)
    
    # 2. FX (Daily)
    fx = fx_df.copy()
    if "date" in fx.columns:
        fx = fx.rename(columns={"date": "time"})
    
    fx["fx_ret_5d"] = fx["close"].pct_change(5)
    fx["fx_vol_21d"] = fx["close"].pct_change().rolling(21).std()
    
    fx_cols = ["time", "fx_ret_5d", "fx_vol_21d"]
    # Return both frames to be merged later
    return macro, fx[fx_cols]

def build_bank_features(bank_df):
    """Group E: Bank Fundamentals (Standardized per symbol)"""
    df = bank_df.copy()
    
    cols = ["ROE", "ROA", "P_B", "LDR", "CIR", "Assets_Equity"]
    
    for col in cols:
        if col in df.columns:
            # Z-score normalization per bank
            df[f"{col}_z"] = df.groupby("symbol")[col].transform(
                lambda x: (x - x.mean()) / x.std()
            )
            
    return df

def build_target(df, horizon=21):
    """Calculate target: Log return over horizon days."""
    df["log_return_21d"] = df.groupby("symbol")["close"].transform(
        lambda x: safe_log_return(x, horizon)
    )
    # Clean infs
    df["log_return_21d"] = df["log_return_21d"].replace([np.inf, -np.inf], np.nan)
    return df
