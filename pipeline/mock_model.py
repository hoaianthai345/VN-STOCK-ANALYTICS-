import numpy as np
import pandas as pd

class MockModel:
    def __init__(self):
        print("Initializing Mock Model...")
        
    def predict(self, df: pd.DataFrame):
        """
        Takes a DataFrame of stock features and returns 4 signals + prediction.
        """
        n = len(df)
        
        # Generate 4 random signals between 0 and 1
        signals = {
            "signal_1": np.random.uniform(0, 1, n),
            "signal_2": np.random.uniform(0, 1, n),
            "signal_3": np.random.uniform(0, 1, n),
            "signal_4": np.random.uniform(0, 1, n),
        }
        
        # Generate a prediction based on average of signals
        avg_signal = (signals["signal_1"] + signals["signal_2"] + signals["signal_3"] + signals["signal_4"]) / 4
        predictions = ["BUY" if x > 0.6 else "SELL" if x < 0.4 else "HOLD" for x in avg_signal]
        confidences = np.abs(avg_signal - 0.5) * 2 # simple confidence metric
        
        return pd.DataFrame({
            **signals,
            "prediction": predictions,
            "confidence": confidences
        })
