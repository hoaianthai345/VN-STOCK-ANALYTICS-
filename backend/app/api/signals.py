from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.models import Signal, StockPrice
from pydantic import BaseModel
from datetime import date

router = APIRouter()

class SignalSchema(BaseModel):
    symbol: str
    date: date
    signal_1: float
    signal_2: float
    signal_3: float
    signal_4: float
    prediction: str
    confidence: float

    class Config:
        from_attributes = True

@router.get("/signals", response_model=List[SignalSchema])
def get_signals(
    symbol: Optional[str] = None, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    query = db.query(Signal)
    if symbol:
        query = query.filter(Signal.symbol == symbol)
    
    # Get latest signals first
    return query.order_by(Signal.date.desc()).limit(limit).all()

@router.get("/signals/latest", response_model=List[SignalSchema])
def get_latest_signals(db: Session = Depends(get_db)):
    """Get the most recent signal for each stock"""
    subquery = db.query(
        Signal.symbol, 
        func.max(Signal.date).label('max_date')
    ).group_by(Signal.symbol).subquery()
    
    query = db.query(Signal).join(
        subquery, 
        (Signal.symbol == subquery.c.symbol) & (Signal.date == subquery.c.max_date)
    )
    return query.all()
