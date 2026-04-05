"""
Enhanced Data Preprocessing Script for Cryptocurrency Price Prediction

This script prepares collected data for machine learning with improved
error handling, validation, and logging.

Features:
- Comprehensive data validation
- Configurable feature selection
- Proper train-test splitting
- Feature scaling with MinMaxScaler
- Detailed logging and progress tracking
"""

import os
import pandas as pd
from typing import Tuple, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from utils import (
    ConfigManager, LoggerSetup, DataValidator,
    FileManager, print_section_header, print_metrics
)

# Initialize configuration and logging
config = ConfigManager()
logger = LoggerSetup.setup_logger("data_preprocessing", log_dir=config.get("paths", "logs_dir", "logs"))

# Load configuration
SYMBOLS = config.get("data_collection", "symbols")
MAIN_DIR = config.get("paths", "main_dir")
DF_FEATURES = config.get("preprocessing", "features")
TARGET = config.get("preprocessing", "target")
TIME_COLS = config.get("preprocessing", "time_columns")
TEST_SIZE = config.get("preprocessing", "test_size")
RANDOM_STATE = config.get("preprocessing", "random_state")


def ensure_time_and_lags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure hour/dayofweek/day and 1-step lag features exist.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with time and lag features
    """
    logger.info("Ensuring time and lag features exist")
    
    # Ensure open_time is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["open_time"]):
        df["open_time"] = pd.to_datetime(df["open_time"])
    
    # Time features
    if "hour" not in df.columns:
        df["hour"] = df["open_time"].dt.hour
        logger.debug("Added 'hour' feature")
    
    if "dayofweek" not in df.columns:
        df["dayofweek"] = df["open_time"].dt.dayofweek
        logger.debug("Added 'dayofweek' feature")
    
    if "day" not in df.columns:
        df["day"] = df["open_time"].dt.day
        logger.debug("Added 'day' feature")
    
    # Lag features (1-step)
    if "close_lag_1" not in df.columns:
        df["close_lag_1"] = df["close"].shift(1)
        logger.debug("Added 'close_lag_1' feature")
    
    if "volume_lag_1" not in df.columns:
        df["volume_lag_1"] = df["volume"].shift(1)
        logger.debug("Added 'volume_lag_1' feature")
    
    return df


def preprocess_symbol(symbol: str) -> Tuple:
    """
    Preprocess data for a single symbol.
    
    Steps:
    1. Load CSV
    2. Ensure time/lag features
    3. Select features + target
    4. Train-test split
    5. Scale features (except time cols) and target
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        Tuple of (X_train_final, X_test_final, y_train_scaled, y_test_scaled)
        
    Raises:
        FileNotFoundError: If CSV file not found
        ValueError: If required columns missing
    """
    print_section_header(f"Processing {symbol}")
    
    try:
        # Validate symbol
        DataValidator.validate_symbol(symbol, SYMBOLS)
        
        # Path to CSV
        symbol_dir = os.path.join(MAIN_DIR, symbol)
        csv_path = FileManager.safe_file_path(symbol_dir, f"{symbol}_ML_ready.csv")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV not found for {symbol}: {csv_path}")
        
        logger.info(f"Loading data from {csv_path}")
        
        # Load data
        df = pd.read_csv(csv_path)
        initial_rows = len(df)
        logger.info(f"Loaded {initial_rows} rows")
        
        # Ensure time features + lag features
        df = ensure_time_and_lags(df)
        
        # Validate target column exists
        if TARGET not in df.columns:
            raise ValueError(
                f"'{TARGET}' column not found in {symbol} dataset. "
                "Make sure the collection script created 'target_next_close'."
            )
        
        # Drop rows where any of the selected features or target is NaN
        df_model = df.dropna(subset=DF_FEATURES + [TARGET]).reset_index(drop=True)
        final_rows = len(df_model)
        
        logger.info(f"After removing NaN: {final_rows} rows ({initial_rows - final_rows} removed)")
        
        # Validate minimum rows
        DataValidator.validate_dataframe(df_model, DF_FEATURES + [TARGET], min_rows=1000)
        
        # Split into X (features) and y (target)
        X = df_model[DF_FEATURES].copy()
        y = df_model[TARGET].copy()
        
        logger.info(f"Features: {DF_FEATURES}")
        logger.info(f"Target: {TARGET}")
        
        # Train-test split (time-series aware: no shuffle)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=TEST_SIZE,
            shuffle=False,
            random_state=RANDOM_STATE
        )
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Scale features (except time columns)
        scale_cols = [col for col in DF_FEATURES if col not in TIME_COLS]
        logger.info(f"Scaling columns: {scale_cols}")
        
        scaler_X = MinMaxScaler()
        scaler_X.fit(X_train[scale_cols])
        
        # Create copies to avoid changing original X_train/X_test
        X_train_final = X_train.copy()
        X_test_final = X_test.copy()
        
        X_train_final[scale_cols] = scaler_X.transform(X_train[scale_cols])
        X_test_final[scale_cols] = scaler_X.transform(X_test[scale_cols])
        
        # Scale target
        scaler_y = MinMaxScaler()
        y_train_arr = y_train.values.reshape(-1, 1)
        y_test_arr = y_test.values.reshape(-1, 1)
        
        scaler_y.fit(y_train_arr)
        y_train_scaled = scaler_y.transform(y_train_arr)
        y_test_scaled = scaler_y.transform(y_test_arr)
        
        # Print shapes
        print(f"{symbol} ->")
        print(f"  X_train_final: {X_train_final.shape}")
        print(f"  X_test_final : {X_test_final.shape}")
        print(f"  y_train_scaled: {y_train_scaled.shape}")
        print(f"  y_test_scaled : {y_test_scaled.shape}")
        
        logger.info(f"Preprocessing completed successfully for {symbol}")
        
        # Optionally save scalers for later use
        try:
            import joblib
            scaler_dir = FileManager.ensure_directory(os.path.join(symbol_dir, "scalers"))
            joblib.dump(scaler_X, os.path.join(scaler_dir, f"{symbol}_scaler_X.pkl"))
            joblib.dump(scaler_y, os.path.join(scaler_dir, f"{symbol}_scaler_y.pkl"))
            logger.info(f"Saved scalers to {scaler_dir}")
        except ImportError:
            logger.warning("joblib not available, scalers not saved")
        
        return X_train_final, X_test_final, y_train_scaled, y_test_scaled
        
    except Exception as e:
        logger.error(f"Error while processing {symbol}: {e}", exc_info=True)
        print(f"✗ Error while processing {symbol}: {e}")
        raise


def main():
    """Main execution function."""
    print_section_header("Cryptocurrency Data Preprocessing")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Test size: {TEST_SIZE * 100}%")
    print(f"Features: {len(DF_FEATURES)}")
    
    results = {}
    
    for sym in SYMBOLS:
        try:
            result = preprocess_symbol(sym)
            results[sym] = "Success"
        except Exception as e:
            results[sym] = f"Failed: {str(e)[:50]}"
    
    # Summary
    print_section_header("Preprocessing Summary")
    successful = sum(1 for v in results.values() if v == "Success")
    total = len(results)
    
    print(f"Successful: {successful}/{total}")
    
    for sym, status in results.items():
        if status == "Success":
            print(f"  ✓ {sym}")
        else:
            print(f"  ✗ {sym}: {status}")
    
    logger.info(f"Preprocessing completed: {successful}/{total} successful")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Preprocessing interrupted by user")
        print("\n\nPreprocessing interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in preprocessing: {e}", exc_info=True)
        print(f"\n\nFatal error: {e}")
        raise
