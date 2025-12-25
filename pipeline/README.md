# VN Bank Advisor - Training Pipeline

Modular XGBoost training pipeline supporting 5 feature groups (Market, Technical, Sentiment, Macro, Fundamental).

## Prerequisites

1.  **Python 3.8+**
2.  **OpenMP** (Required for XGBoost on macOS):
    ```bash
    brew install libomp
    ```

## Installation

```bash
pip install -r requirements.txt
```

## Data Organization

To fully utilize the **5 Feature Groups**, place your CSV files in the `data/` directory.
Only `vn30_2015_2025.csv` (Market) is required. Others are optional but recommended for better models.

| Feature Group | Data Type | Filename | Expected Columns (Partial) |
| :--- | :--- | :--- | :--- |
| **A** (Market) | Market OHLCV | `vn30_2015_2025.csv` | `symbol`, `time`, `open`, `high`, `low`, `close`, `volume` |
| **B** (Technical) | (Generated) | N/A | (Calculated from Market data) |
| **C** (Sentiment) | Sentiment | `sentiment.csv` | `symbol`, `date`, `sentiment_lag_1`, `buzz_7d_lag1`... |
| **D** (Macro/FX) | Macro/FX | `macro.csv` | `date`/`quarter_date`, `GDP`, `INF`, `DC`, `fx_ret_5d`... |
| **E** (Fundamental)| Bank Data | `fundamental.csv` | `symbol`, `quarter_date`, `ROE`, `ROA`, `P_B`... |

*Note: You can change these paths in `pipeline/config.py`.*

## Feature Groups

-   **Group A**: Market Features (Momentum, Volatility)
-   **Group B**: Technical Indicators (RSI, ATR, BB)
-   **Group C**: Sentiment Analysis
-   **Group D**: Macroeconomic & FX
-   **Group E**: Bank Fundamentals

## Configuration

Edit `pipeline/config.py` to:
-   Toggle feature groups (`USE_GROUP_C = True/False`).
-   Enhance feature lists.
-   Change Targets (e.g. `RETURN_HORIZON = 63` for quarterly).
-   Tune XGBoost hyperparameters.

## Usage

### 1. Train Models
```bash
python3 -m pipeline.train_pipeline
```
This script will:
1.  Load and merge all available data files.
2.  Generate features for enabled groups.
3.  Train 4 XGBoost models (Return, Risk, Regime, Direction).
4.  Save models to `artifacts/`.

### 2. Run Inference
```bash
python3 -m pipeline.inference
```
