# API Reference

## Table of Contents
1. [Utility Functions](#utility-functions)
2. [Data Collection Functions](#data-collection-functions)
3. [Preprocessing Functions](#preprocessing-functions)
4. [Model Training Functions](#model-training-functions)
5. [Usage Examples](#usage-examples)

## Utility Functions

### ConfigManager

Configuration management class for loading and accessing system settings.

#### `__init__(config_path: str = "config.json")`

Initialize configuration manager.

**Parameters**:
- `config_path` (str): Path to configuration JSON file. Default: "config.json"

**Raises**:
- `FileNotFoundError`: If configuration file doesn't exist
- `ValueError`: If JSON is invalid

**Example**:
```python
from utils import ConfigManager

config = ConfigManager("config.json")
```

#### `get(section: str, key: Optional[str] = None, default: Any = None) -> Any`

Get configuration value.

**Parameters**:
- `section` (str): Configuration section name
- `key` (Optional[str]): Key within section. If None, returns entire section
- `default` (Any): Default value if not found

**Returns**:
- Configuration value or default

**Example**:
```python
symbols = config.get("data_collection", "symbols")
# Returns: ["BTCUSDT", "ETHUSDT", ...]

all_model_config = config.get("model")
# Returns: {"epochs": 40, "batch_size": 64, ...}
```

---

### LoggerSetup

Logging configuration class.

#### `setup_logger(name: str, log_dir: str = "logs", level: str = "INFO", console: bool = True, file_logging: bool = True) -> logging.Logger`

Set up logger with file and console handlers.

**Parameters**:
- `name` (str): Logger name
- `log_dir` (str): Directory for log files. Default: "logs"
- `level` (str): Logging level ("DEBUG", "INFO", "WARNING", "ERROR"). Default: "INFO"
- `console` (bool): Enable console logging. Default: True
- `file_logging` (bool): Enable file logging. Default: True

**Returns**:
- `logging.Logger`: Configured logger instance

**Example**:
```python
from utils import LoggerSetup

logger = LoggerSetup.setup_logger(
    name="my_module",
    log_dir="logs",
    level="DEBUG"
)

logger.info("Processing started")
logger.error("An error occurred")
```

---

### DataValidator

Data validation utilities.

#### `validate_dataframe(df: pd.DataFrame, required_columns: List[str], min_rows: int = 1) -> bool`

Validate DataFrame has required columns and minimum rows.

**Parameters**:
- `df` (pd.DataFrame): DataFrame to validate
- `required_columns` (List[str]): List of required column names
- `min_rows` (int): Minimum number of rows required. Default: 1

**Returns**:
- `bool`: True if valid

**Raises**:
- `ValueError`: If validation fails

**Example**:
```python
from utils import DataValidator

DataValidator.validate_dataframe(
    df,
    required_columns=["open", "high", "low", "close"],
    min_rows=1000
)
```

#### `validate_date_range(start_date: str, end_date: str) -> bool`

Validate date range is logical.

**Parameters**:
- `start_date` (str): Start date in YYYY-MM-DD format
- `end_date` (str): End date in YYYY-MM-DD format

**Returns**:
- `bool`: True if valid

**Raises**:
- `ValueError`: If dates are invalid or illogical

**Example**:
```python
DataValidator.validate_date_range("2020-01-01", "2025-01-01")  # Valid
DataValidator.validate_date_range("2025-01-01", "2020-01-01")  # Raises ValueError
```

#### `validate_symbol(symbol: str, valid_symbols: List[str]) -> bool`

Validate cryptocurrency symbol.

**Parameters**:
- `symbol` (str): Symbol to validate
- `valid_symbols` (List[str]): List of valid symbols

**Returns**:
- `bool`: True if valid

**Raises**:
- `ValueError`: If symbol is invalid

**Example**:
```python
DataValidator.validate_symbol("BTCUSDT", ["BTCUSDT", "ETHUSDT"])  # Valid
DataValidator.validate_symbol("INVALID", ["BTCUSDT", "ETHUSDT"])  # Raises ValueError
```

---

### RetryHandler

Retry logic for API calls and operations.

#### `retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0, logger: Optional[logging.Logger] = None)`

Retry function with exponential backoff.

**Parameters**:
- `func`: Function to retry (callable with no arguments)
- `max_retries` (int): Maximum number of retry attempts. Default: 3
- `initial_delay` (float): Initial delay in seconds. Default: 1.0
- `backoff_factor` (float): Multiplier for delay after each retry. Default: 2.0
- `logger` (Optional[logging.Logger]): Logger for retry messages

**Returns**:
- Function result if successful

**Raises**:
- Last exception if all retries fail

**Example**:
```python
from utils import RetryHandler

def fetch_data():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

data = RetryHandler.retry_with_backoff(
    fetch_data,
    max_retries=5,
    initial_delay=1.0,
    backoff_factor=2.0
)
```

---

### FileManager

Safe file operations.

#### `ensure_directory(path: str) -> str`

Ensure directory exists, create if necessary.

**Parameters**:
- `path` (str): Directory path

**Returns**:
- `str`: Absolute path to directory

**Example**:
```python
from utils import FileManager

data_dir = FileManager.ensure_directory("crypto_data/BTCUSDT")
# Creates directory if it doesn't exist, returns absolute path
```

#### `safe_file_path(directory: str, filename: str) -> str`

Create safe file path preventing directory traversal.

**Parameters**:
- `directory` (str): Base directory
- `filename` (str): File name

**Returns**:
- `str`: Safe absolute file path

**Raises**:
- `ValueError`: If path is unsafe (e.g., contains "../")

**Example**:
```python
safe_path = FileManager.safe_file_path("crypto_data", "BTCUSDT_data.csv")
# Returns: "C:/Users/.../crypto_data/BTCUSDT_data.csv"

# This would raise ValueError:
FileManager.safe_file_path("crypto_data", "../../../etc/passwd")
```

#### `get_file_size_mb(file_path: str) -> float`

Get file size in megabytes.

**Parameters**:
- `file_path` (str): Path to file

**Returns**:
- `float`: File size in MB

**Example**:
```python
size = FileManager.get_file_size_mb("crypto_data/BTCUSDT/BTCUSDT_ML_ready.csv")
print(f"File size: {size:.2f} MB")
```

---

## Data Collection Functions

### `to_ms(date_str: str) -> int`

Convert YYYY-MM-DD to milliseconds timestamp.

**Parameters**:
- `date_str` (str): Date string in YYYY-MM-DD format

**Returns**:
- `int`: Timestamp in milliseconds

**Example**:
```python
timestamp = to_ms("2024-01-15")
# Returns: 1705276800000
```

---

### `get_binance_ohlcv(symbol: str, interval: str, start_time: int, end_time: int) -> pd.DataFrame`

Download OHLCV data from Binance using pagination with retry logic.

**Parameters**:
- `symbol` (str): Trading pair symbol (e.g., "BTCUSDT")
- `interval` (str): Candle interval (e.g., "1h", "1d")
- `start_time` (int): Start timestamp in milliseconds
- `end_time` (int): End timestamp in milliseconds

**Returns**:
- `pd.DataFrame`: DataFrame with OHLCV data

**Raises**:
- `requests.exceptions.RequestException`: If API request fails after retries
- `Exception`: For other unexpected errors

**Example**:
```python
start_ms = to_ms("2024-01-01")
end_ms = to_ms("2024-01-31")

df = get_binance_ohlcv("BTCUSDT", "1h", start_ms, end_ms)
print(df.head())
```

---

### `add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame`

Add technical indicators to OHLCV data.

**Parameters**:
- `df` (pd.DataFrame): DataFrame with OHLCV data

**Returns**:
- `pd.DataFrame`: DataFrame with added technical indicators

**Indicators Added**:
- SMA_20, EMA_20, RSI_14, MACD, MACD_signal
- BBM, BBU, BBL (Bollinger Bands)
- OBV (On-Balance Volume)

**Example**:
```python
df = add_technical_indicators(df)
print(df[['close', 'SMA_20', 'RSI_14']].head())
```

---

### `add_ml_features(df: pd.DataFrame) -> pd.DataFrame`

Add machine learning features including lag features, returns, and volatility.

**Parameters**:
- `df` (pd.DataFrame): DataFrame with OHLCV and technical indicators

**Returns**:
- `pd.DataFrame`: DataFrame with added ML features

**Features Added**:
- Lag features: close_lag_1, close_lag_3, ..., close_lag_24
- Returns: return_1h, return_3h, return_6h
- Volatility: vol_3h, vol_6h, vol_12h, vol_24h
- Targets: target_next_close, target_up_down

**Example**:
```python
df = add_ml_features(df)
print(df[['close', 'close_lag_1', 'return_1h', 'target_next_close']].head())
```

---

### `process_symbol(symbol: str) -> Optional[pd.DataFrame]`

Download, process, and save data for a single symbol.

**Parameters**:
- `symbol` (str): Trading pair symbol

**Returns**:
- `Optional[pd.DataFrame]`: Processed DataFrame or None if error occurs

**Side Effects**:
- Creates directory for symbol
- Saves CSV file with processed data
- Logs progress and errors

**Example**:
```python
df = process_symbol("BTCUSDT")
if df is not None:
    print(f"Successfully processed {len(df)} rows")
```

---

## Preprocessing Functions

### `ensure_time_and_lags(df: pd.DataFrame) -> pd.DataFrame`

Ensure hour/dayofweek/day and 1-step lag features exist.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame

**Returns**:
- `pd.DataFrame`: DataFrame with time and lag features

**Features Added (if missing)**:
- hour, dayofweek, day
- close_lag_1, volume_lag_1

**Example**:
```python
df = ensure_time_and_lags(df)
print(df[['open_time', 'hour', 'dayofweek', 'close_lag_1']].head())
```

---

### `preprocess_symbol(symbol: str) -> Tuple`

Preprocess data for a single symbol.

**Parameters**:
- `symbol` (str): Trading pair symbol

**Returns**:
- `Tuple`: (X_train_final, X_test_final, y_train_scaled, y_test_scaled)
  - X_train_final (pd.DataFrame): Scaled training features
  - X_test_final (pd.DataFrame): Scaled test features
  - y_train_scaled (np.ndarray): Scaled training target
  - y_test_scaled (np.ndarray): Scaled test target

**Raises**:
- `FileNotFoundError`: If CSV file not found
- `ValueError`: If required columns missing

**Side Effects**:
- Saves scaler objects to disk (if joblib available)

**Example**:
```python
X_train, X_test, y_train, y_test = preprocess_symbol("BTCUSDT")
print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")
```

---

## Model Training Functions

### `load_symbol_df(symbol: str) -> pd.DataFrame`

Load ML-ready CSV for a given symbol and sort by time.

**Parameters**:
- `symbol` (str): Trading pair symbol

**Returns**:
- `pd.DataFrame`: Loaded and sorted DataFrame

**Raises**:
- `FileNotFoundError`: If CSV file not found

**Example**:
```python
df = load_symbol_df("BTCUSDT")
print(f"Loaded {len(df)} rows for BTCUSDT")
```

---

### `clip_outliers_iqr(df: pd.DataFrame, cols: list, factor: float = 1.5) -> pd.DataFrame`

Winsorize selected numeric columns using IQR bounds.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame
- `cols` (list): Columns to clip
- `factor` (float): IQR multiplier for bounds. Default: 1.5

**Returns**:
- `pd.DataFrame`: DataFrame with clipped values

**Example**:
```python
df = clip_outliers_iqr(df, ["open", "high", "low", "close"], factor=1.5)
```

---

### `add_time_features(df: pd.DataFrame) -> pd.DataFrame`

Add hour, dayofweek, day if 'open_time' is available.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame

**Returns**:
- `pd.DataFrame`: DataFrame with time features

**Example**:
```python
df = add_time_features(df)
print(df[['open_time', 'hour', 'dayofweek', 'day']].head())
```

---

### `prepare_features_and_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]`

Prepare features and target for model training.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame

**Returns**:
- `Tuple`: (X, y, feature_cols)
  - X (pd.DataFrame): Features
  - y (pd.Series): Target
  - feature_cols (list): List of feature column names

**Raises**:
- `ValueError`: If target column not found or no features available

**Example**:
```python
X, y, features = prepare_features_and_target(df)
print(f"Features: {features}")
print(f"Samples: {len(X)}")
```

---

### `time_series_train_test_split(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> Tuple`

Deterministic time-based split (no shuffle).

**Parameters**:
- `X` (pd.DataFrame): Features DataFrame
- `y` (pd.Series): Target Series
- `test_size` (float): Proportion of test data. Default: 0.2

**Returns**:
- `Tuple`: (X_train, X_test, y_train, y_test)

**Example**:
```python
X_train, X_test, y_train, y_test = time_series_train_test_split(X, y, test_size=0.2)
```

---

### `build_lstm_sequences(X_scaled: np.ndarray, y_scaled: np.ndarray, seq_len: int) -> Tuple[np.ndarray, np.ndarray]`

Convert 2D arrays into 3D sequences for LSTM.

**Parameters**:
- `X_scaled` (np.ndarray): Scaled features (2D)
- `y_scaled` (np.ndarray): Scaled target (2D)
- `seq_len` (int): Sequence length

**Returns**:
- `Tuple`: (X_seq, y_seq)
  - X_seq (np.ndarray): 3D array of shape (n_sequences, seq_len, n_features)
  - y_seq (np.ndarray): 2D array of shape (n_sequences, 1)

**Example**:
```python
X_seq, y_seq = build_lstm_sequences(X_scaled, y_scaled, seq_len=48)
print(f"Sequence shape: {X_seq.shape}")  # (n, 48, features)
```

---

### `evaluate_regression(y_true, y_pred) -> Dict[str, float]`

Calculate regression metrics.

**Parameters**:
- `y_true`: True values
- `y_pred`: Predicted values

**Returns**:
- `Dict[str, float]`: Dictionary with keys "MSE", "MAE", "R2"

**Example**:
```python
metrics = evaluate_regression(y_test, y_pred)
print(f"MSE: {metrics['MSE']:.2f}")
print(f"MAE: {metrics['MAE']:.2f}")
print(f"R²: {metrics['R2']:.4f}")
```

---

### `train_lstm_for_symbol(symbol: str) -> Dict[str, Any]`

Full LSTM pipeline for a single symbol.

**Parameters**:
- `symbol` (str): Trading pair symbol

**Returns**:
- `Dict[str, Any]`: Dictionary with keys:
  - "symbol": Symbol name
  - "metrics": Performance metrics dict
  - "model_path": Path to saved model
  - "plot_path": Path to prediction plot
  - "duration": Training duration in seconds

**Raises**:
- Various exceptions for data loading, training errors

**Side Effects**:
- Saves trained model (.keras file)
- Saves scalers and feature list (.pkl files)
- Saves prediction plot (.png file)
- Logs training progress

**Example**:
```python
result = train_lstm_for_symbol("BTCUSDT")
print(f"Model saved to: {result['model_path']}")
print(f"Metrics: {result['metrics']}")
```

---

## Usage Examples

### Complete Pipeline Example

```python
# 1. Data Collection
from data_collector_enhanced import process_symbol

df = process_symbol("BTCUSDT")
print(f"Collected {len(df)} rows")

# 2. Preprocessing
from data_preprocessing_enhanced import preprocess_symbol

X_train, X_test, y_train, y_test = preprocess_symbol("BTCUSDT")
print(f"Training samples: {len(X_train)}")

# 3. Model Training
from model_training_enhanced import train_lstm_for_symbol

result = train_lstm_for_symbol("BTCUSDT")
print(f"R² Score: {result['metrics']['R2']:.4f}")
```

### Making Predictions

```python
from tensorflow.keras.models import load_model
import joblib
import numpy as np

# Load model and scalers
model = load_model("lstm_models/BTCUSDT/BTCUSDT_lstm.keras")
scaler_X = joblib.load("lstm_models/BTCUSDT/BTCUSDT_scaler_X.pkl")
scaler_y = joblib.load("lstm_models/BTCUSDT/BTCUSDT_scaler_y.pkl")
features = joblib.load("lstm_models/BTCUSDT/BTCUSDT_features.pkl")

# Prepare new data (must have same features)
new_data = df_new[features].values  # Shape: (n, 34)
new_data_scaled = scaler_X.transform(new_data)

# Create sequences
sequence_length = 48
X_seq = []
for i in range(len(new_data_scaled) - sequence_length):
    X_seq.append(new_data_scaled[i:i+sequence_length])
X_seq = np.array(X_seq)  # Shape: (n, 48, 34)

# Predict
predictions_scaled = model.predict(X_seq)
predictions = scaler_y.inverse_transform(predictions_scaled)

print(f"Predicted prices: {predictions[:5].ravel()}")
```

### Custom Configuration

```python
from utils import ConfigManager

# Load custom config
config = ConfigManager("my_config.json")

# Access settings
symbols = config.get("data_collection", "symbols")
epochs = config.get("model", "epochs")

print(f"Training {len(symbols)} symbols for {epochs} epochs")
```

### Error Handling Example

```python
from utils import RetryHandler, LoggerSetup
import requests

logger = LoggerSetup.setup_logger("my_app")

def fetch_data():
    response = requests.get("https://api.binance.com/api/v3/ping")
    response.raise_for_status()
    return response.json()

try:
    data = RetryHandler.retry_with_backoff(
        fetch_data,
        max_retries=5,
        initial_delay=1.0,
        logger=logger
    )
    print("API is accessible")
except Exception as e:
    logger.error(f"Failed to connect to API: {e}")
```

---

**Document Version**: 1.0  
**Last Updated**: December 15, 2025  
**Author**: API Documentation Team
