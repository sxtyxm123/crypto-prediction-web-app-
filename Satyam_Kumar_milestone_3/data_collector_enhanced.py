"""
Enhanced Data Collection Script for Cryptocurrency Price Prediction

This script fetches OHLCV data from Binance API with improved error handling,
logging, and retry mechanisms.

Features:
- Automatic retry with exponential backoff
- Comprehensive logging
- Data validation
- Progress tracking
- Configuration-based parameters
"""

import os
import time
import requests
import pandas as pd
from typing import Optional, List
from utils import (
    ConfigManager, LoggerSetup, DataValidator, 
    RetryHandler, FileManager, print_section_header, format_duration
)

# Initialize configuration and logging
config = ConfigManager()
logger = LoggerSetup.setup_logger("data_collector", log_dir=config.get("paths", "logs_dir", "logs"))

# Load configuration
SYMBOLS = config.get("data_collection", "symbols")
INTERVAL = config.get("data_collection", "interval")
START_DATE = config.get("data_collection", "start_date")
END_DATE = config.get("data_collection", "end_date")
BASE_URL = config.get("data_collection", "base_url")
API_LIMIT = config.get("data_collection", "api_limit")
REQUEST_DELAY = config.get("data_collection", "request_delay")
MAX_RETRIES = config.get("data_collection", "max_retries")
RETRY_DELAY = config.get("data_collection", "retry_delay")
MAIN_DIR = config.get("paths", "main_dir")

# Technical indicator configuration
TECH_CONFIG = config.get("technical_indicators")


def to_ms(date_str: str) -> int:
    """
    Convert YYYY-MM-DD to milliseconds timestamp.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Timestamp in milliseconds
    """
    return int(pd.Timestamp(date_str).timestamp() * 1000)


