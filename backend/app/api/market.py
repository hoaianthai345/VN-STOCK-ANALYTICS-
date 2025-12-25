from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import StockPrice, Signal
import pandas as pd
from typing import List, Optional
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

router = APIRouter()

class MarketSummary(BaseModel):
    date: str
    total_volume: float
    top_gainers: List[dict]
    top_losers: List[dict]

class BankHistory(BaseModel):
    date: str
    close: float
    volume: float
    rsi: Optional[float] = None
    macd: Optional[float] = None

from pipeline.data_loader import load_market_data, load_fundamental_data

@router.get("/summary", response_model=MarketSummary)
def get_market_summary(db: Session = Depends(get_db)):
    """
    Get the latest market summary (Dashboard).
    """
    # Use real data from pipeline loader
    df = load_market_data()
    if df.empty:
         return {
            "date": "N/A",
            "total_volume": 0,
            "top_gainers": [],
            "top_losers": []
        }
    
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].copy()
    
    # Calculate daily change if not present (assuming Close is close price)
    # Using 'change' column if exists, else compute from previous day (complex in this snippet, using placeholders if needed)
    # For MVP, assuming 'change' column exists or using random/placeholder
    if "change" not in latest_df.columns:
         latest_df["change"] = 0.0 # Placeholder
         
    # Sort
    latest_df = latest_df.sort_values("change", ascending=False)
    
    total_vol = latest_df["volume"].sum() if "volume" in latest_df.columns else 0
    
    gainers = latest_df.head(5)[["symbol", "change"]].to_dict(orient="records")
    losers = latest_df.tail(5)[["symbol", "change"]].sort_values("change")[["symbol", "change"]].to_dict(orient="records")
    
    return jsonable_encoder({
        "date": str(latest_date.date()),
        "total_volume": float(total_vol),
        "top_gainers": gainers,
        "top_losers": losers
    })

@router.get("/symbols")
def get_symbols():
    """
    Get list of available bank symbols.
    """
    df = load_market_data()
    if df.empty:
        return []
    
    if "symbol" in df.columns:
        symbols = sorted(df["symbol"].unique().tolist())
        return jsonable_encoder(symbols)
    return jsonable_encoder([])

@router.get("/history/{symbol}")
def get_bank_history(symbol: str):
    """
    Get historical data for a specific bank or ALL Industry (Explorer).
    """
    df = load_market_data()
    if df.empty:
        return []
    
    df["date"] = df["date"].astype(str)
    
    if symbol == "ALL":
        # Aggregate logic: Average Close, Sum Volume per Day
        # We need numerical columns only
        numeric_cols = ["open", "high", "low", "close", "volume"] 
        # Ensure cols exist
        valid_cols = [c for c in numeric_cols if c in df.columns]
        
        agg_df = df.groupby("date")[valid_cols].mean().reset_index()
        # For volume, sum makes more sense for "Industry Total", but mean is "Average Bank"
        # User asked for "Toàn ngành" (Whole Industry), so usually Sum Volume, Avg Price index.
        # Let's use MEAN for price and SUM for volume to represent the sector activity.
        if "volume" in df.columns:
             vol_sum = df.groupby("date")["volume"].sum().reset_index()
             agg_df["volume"] = vol_sum["volume"]
             
        # Add a dummy symbol
        agg_df["symbol"] = "ALL"
        
        # Replace NaN with None
        agg_df = agg_df.where(pd.notnull(agg_df), None)
        data = agg_df.to_dict(orient="records")
    else:
        bank_df = df[df["symbol"] == symbol].copy()
        # Replace NaN with None
        bank_df = bank_df.where(pd.notnull(bank_df), None)
        data = bank_df.to_dict(orient="records")
        
    return jsonable_encoder(data)

@router.get("/financials/{symbol}")
def get_bank_financials(symbol: str):
    """
    Get quarterly financial data for a bank or ALL Industry avg.
    """
    df = load_fundamental_data()
    if df.empty:
        return []

    # Convert quarter_date to string
    if "quarter_date" in df.columns:
        df["quarter_date"] = df["quarter_date"].astype(str)
    
    if symbol == "ALL":
        # Average key metrics across all banks per quarter
        numeric_cols = ["ROE", "ROA", "P_B", "GDP", "Inflation", "CreditGrowth"] # Add others as needed
        valid_cols = [c for c in numeric_cols if c in df.columns]
        
        agg_df = df.groupby("quarter_date")[valid_cols].mean().reset_index()
        # Replace NaN with None
        agg_df = agg_df.where(pd.notnull(agg_df), None)
        return jsonable_encoder(agg_df.to_dict(orient="records"))
    else:
        bank_df = df[df["symbol"] == symbol].copy()
        # Replace NaN with None
        bank_df = bank_df.where(pd.notnull(bank_df), None)
        return jsonable_encoder(bank_df.to_dict(orient="records"))
