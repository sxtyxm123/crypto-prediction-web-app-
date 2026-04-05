"""
Enhanced LSTM Model Training Script for Cryptocurrency Price Prediction

This script trains LSTM models with improved error handling, validation,
and uses the modern Keras format (.keras instead of .h5).

Features:
- Comprehensive error handling and logging
- Modern .keras model format
- Enhanced visualization
- Model performance tracking
- Automatic hyperparameter configuration
"""

import os
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

from utils import (
    ConfigManager, LoggerSetup, DataValidator,
    FileManager, print_section_header, print_metrics, format_duration
)

# TensorFlow / Keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2

# Initialize configuration and logging
config = ConfigManager()
logger = LoggerSetup.setup_logger("model_training", log_dir=config.get("paths", "logs_dir", "logs"))

# Load configuration
SYMBOLS = config.get("data_collection", "symbols")
MAIN_DIR = config.get("paths", "main_dir")
MODELS_DIR = config.get("paths", "models_dir")
# Use percentage change as target to reduce overfitting
TARGET_COL = "target_pct_change"  # Changed from "target_next_close"
TEST_SIZE = config.get("model", "test_size")
SEQUENCE_LENGTH = config.get("model", "sequence_length")
EPOCHS = config.get("model", "epochs")
BATCH_SIZE = config.get("model", "batch_size")
RANDOM_STATE = config.get("model", "random_state")
VALIDATION_SPLIT = config.get("model", "validation_split")
ES_PATIENCE = config.get("model", "early_stopping_patience")
LSTM_UNITS = config.get("model", "lstm_units")
DROPOUT_RATE = config.get("model", "dropout_rate")

# Candidate features
CANDIDATE_FEATURES = [
    "open", "high", "low", "close", "volume",
    "SMA_20", "EMA_20", "RSI_14", "MACD", "MACD_signal",
    "BBM", "BBU", "BBL", "OBV",
    "return_1h", "return_3h", "return_6h",
    "vol_3h", "vol_6h", "vol_12h", "vol_24h",
    "close_lag_1", "close_lag_3", "close_lag_6",
    "close_lag_12", "close_lag_24",
    "volume_lag_1", "volume_lag_3", "volume_lag_6",
    "volume_lag_12", "volume_lag_24",
    "hour", "dayofweek", "day"
]

PRICE_COLS_FOR_OUTLIERS = ["open", "high", "low", "close", TARGET_COL]


