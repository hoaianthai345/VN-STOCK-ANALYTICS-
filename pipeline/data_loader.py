import pandas as pd
import numpy as np
import os
from . import config

def fix_columns(df):
    """Sets the first row as column names and resets index."""
    df = df.copy()
    df.columns = df.iloc[0]
    df = df.iloc[1:].reset_index(drop=True)
    return df

def clean_numeric(series):
    """Cleans numeric columns by removing commas and percentage signs."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace("nan", np.nan)
        .astype(float)
    )

def make_quarter_date(df):
    """Creates a 'quarter_date' column from 'year' and 'quarter'."""
    if "year" in df.columns and "quarter" in df.columns:
        try:
            # Drop rows with NaN year/quarter or handle them
            # Convert to numeric first to coerce errors
            df["year"] = pd.to_numeric(df["year"], errors='coerce')
            df["quarter"] = pd.to_numeric(df["quarter"], errors='coerce')
            
            # Filter invalid rows temporarily or keep them as NaT?
            # Let's keep valid ones
            valid_mask = df["year"].notna() & df["quarter"].notna()
            
            # Create Index for valid rows
            if valid_mask.any():
                dates = pd.PeriodIndex.from_fields(
                    year=df.loc[valid_mask, "year"].astype(int),
                    quarter=df.loc[valid_mask, "quarter"].astype(int),
                    freq="Q"
                ).to_timestamp()
                
                df.loc[valid_mask, "quarter_date"] = dates
                df["quarter_date"] = pd.to_datetime(df["quarter_date"])
            else:
                df["quarter_date"] = pd.NaT

        except Exception as e:
            print(f"Warning: Could not create quarter_date: {e}")
            df["quarter_date"] = pd.NaT
            
    return df

def load_market_data():
    """Loads and standardizes market data."""
    if not os.path.exists(config.MARKET_DATA_PATH):
        raise FileNotFoundError(f"Market data not found at {config.MARKET_DATA_PATH}")
    
    df = pd.read_csv(config.MARKET_DATA_PATH)
    
    # Standardize column names
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    if "ticker" in df.columns:
        df = df.rename(columns={"ticker": "symbol"})
        
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        df = df.rename(columns={"time": "date"})
    
    # Filter by date if configured
    if hasattr(config, 'START_DATE') and "date" in df.columns:
        df = df[df['date'] >= config.START_DATE]
        
    return df

def load_bank_ratio():
    """Loads and cleans bank ratio data from Excel."""
    if not os.path.exists(config.BANK_RATIO_DATA_PATH):
        print(f"Warning: Bank ratio data not found at {config.BANK_RATIO_DATA_PATH}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(config.BANK_RATIO_DATA_PATH, sheet_name="ratio")
        df = fix_columns(df)
        df = df.rename(columns=config.BANK_RATIO_COL_MAPPING)
        
        # Clean numeric columns
        for col in config.BANK_RATIO_NUMERIC_COLS:
            if col in df.columns:
                df[col] = clean_numeric(df[col])
                
        # Filter year >= 2015
        if "year" in df.columns:
            df = df[df["year"].astype(float) >= 2015]
            
        df = make_quarter_date(df)
        return df
    except Exception as e:
        print(f"Error loading bank ratio: {e}")
        return pd.DataFrame()

def load_macro_data():
    """Loads and cleans macro data from Excel."""
    if not os.path.exists(config.MACRO_DATA_PATH):
        print(f"Warning: Macro data not found at {config.MACRO_DATA_PATH}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(config.MACRO_DATA_PATH)
        
        # Clean numeric columns in Macro
        macro_numeric_cols = ["Inflation", "GDP", "CreditGrowth"]
        for col in macro_numeric_cols:
            if col in df.columns:
                df[col] = clean_numeric(df[col])
                
        # Standardize names to create quarter_date
        df = df.rename(columns={"Year": "year", "Quarter": "quarter", "Inflation": "INF", "CreditGrowth": "DC"})
        df = make_quarter_date(df)
        
        return df
    except Exception as e:
        print(f"Error loading macro data: {e}")
        return pd.DataFrame()

def load_fundamental_data():
    """Loads fundamental data, merges with ROA from bank_ratio and Macro data."""
    if not os.path.exists(config.FUNDAMENTAL_DATA_PATH):
        print(f"Warning: Fundamental data not found at {config.FUNDAMENTAL_DATA_PATH}")
        return pd.DataFrame()

    try:
        # Load 'real' fundamental data
        df = pd.read_excel(config.FUNDAMENTAL_DATA_PATH, sheet_name="data")
        df = df.rename(columns=config.FUNDAMENTAL_COL_MAPPING)
        
        # Load Bank Ratio to get ROA
        bank_ratio = load_bank_ratio()
        if not bank_ratio.empty and "roa" in bank_ratio.columns:
            roa_df = bank_ratio[["symbol", "year", "quarter", "roa"]].copy()
            
            if "symbol" in df.columns and "year" in df.columns and "quarter" in df.columns:
                # Ensure types match
                df["year"] = df["year"].astype(int)
                df["quarter"] = df["quarter"].astype(int)
                
                df = df.merge(roa_df, on=["symbol", "year", "quarter"], how="left")
                
                # Use ROA from bank_ratio favor
                if "roa" in df.columns:
                    df["ROA"] = df["roa"]
                    df = df.drop(columns=["roa"])

        # Create quarter_date
        df = make_quarter_date(df)

        # Load and Merge Macro
        macro = load_macro_data()
        if not macro.empty and "quarter_date" in macro.columns:
            macro_cols = ["quarter_date", "GDP", "DC", "INF"]
            existing_macro_cols = [c for c in macro_cols if c in macro.columns]
            
            df = df.merge(macro[existing_macro_cols], on="quarter_date", how="left")

        return df
    except Exception as e:
        print(f"Error loading fundamental data: {e}")
        return pd.DataFrame()

def gather_data():
    """
    Orchestrates the loading of all data sources.
    Returns dictionary with market, micro, and sentiment dataframes.
    """
    print("Loading Market Data...")
    market_df = load_market_data()
    
    print("Loading Micro Data (Fundamental + Macro)...")
    micro_df = load_fundamental_data()
    
    sentiment_df = None
    if os.path.exists(config.SENTIMENT_DATA_PATH):
        print("Loading Sentiment Data...")
        try:
            sentiment_df = pd.read_csv(config.SENTIMENT_DATA_PATH)
        except Exception:
            pass
    
    return {
        "market": market_df,
        "micro": micro_df,
        "sentiment": sentiment_df
    }