def get_binance_ohlcv(symbol: str, interval: str, start_time: int, end_time: int) -> pd.DataFrame:
    """
    Download OHLCV data from Binance using pagination with retry logic.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        interval: Candle interval (e.g., '1h')
        start_time: Start timestamp in milliseconds
        end_time: End timestamp in milliseconds
        
    Returns:
        DataFrame with OHLCV data
        
    Raises:
        Exception: If all retry attempts fail
    """
    url = f"{BASE_URL}/api/v3/klines"
    all_data = []
    start = start_time
    
    logger.info(f"Fetching data for {symbol} from {pd.Timestamp(start_time, unit='ms')} to {pd.Timestamp(end_time, unit='ms')}")
    
    request_count = 0
    
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start,
            "endTime": end_time,
            "limit": API_LIMIT
        }
        
        def make_request():
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            # Use retry handler for API call
            data = RetryHandler.retry_with_backoff(
                make_request,
                max_retries=MAX_RETRIES,
                initial_delay=RETRY_DELAY,
                logger=logger
            )
            
            if not data:
                logger.info(f"No more data available for {symbol}")
                break
            
            all_data.extend(data)
            request_count += 1
            
            # Update start time for next batch
            start = data[-1][0] + 1
            
            # Log progress
            current_time = pd.Timestamp(data[-1][0], unit='ms')
            logger.debug(f"Fetched batch {request_count}: up to {current_time}")
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {e}")
            raise
    
    logger.info(f"Fetched {len(all_data)} candles for {symbol} in {request_count} requests")
    
    # Convert to DataFrame
    cols = [
        "open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_asset_volume", "trades", "taker_buy_volume",
        "taker_buy_quote_volume", "ignore"
    ]
    
    df = pd.DataFrame(all_data, columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    
    float_cols = ["open", "high", "low", "close", "volume",
                  "quote_asset_volume", "taker_buy_volume", "taker_buy_quote_volume"]
    
    for col in float_cols:
        df[col] = df[col].astype(float)
    
    df["trades"] = df["trades"].astype(int)
    
    return df


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to OHLCV data.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added technical indicators
    """
    logger.info("Adding technical indicators")
    
    close = df["close"]
    volume = df["volume"]
    
    # Moving averages
    df["SMA_20"] = close.rolling(TECH_CONFIG["sma_period"]).mean()
    df["EMA_20"] = close.ewm(span=TECH_CONFIG["ema_period"], adjust=False).mean()
    
    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(TECH_CONFIG["rsi_period"]).mean()
    avg_loss = loss.rolling(TECH_CONFIG["rsi_period"]).mean()
    rs = avg_gain / avg_loss
    
    df["RSI_14"] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = close.ewm(span=TECH_CONFIG["macd_fast"], adjust=False).mean()
    ema26 = close.ewm(span=TECH_CONFIG["macd_slow"], adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=TECH_CONFIG["macd_signal"], adjust=False).mean()
    
    # Bollinger Bands
    df["BBM"] = close.rolling(TECH_CONFIG["bb_period"]).mean()
    std_20 = close.rolling(TECH_CONFIG["bb_period"]).std()
    df["BBU"] = df["BBM"] + TECH_CONFIG["bb_std"] * std_20
    df["BBL"] = df["BBM"] - TECH_CONFIG["bb_std"] * std_20
    
    # OBV (On-Balance Volume)
    obv = [0]
    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    
    df["OBV"] = obv
    
    logger.info("Technical indicators added successfully")
    return df


def add_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add machine learning features including lag features, returns, and volatility.
    
    Args:
        df: DataFrame with OHLCV and technical indicators
        
    Returns:
        DataFrame with added ML features
    """
    logger.info("Adding ML features")
    
    # Lag features
    for lag in TECH_CONFIG["lag_periods"]:
        df[f"close_lag_{lag}"] = df["close"].shift(lag)
        df[f"volume_lag_{lag}"] = df["volume"].shift(lag)
    
    # Returns
    df["return_1h"] = df["close"].pct_change(1)
    df["return_3h"] = df["close"].pct_change(3)
    df["return_6h"] = df["close"].pct_change(6)
    
    # Volatility
    for w in TECH_CONFIG["volatility_windows"]:
        df[f"vol_{w}h"] = df["close"].rolling(w).std()
    
    # Target 1: Next close price (original)
    df["target_next_close"] = df["close"].shift(-1)
    
    # Target 2: Price change (absolute)
    df["target_price_change"] = df["close"].shift(-1) - df["close"]
    
    # Target 3: Percentage change (better for learning patterns)
    df["target_pct_change"] = ((df["close"].shift(-1) - df["close"]) / df["close"]) * 100
    
    # Target 4: Multi-step ahead (4 hours)
    df["target_4h_ahead"] = df["close"].shift(-4)
    df["target_4h_pct_change"] = ((df["close"].shift(-4) - df["close"]) / df["close"]) * 100
    
    # Target 5: Direction (binary classification)
    df["target_up_down"] = (df["target_next_close"] > df["close"]).astype(int)
    
    logger.debug("Added ML features and multiple target variables")
    return df


def process_symbol(symbol: str) -> Optional[pd.DataFrame]:
    """
    Download, process, and save data for a single symbol.
    
    Args:
        symbol: Trading pair symbol
        
    Returns:
        Processed DataFrame or None if error occurs
    """
    print_section_header(f"Processing {symbol}")
    start_time = time.time()
    
    try:
        # Validate symbol
        DataValidator.validate_symbol(symbol, SYMBOLS)
        
        # Validate date range
        DataValidator.validate_date_range(START_DATE, END_DATE)
        
        # Create directories
        main_dir = FileManager.ensure_directory(MAIN_DIR)
        symbol_dir = FileManager.ensure_directory(os.path.join(main_dir, symbol))
        
        # Convert dates to milliseconds
        start_ms = to_ms(START_DATE)
        end_ms = to_ms(END_DATE)
        
        # Fetch data
        df = get_binance_ohlcv(symbol, INTERVAL, start_ms, end_ms)
        
        # Add features
        df = add_technical_indicators(df)
        df = add_ml_features(df)
        
        # Remove NaN rows
        initial_rows = len(df)
        df = df.dropna().reset_index(drop=True)
        final_rows = len(df)
        
        logger.info(f"Removed {initial_rows - final_rows} rows with NaN values")
        
        # Validate final data
        required_cols = ["open", "high", "low", "close", "volume", "target_next_close"]
        DataValidator.validate_dataframe(df, required_cols, min_rows=100)
        
        # Save to CSV
        file_path = FileManager.safe_file_path(symbol_dir, f"{symbol}_ML_ready.csv")
        df.to_csv(file_path, index=False)
        
        file_size = FileManager.get_file_size_mb(file_path)
        duration = time.time() - start_time
        
        logger.info(f"Saved: {file_path}")
        logger.info(f"Shape: {df.shape}, Size: {file_size:.2f} MB")
        logger.info(f"Processing time: {format_duration(duration)}")
        
        print(f"✓ Saved: {file_path}")
        print(f"  Shape: {df.shape}")
        print(f"  Size: {file_size:.2f} MB")
        print(f"  Time: {format_duration(duration)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}", exc_info=True)
        print(f"✗ Error processing {symbol}: {e}")
        return None


def main():
    """Main execution function."""
    print_section_header("Cryptocurrency Data Collection")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Interval: {INTERVAL}")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    
    overall_start = time.time()
    results = {}
    
    for sym in SYMBOLS:
        df = process_symbol(sym)
        results[sym] = df is not None
        time.sleep(0.5)  # Brief pause between symbols
    
    # Summary
    print_section_header("Collection Summary")
    successful = sum(results.values())
    total = len(results)
    
    print(f"Successful: {successful}/{total}")
    print(f"Total time: {format_duration(time.time() - overall_start)}")
    
    for sym, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {sym}")
    
    logger.info(f"Data collection completed: {successful}/{total} successful")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Data collection interrupted by user")
        print("\n\nData collection interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in data collection: {e}", exc_info=True)
        print(f"\n\nFatal error: {e}")
        raise