def load_symbol_df(symbol: str) -> pd.DataFrame:
    """
    Load ML-ready CSV for a given symbol and sort by time.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        Loaded and sorted DataFrame
    """
    symbol_dir = os.path.join(MAIN_DIR, symbol)
    csv_path = FileManager.safe_file_path(symbol_dir, f"{symbol}_ML_ready.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found for {symbol}: {csv_path}")
    
    logger.info(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure datetime and sort
    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"])
        df = df.sort_values("open_time").reset_index(drop=True)
    
    logger.info(f"Loaded {len(df)} rows for {symbol}")
    return df


def clip_outliers_iqr(df: pd.DataFrame, cols: list, factor: float = 1.5) -> pd.DataFrame:
    """
    Winsorize selected numeric columns using IQR bounds.
    
    Args:
        df: Input DataFrame
        cols: Columns to clip
        factor: IQR multiplier for bounds
        
    Returns:
        DataFrame with clipped values
    """
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr
        df[col] = df[col].clip(lower, upper)
    
    logger.debug(f"Clipped outliers for {len(cols)} columns")
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add hour, dayofweek, day if 'open_time' is available.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with time features
    """
    df = df.copy()
    if "open_time" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["open_time"]):
        df["open_time"] = pd.to_datetime(df["open_time"])
    
    if "open_time" in df.columns:
        df["hour"] = df["open_time"].dt.hour
        df["dayofweek"] = df["open_time"].dt.dayofweek
        df["day"] = df["open_time"].dt.day
    
    return df


def prepare_features_and_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Prepare features and target for model training.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (X, y, feature_cols)
    """
    df = add_time_features(df)
    df = clip_outliers_iqr(df, PRICE_COLS_FOR_OUTLIERS)
    
    if TARGET_COL not in df.columns:
        raise ValueError(f"{TARGET_COL} not found in dataframe.")
    
    feature_cols = [c for c in CANDIDATE_FEATURES if c in df.columns]
    if not feature_cols:
        raise ValueError("No candidate features found in dataframe.")
    
    logger.info(f"Using {len(feature_cols)} features")
    
    df_model = df[feature_cols + [TARGET_COL]].dropna().reset_index(drop=True)
    
    X = df_model[feature_cols]
    y = df_model[TARGET_COL]
    
    return X, y, feature_cols


def time_series_train_test_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = TEST_SIZE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Deterministic time-based split (no shuffle).
    
    Args:
        X: Features DataFrame
        y: Target Series
        test_size: Proportion of test data
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    n = len(X)
    split_idx = int(n * (1 - test_size))
    
    X_train = X.iloc[:split_idx].copy()
    X_test = X.iloc[split_idx:].copy()
    y_train = y.iloc[:split_idx].copy()
    y_test = y.iloc[split_idx:].copy()
    
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    return X_train, X_test, y_train, y_test


def build_lstm_sequences(
    X_scaled: np.ndarray,
    y_scaled: np.ndarray,
    seq_len: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert 2D arrays into 3D sequences for LSTM.
    
    Args:
        X_scaled: Scaled features
        y_scaled: Scaled target
        seq_len: Sequence length
        
    Returns:
        Tuple of (X_seq, y_seq)
    """
    X_seq, y_seq = [], []
    for i in range(len(X_scaled) - seq_len):
        X_seq.append(X_scaled[i:i+seq_len])
        y_seq.append(y_scaled[i+seq_len])
    
    logger.debug(f"Created {len(X_seq)} sequences of length {seq_len}")
    return np.array(X_seq), np.array(y_seq)


def evaluate_regression(y_true, y_pred) -> Dict[str, float]:
    """
    Calculate regression metrics including directional accuracy.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Dictionary of metrics
    """
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # Calculate directional accuracy (important for trading)
    direction_true = np.sign(y_true[1:] - y_true[:-1])
    direction_pred = np.sign(y_pred[1:] - y_pred[:-1])
    directional_accuracy = np.mean(direction_true == direction_pred) * 100
    
    # Calculate MAPE
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
    
    return {
        "MSE": mse,
        "MAE": mae,
        "R2": r2,
        "MAPE": mape,
        "Directional_Accuracy": directional_accuracy
    }


def train_lstm_for_symbol(symbol: str) -> Dict[str, Any]:
    """
    Full LSTM pipeline for a single symbol.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        Dictionary with training results
    """
    print_section_header(f"Training LSTM for {symbol}")
    start_time = time.time()
    
    try:
        # Load and prepare data
        df = load_symbol_df(symbol)
        X, y, used_features = prepare_features_and_target(df)
        
        print(f"Total usable rows: {len(X)}")
        print(f"Features: {len(used_features)}")
        
        # Time-based split
        X_train_df, X_test_df, y_train_ser, y_test_ser = time_series_train_test_split(X, y)
        
        # Scaling
        scaler_X = MinMaxScaler()
        scaler_y = MinMaxScaler()
        
        X_train_scaled_2d = scaler_X.fit_transform(X_train_df.values)
        X_test_scaled_2d = scaler_X.transform(X_test_df.values)
        
        y_train_scaled_2d = scaler_y.fit_transform(y_train_ser.values.reshape(-1, 1))
        y_test_scaled_2d = scaler_y.transform(y_test_ser.values.reshape(-1, 1))
        
        # Build sequences
        X_train_seq, y_train_seq = build_lstm_sequences(
            X_train_scaled_2d, y_train_scaled_2d, SEQUENCE_LENGTH
        )
        X_test_seq, y_test_seq = build_lstm_sequences(
            X_test_scaled_2d, y_test_scaled_2d, SEQUENCE_LENGTH
        )
        
        print(f"X_train_seq shape: {X_train_seq.shape}")
        print(f"X_test_seq shape: {X_test_seq.shape}")
        
        n_features = X_train_seq.shape[-1]
        
        # Reduced model complexity to prevent overfitting
        # Using smaller LSTM units: [32, 16] instead of [64, 32]
        lstm_units_reduced = [32, 16]
        dropout_rate_high = 0.5  # Increased dropout
        l2_strength = 0.02  # Stronger regularization
        
        model = Sequential()
        model.add(Input(shape=(SEQUENCE_LENGTH, n_features)))
        
        # First LSTM layer with strong regularization
        model.add(LSTM(
            lstm_units_reduced[0],
            return_sequences=True,
            kernel_regularizer=l2(l2_strength),
            recurrent_regularizer=l2(l2_strength),
            bias_regularizer=l2(l2_strength)
        ))
        model.add(BatchNormalization())  # Add batch normalization
        model.add(Dropout(dropout_rate_high))
        
        # Second LSTM layer with strong regularization
        model.add(LSTM(
            lstm_units_reduced[1],
            kernel_regularizer=l2(l2_strength),
            recurrent_regularizer=l2(l2_strength),
            bias_regularizer=l2(l2_strength)
        ))
        model.add(BatchNormalization())  # Add batch normalization
        model.add(Dropout(dropout_rate_high))
        
        # Output layer
        model.add(Dense(1))
        
        model.compile(loss="mse", optimizer="adam")
        
        logger.info(f"Model architecture: LSTM({lstm_units_reduced[0]}) -> LSTM({lstm_units_reduced[1]}) -> Dense(1)")
        logger.info(f"Anti-overfitting measures: Dropout={dropout_rate_high}, L2={l2_strength}")
        
        # Enhanced callbacks for better overfitting prevention
        es = EarlyStopping(
            monitor="val_loss",
            patience=8,  # Increased patience for better convergence
            restore_best_weights=True,
            verbose=1
        )
        
        # Reduce learning rate when validation loss plateaus
        reduce_lr = ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1
        )
        
        # Increased batch size for more stable gradients
        batch_size_stable = 128
        validation_split_larger = 0.15  # Larger validation set
        
        # Train
        logger.info("Starting model training with anti-overfitting measures")
        logger.info(f"Batch size: {batch_size_stable}, Validation split: {validation_split_larger}")
        
        history = model.fit(
            X_train_seq, y_train_seq,
            validation_split=validation_split_larger,
            epochs=EPOCHS,
            batch_size=batch_size_stable,
            callbacks=[es, reduce_lr],
            verbose=1
        )
        
        # Predict
        y_pred_seq_scaled = model.predict(X_test_seq, verbose=0)
        
        # Inverse transform
        y_pred_seq = scaler_y.inverse_transform(y_pred_seq_scaled).ravel()
        y_test_seq_orig = scaler_y.inverse_transform(y_test_seq).ravel()
        
        # Evaluate
        metrics = evaluate_regression(y_test_seq_orig, y_pred_seq)
        
        print_metrics(metrics, f"LSTM Metrics for {symbol}")
        
        # Prepare output directory
        models_dir = FileManager.ensure_directory(MODELS_DIR)
        symbol_model_dir = FileManager.ensure_directory(os.path.join(models_dir, symbol))
        
        # Plot predictions
        plt.figure(figsize=(14, 6))
        plt.plot(y_test_seq_orig[:500], label="Actual Price", linewidth=2, alpha=0.8)
        plt.plot(y_pred_seq[:500], label="Predicted Price", linewidth=2, alpha=0.8)
        plt.title(f"LSTM Prediction vs Actual - {symbol}", fontsize=14, fontweight='bold')
        plt.xlabel("Time Step", fontsize=12)
        plt.ylabel("Price", fontsize=12)
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plot_path = FileManager.safe_file_path(symbol_model_dir, f"{symbol}_lstm_predictions.png")
        plt.savefig(plot_path, dpi=150)
        plt.close()
        
        logger.info(f"Saved prediction plot to: {plot_path}")
        
        # Plot training history to visualize overfitting
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Training Loss', linewidth=2)
        plt.plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
        plt.title(f'Model Loss - {symbol}', fontsize=14, fontweight='bold')
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel('Loss', fontsize=12)
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 2, 2)
        # Plot train vs validation gap
        gap = np.array(history.history['val_loss']) - np.array(history.history['loss'])
        plt.plot(gap, label='Val-Train Gap', linewidth=2, color='red')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.title(f'Overfitting Gap - {symbol}', fontsize=14, fontweight='bold')
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel('Loss Difference', fontsize=12)
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        history_plot_path = FileManager.safe_file_path(symbol_model_dir, f"{symbol}_training_history.png")
        plt.savefig(history_plot_path, dpi=150)
        plt.close()
        
        logger.info(f"Saved training history plot to: {history_plot_path}")
        
        # Save model in modern .keras format
        model_path = FileManager.safe_file_path(symbol_model_dir, f"{symbol}_lstm.keras")
        model.save(model_path)
        logger.info(f"Saved LSTM model to: {model_path}")
        
        # Save scalers and features
        try:
            import joblib
            joblib.dump(scaler_X, os.path.join(symbol_model_dir, f"{symbol}_scaler_X.pkl"))
            joblib.dump(scaler_y, os.path.join(symbol_model_dir, f"{symbol}_scaler_y.pkl"))
            joblib.dump(used_features, os.path.join(symbol_model_dir, f"{symbol}_features.pkl"))
            logger.info("Saved scalers and feature list")
        except ImportError:
            logger.warning("joblib not available; scalers not saved")
        
        duration = time.time() - start_time
        print(f"Training completed in {format_duration(duration)}")
        
        return {
            "symbol": symbol,
            "metrics": metrics,
            "model_path": model_path,
            "plot_path": plot_path,
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"Error training model for {symbol}: {e}", exc_info=True)
        print(f"✗ Error training {symbol}: {e}")
        raise


def main():
    """Main execution function."""
    print_section_header("LSTM Model Training")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Sequence Length: {SEQUENCE_LENGTH}")
    print(f"Epochs: {EPOCHS} (with early stopping)")
    print(f"Batch Size: {BATCH_SIZE}")
    
    overall_start = time.time()
    all_results = {}
    
    for sym in SYMBOLS:
        try:
            result = train_lstm_for_symbol(sym)
            all_results[sym] = result["metrics"]
        except Exception as e:
            logger.error(f"Failed to train model for {sym}: {e}")
            all_results[sym] = None
    
    # Summary
    print_section_header("Training Summary")
    successful = sum(1 for v in all_results.values() if v is not None)
    total = len(all_results)
    
    print(f"Successful: {successful}/{total}")
    print(f"Total time: {format_duration(time.time() - overall_start)}")
    
    for sym, metrics in all_results.items():
        if metrics:
            print(f"\n{sym}:")
            print_metrics(metrics)
        else:
            print(f"\n{sym}: ✗ Failed")
    
    logger.info(f"Model training completed: {successful}/{total} successful")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Model training interrupted by user")
        print("\n\nModel training interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in model training: {e}", exc_info=True)
        print(f"\n\nFatal error: {e}")
        raise
