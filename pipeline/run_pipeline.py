import sys
import os
import random
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

# Add project root to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.models import StockPrice, Signal
from pipeline.mock_model import MockModel

# Banks list
BANKS = ["VCB", "TCB", "ACB", "BID", "CTG", "MBB", "VPB"]

def generate_synthetic_data(days=30):
    """Generate last N days of data for each bank"""
    data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    for symbol in BANKS:
        current_price = random.uniform(20000, 90000)
        for i in range(days):
            date = start_date + timedelta(days=i)
            change = random.uniform(-0.02, 0.02)
            open_p = current_price
            close_p = current_price * (1 + change)
            high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.01))
            low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.01))
            vol = random.randint(100000, 5000000)
            
            data.append({
                "symbol": symbol,
                "date": date.date(),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "volume": vol
            })
            current_price = close_p
            
    return pd.DataFrame(data)

def save_to_db(db: Session, df_prices: pd.DataFrame, df_signals: pd.DataFrame):
    # Save Prices
    for _, row in df_prices.iterrows():
        # Check if exists
        exists = db.query(StockPrice).filter(
            StockPrice.symbol == row['symbol'],
            StockPrice.date == row['date']
        ).first()
        
        if not exists:
            db_price = StockPrice(**row.to_dict())
            db.add(db_price)
            
    # Save Signals
    for _, row in df_signals.iterrows():
         # Check if exists
        exists = db.query(Signal).filter(
            Signal.symbol == row['symbol'],
            Signal.date == row['date']
        ).first()
        
        if not exists:
            db_signal = Signal(**row.to_dict())
            db.add(db_signal)
    
    db.commit()
    print("Data saved to database.")

def run_pipeline():
    print("Running pipeline...")
    # 1. Generate Data
    df_prices = generate_synthetic_data(days=30)
    print(f"Generated {len(df_prices)} price records.")
    
    # 2. Mock Inference
    model = MockModel()
    predictions = model.predict(df_prices)
    
    # Combine predictions with basic info for saving
    df_signals = df_prices[['symbol', 'date']].copy()
    for col in predictions.columns:
        df_signals[col] = predictions[col]
        
    print(f"Generated {len(df_signals)} signal records.")
    
    # 3. Save to DB
    # Create tables if not exist (just in case)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        save_to_db(db, df_prices, df_signals)
    finally:
        db.close()
        
if __name__ == "__main__":
    run_pipeline()
