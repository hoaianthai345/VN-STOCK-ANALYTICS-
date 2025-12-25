from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv() # Load variables from .env

from .database import engine, Base, get_db
from backend.app.models import models
from backend.app.api import signals, market, advisor, admin

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VN Bank Advisor API")

app.include_router(signals.router, prefix="/api/v1", tags=["signals"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(advisor.router, prefix="/api/v1/advisor", tags=["advisor"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to VN Bank Advisor API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {"status": "ok", "db": "connected"}
