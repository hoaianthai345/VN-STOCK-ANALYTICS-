import os

# --- Paths ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts")

# --- Data Paths ---
MARKET_DATA_PATH = os.path.join(DATA_DIR, "vn30_2015_2025.csv")
BANK_RATIO_DATA_PATH = os.path.join(DATA_DIR, "bank.xlsx")
MACRO_DATA_PATH = os.path.join(DATA_DIR, "macro.xlsx")
FUNDAMENTAL_DATA_PATH = os.path.join(DATA_DIR, "data_with_metadata.xlsx")
SENTIMENT_DATA_PATH = os.path.join(DATA_DIR, "VN30_Daily_Features.csv")
FX_DATA_PATH = os.path.join(DATA_DIR, "usd_vnd_full_2015_raw.csv")

# --- Column Mappings (Inferred/Default) ---
BANK_RATIO_COL_MAPPING = {
    # Add mappings if source columns differ from target
}
BANK_RATIO_NUMERIC_COLS = ["roa", "roe", "nim", "cir", "ldr", "bad_debt"]

FUNDAMENTAL_COL_MAPPING = {
    "CP": "symbol",
    "Năm": "year",
    "Kỳ": "quarter",
    "ROE (%)": "ROE"
}

# --- Feature Groups ---
# Group A: Market Features (from OHLCV)
GROUP_A_MARKET = [
    "ret_1d", "ret_5d", "ret_21d",
    "vol_5d", "vol_21d",
    "high_low_range",
    "close_vs_ma21", "close_vs_ma63"
]

# Group B: Technical Indicators
GROUP_B_TECHNICAL = [
    "RSI_14",
    "ATR_14_pct",  # ATR scaled by price
    "BB_width"
]

# Group C: Sentiment Features (from News)
GROUP_C_SENTIMENT = [
    "sentiment_lag_1", "sentiment_lag_3", "sentiment_lag_7",
    "sentiment_7d_avg_lag1",
    "buzz_7d_lag1",
    "sentiment_decay_lag1"
]

# Group D: Macro Features (Quarterly -> Daily)
GROUP_D_MACRO = [
    "GDP_t_1Q", "INF_t_1Q", "DC_t_1Q",  # Lagged 1 quarter
    "fx_ret_5d", "fx_vol_21d"           # FX context
]

# Group E: Bank Fundamentals (Quarterly -> Daily, standardized per bank)
GROUP_E_BANK = [
    "ROE_z", "ROA_z", "P_B_z", "LDR_z", "CIR_z", "Assets_Equity_z"
]

# All Features
FEATURE_COLS = GROUP_A_MARKET + GROUP_B_TECHNICAL + GROUP_C_SENTIMENT + GROUP_D_MACRO + GROUP_E_BANK

# Core Features (Minimal set required for model to run if others missing)
CORE_FEATURES = GROUP_A_MARKET + GROUP_B_TECHNICAL

# --- Target ---
TARGET_COL = "log_return_21d"
PREDICTION_HORIZON = 21

# --- Model Params (XGBoost) ---
XGB_PARAMS = {
    "n_estimators": 100,
    "learning_rate": 0.05,
    "max_depth": 5,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "n_jobs": -1,
    "random_state": 42
}

# Distinct params for each model type if needed
XGB_PARAMS_RETURN = XGB_PARAMS.copy()
XGB_PARAMS_RETURN["objective"] = "reg:squarederror"

XGB_PARAMS_RISK = XGB_PARAMS.copy()
XGB_PARAMS_RISK["objective"] = "reg:squarederror"

XGB_PARAMS_REGIME = XGB_PARAMS.copy()
XGB_PARAMS_REGIME["objective"] = "multi:softprob"
XGB_PARAMS_REGIME["num_class"] = 3 # Bull, Bear, Neutral (Example)

XGB_PARAMS_DIRECTION = XGB_PARAMS.copy()
XGB_PARAMS_DIRECTION["objective"] = "binary:logistic"

# --- Training Config ---
START_TRAIN_DATE = "2015-01-01"
FIRST_TEST_YEAR = 2020
MIN_TEST_ROWS = 200
