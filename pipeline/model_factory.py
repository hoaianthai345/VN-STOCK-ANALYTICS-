from xgboost import XGBRegressor, XGBClassifier
from .config import (
    XGB_PARAMS_RETURN, 
    XGB_PARAMS_RISK, 
    XGB_PARAMS_REGIME, 
    XGB_PARAMS_DIRECTION
)

def create_return_model():
    """Create XGBoost Regressor for Return prediction"""
    return XGBRegressor(**XGB_PARAMS_RETURN)

def create_risk_model():
    """Create XGBoost Regressor for Risk (Volatility) prediction"""
    return XGBRegressor(**XGB_PARAMS_RISK)

def create_regime_model():
    """Create XGBoost Classifier for Regime prediction"""
    return XGBClassifier(**XGB_PARAMS_REGIME)

def create_direction_model():
    """Create XGBoost Classifier for Direction prediction"""
    return XGBClassifier(**XGB_PARAMS_DIRECTION)
