import pandas as pd
import numpy as np

def safe_log_return(close: pd.Series, horizon: int = 21) -> pd.Series:
    """
    Calculate log return: log(close_{t+h}/close_t)
    """
    close = pd.to_numeric(close, errors="coerce")
    close = close.where(close > 0, np.nan)
    return np.log(close.shift(-horizon) / close)

def safe_log_return_1d(close: pd.Series) -> pd.Series:
    """log return 1-day: log(close_t / close_{t-1})"""
    close = close.astype("float64")
    return np.log(close / close.shift(1))

def future_realized_vol(close: pd.Series, horizon: int = 21) -> pd.Series:
    """
    Future realized volatility over next horizon days.
    vol_future(t) = std(logret_{t+1} ... logret_{t+horizon})
    """
    logret_1d = safe_log_return_1d(close)
    logret_next = logret_1d.shift(-1)
    # min_periods can be adjusted, but kept as horizon for consistency with notebook
    vol_future = logret_next.rolling(horizon, min_periods=horizon).std()
    return vol_future

def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index)"""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Calculate ATR (Average True Range)"""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    atr = true_range.rolling(window=window).mean()
    return atr

def calculate_bb_width(close: pd.Series, window: int = 20, std_dev: int = 2) -> pd.Series:
    """Calculate Bollinger Bands Width"""
    ma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    
    upper = ma + (std * std_dev)
    lower = ma - (std * std_dev)
    
    # Avoid division by zero
    ma = ma.replace(0, np.nan)
    bb_width = (upper - lower) / ma
    return bb_width

def calculate_rolling_volatility(close: pd.Series, window: int = 21) -> pd.Series:
    """Calculate historical realized volatility (standard deviation of returns)"""
    log_ret = safe_log_return_1d(close)
    return log_ret.rolling(window=window).std()

def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators for a DataFrame containing OHLCV data.
    Expects columns: 'high', 'low', 'close', 'symbol', 'date' (or 'time').
    """
    df = df.copy()
    
    # ensure sorted by date per symbol if multiple symbols
    if 'symbol' in df.columns:
        df = df.sort_values(['symbol', 'date'])
        
        # Group by symbol for calculations
        grouped = df.groupby('symbol')
        
        df['RSI_14'] = grouped['close'].transform(lambda x: calculate_rsi(x, 14))
        df['ATR_14'] = grouped.apply(lambda x: calculate_atr(x['high'], x['low'], x['close'], 14)).reset_index(level=0, drop=True)
        # ATR % (as used in notebook: ATR_14_pct)
        df['ATR_14_pct'] = df['ATR_14'] / df['close']
        
        df['BB_width'] = grouped['close'].transform(lambda x: calculate_bb_width(x, 20, 2))
        
        # Market features (Group A in notebook)
        df['ret_1d'] = grouped['close'].transform(lambda x: safe_log_return_1d(x))
        df['ret_5d'] = grouped['close'].transform(lambda x: safe_log_return(x, 5)) # Note: safe_log_return is FORWARD looking in notebook for target, but here we likely want backward for features?
        # WAIT: The notebook features "ret_1d", "ret_5d" in Group A are LAGGED features (past returns). 
        # But `safe_log_return(horizon=-5)`? 
        # Let's check notebook implementation of "ret_1d" feature vs target.
        # Target: `safe_log_return(s, horizon=21)` which is shift(-horizon) -> FUTURE.
        # Feature: "ret_1d" joined from `price_feat`. 
        # I need to implement PAST returns.
        
        # Correct implementation for FEATURES (Past Returns):
        df['ret_1d_lag'] = grouped['close'].transform(lambda x: np.log(x / x.shift(1)))
        df['ret_5d_lag'] = grouped['close'].transform(lambda x: np.log(x / x.shift(5)))
        df['ret_21d_lag'] = grouped['close'].transform(lambda x: np.log(x / x.shift(21)))
        
        df['vol_5d'] = grouped['close'].transform(lambda x: calculate_rolling_volatility(x, 5))
        df['vol_21d'] = grouped['close'].transform(lambda x: calculate_rolling_volatility(x, 21))
        
        df['high_low_range'] = (df['high'] - df['low']) / df['close']
        
        # Moving Averages
        df['ma21'] = grouped['close'].transform(lambda x: x.rolling(21).mean())
        df['ma63'] = grouped['close'].transform(lambda x: x.rolling(63).mean())
        df['close_vs_ma21'] = df['close'] / df['ma21'] - 1
        df['close_vs_ma63'] = df['close'] / df['ma63'] - 1
        
    else:
        # Single symbol logic
        raise NotImplementedError("This pipeline expects 'symbol' column for grouping.")

    return df
