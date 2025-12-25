import pandas as pd
import numpy as np
import os
from . import config

class PortfolioOptimizer:
    """
    Markowitz Mean-Variance Portfolio Optimization.
    """
    def __init__(self, start_date=None, end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.symbols = []
        self.daily_returns = None
        self.mean_returns = None
        self.cov_matrix = None
        
    def load_data(self, df_market):
        """
        Load market data and calculate daily returns for optimization.
        Expects a DataFrame with 'symbol', 'date', 'close'.
        """
        # Pivot to Date x Symbol matrix
        if 'time' in df_market.columns:
            df_market = df_market.rename(columns={'time': 'date'})
            
        pivot_df = df_market.pivot(index='date', columns='symbol', values='close')
        
        # Filter dates
        if self.start_date:
            pivot_df = pivot_df[pivot_df.index >= self.start_date]
        if self.end_date:
            pivot_df = pivot_df[pivot_df.index <= self.end_date]
            
        self.daily_returns = pivot_df.pct_change().dropna()
        self.symbols = self.daily_returns.columns.tolist()
        
    def calculate_metrics(self):
        """Calculate Annualized Mean Returns and Covariance Matrix."""
        if self.daily_returns is None:
            raise ValueError("Data not loaded.")
            
        # Annualized values (assuming 252 trading days)
        self.mean_returns = self.daily_returns.mean() * 252
        self.cov_matrix = self.daily_returns.cov() * 252
        
    def optimize(self, target_return=None, risk_free_rate=0.03):
        """
        Optimize portfolio weights.
        Placeholder for Scipy Minimize (SLSQP).
        """
        # TODO: Implement Efficient Frontier logic
        print(f"Optimizing for {len(self.symbols)} stocks...")
        
        # Mock result: Equal weights
        n = len(self.symbols)
        return {
            "weights": {s: 1.0/n for s in self.symbols},
            "expected_return": 0.15,
            "expected_volatility": 0.10,
            "sharpe_ratio": 1.2
        }

if __name__ == "__main__":
    # Test logic
    from .data_loader import load_market_data
    df = load_market_data()
    
    opt = PortfolioOptimizer()
    opt.load_data(df)
    opt.calculate_metrics()
    res = opt.optimize()
    print(res)
