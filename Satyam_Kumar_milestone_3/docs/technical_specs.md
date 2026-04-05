# Technical Specifications

## Table of Contents
1. [Data Schemas](#data-schemas)
2. [API Specifications](#api-specifications)
3. [Model Architecture](#model-architecture)
4. [Performance Benchmarks](#performance-benchmarks)
5. [Feature Engineering](#feature-engineering)

## Data Schemas

### Raw OHLCV Data (Binance API Response)

**Format**: JSON Array

**Schema**:
```json
[
  [
    1640995200000,      // Open time (milliseconds)
    "46000.00",         // Open price
    "47000.00",         // High price
    "45500.00",         // Low price
    "46500.00",         // Close price
    "1234.56",          // Volume
    1640998799999,      // Close time (milliseconds)
    "57123456.78",      // Quote asset volume
    12345,              // Number of trades
    "617.28",           // Taker buy base asset volume
    "28561728.39",      // Taker buy quote asset volume
    "0"                 // Ignore
  ]
]
```

### ML-Ready CSV Schema

**File**: `{SYMBOL}_ML_ready.csv`

**Total Columns**: 40

| Column Name | Data Type | Description | Range/Format |
|-------------|-----------|-------------|--------------|
| **Time Columns** |
| open_time | datetime64 | Candle open timestamp | YYYY-MM-DD HH:MM:SS |
| close_time | datetime64 | Candle close timestamp | YYYY-MM-DD HH:MM:SS |
| **OHLCV Data** |
| open | float64 | Opening price | > 0 |
| high | float64 | Highest price in period | >= open |
| low | float64 | Lowest price in period | <= open |
| close | float64 | Closing price | > 0 |
| volume | float64 | Trading volume | >= 0 |
| **Volume Metrics** |
| quote_asset_volume | float64 | Quote asset volume | >= 0 |
| trades | int64 | Number of trades | >= 0 |
| taker_buy_volume | float64 | Taker buy volume | >= 0 |
| taker_buy_quote_volume | float64 | Taker buy quote volume | >= 0 |
| **Technical Indicators** |
| SMA_20 | float64 | 20-period Simple Moving Average | > 0 |
| EMA_20 | float64 | 20-period Exponential Moving Average | > 0 |
| RSI_14 | float64 | 14-period Relative Strength Index | 0-100 |
| MACD | float64 | MACD line | Any |
| MACD_signal | float64 | MACD signal line | Any |
| BBM | float64 | Bollinger Band Middle | > 0 |
| BBU | float64 | Bollinger Band Upper | > BBM |
| BBL | float64 | Bollinger Band Lower | < BBM |
| OBV | float64 | On-Balance Volume | Any |
| **Lag Features** |
| close_lag_1 | float64 | Close price 1 hour ago | > 0 |
| close_lag_3 | float64 | Close price 3 hours ago | > 0 |
| close_lag_6 | float64 | Close price 6 hours ago | > 0 |
| close_lag_12 | float64 | Close price 12 hours ago | > 0 |
| close_lag_24 | float64 | Close price 24 hours ago | > 0 |
| volume_lag_1 | float64 | Volume 1 hour ago | >= 0 |
| volume_lag_3 | float64 | Volume 3 hours ago | >= 0 |
| volume_lag_6 | float64 | Volume 6 hours ago | >= 0 |
| volume_lag_12 | float64 | Volume 12 hours ago | >= 0 |
| volume_lag_24 | float64 | Volume 24 hours ago | >= 0 |
| **Returns** |
| return_1h | float64 | 1-hour return | -1 to +∞ |
| return_3h | float64 | 3-hour return | -1 to +∞ |
| return_6h | float64 | 6-hour return | -1 to +∞ |
| **Volatility** |
| vol_3h | float64 | 3-hour volatility (std dev) | >= 0 |
| vol_6h | float64 | 6-hour volatility | >= 0 |
| vol_12h | float64 | 12-hour volatility | >= 0 |
| vol_24h | float64 | 24-hour volatility | >= 0 |
| **Target Variables** |
| target_next_close | float64 | Next hour's close price | > 0 |
| target_up_down | int64 | Binary: 1=up, 0=down | 0 or 1 |

**Example Row**:
```csv
open_time,open,high,low,close,volume,SMA_20,EMA_20,RSI_14,...
2024-01-15 10:00:00,46000.5,46200.3,45800.1,46100.2,1234.56,45950.3,46020.1,58.3,...
```

### Scaler Files

**Format**: Pickle (joblib)

**Files**:
- `{SYMBOL}_scaler_X.pkl`: MinMaxScaler for features
- `{SYMBOL}_scaler_y.pkl`: MinMaxScaler for target

**Structure**:
```python
{
    'min_': array([...]),      # Minimum values per feature
    'scale_': array([...]),    # Scale factors per feature
    'data_min_': array([...]), # Training data minimums
    'data_max_': array([...]), # Training data maximums
    'feature_range': (0, 1)    # Output range
}
```

## API Specifications

### Binance Klines API

**Endpoint**: `GET /api/v3/klines`

**Base URL**: `https://api.binance.com`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | STRING | YES | Trading pair (e.g., "BTCUSDT") |
| interval | ENUM | YES | Kline interval (e.g., "1h", "1d") |
| startTime | LONG | NO | Start time in milliseconds |
| endTime | LONG | NO | End time in milliseconds |
| limit | INT | NO | Number of results (max 1000, default 500) |

**Intervals**:
- `1m`, `3m`, `5m`, `15m`, `30m` (minutes)
- `1h`, `2h`, `4h`, `6h`, `8h`, `12h` (hours)
- `1d`, `3d` (days)
- `1w` (week)
- `1M` (month)

**Rate Limits**:
- Weight: 1 per request
- Limit: 1200 requests per minute
- IP-based rate limiting

**Example Request**:
```bash
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=100"
```

**Example Response**: See [Raw OHLCV Data Schema](#raw-ohlcv-data-binance-api-response)

**Error Responses**:

```json
{
  "code": -1121,
  "msg": "Invalid symbol."
}
```

Common error codes:
- `-1121`: Invalid symbol
- `-1100`: Illegal characters in parameter
- `-1003`: Too many requests (rate limit)

### Internal API (Future Enhancement)

**Planned REST API for predictions**:

```
POST /api/v1/predict
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "features": [...],
  "horizon": 1
}

Response:
{
  "symbol": "BTCUSDT",
  "current_price": 46100.50,
  "predicted_price": 46250.75,
  "confidence": 0.92,
  "timestamp": "2024-01-15T10:00:00Z"
}
```

## Model Architecture

### LSTM Network Specification

**Framework**: TensorFlow 2.13+ / Keras

**Architecture**:

```python
Model: "sequential"
_________________________________________________________________
Layer (type)                Output Shape              Param #   
=================================================================
lstm (LSTM)                 (None, 48, 64)            25344     
dropout (Dropout)           (None, 48, 64)            0         
lstm_1 (LSTM)               (None, 32)                12416     
dropout_1 (Dropout)         (None, 32)                0         
dense (Dense)               (None, 1)                 33        
=================================================================
Total params: 37,793
Trainable params: 37,793
Non-trainable params: 0
_________________________________________________________________
```

**Layer Details**:

#### Input Layer
- **Shape**: `(batch_size, sequence_length, n_features)`
- **Example**: `(64, 48, 34)`
  - 64 samples per batch
  - 48 hours of history
  - 34 features per hour

#### LSTM Layer 1
- **Units**: 64
- **Return Sequences**: True
- **Activation**: tanh (default)
- **Recurrent Activation**: sigmoid (default)
- **Parameters**: 25,344
  - Formula: `4 * ((input_dim + hidden_dim) * hidden_dim + hidden_dim)`
  - `4 * ((34 + 64) * 64 + 64) = 25,344`

#### Dropout Layer 1
- **Rate**: 0.2 (20% of neurons dropped)
- **Purpose**: Prevent overfitting

#### LSTM Layer 2
- **Units**: 32
- **Return Sequences**: False
- **Activation**: tanh
- **Recurrent Activation**: sigmoid
- **Parameters**: 12,416

#### Dropout Layer 2
- **Rate**: 0.2

#### Dense Output Layer
- **Units**: 1 (price prediction)
- **Activation**: Linear (default)
- **Parameters**: 33 (32 weights + 1 bias)

### Training Configuration

**Optimizer**: Adam
```python
{
    'learning_rate': 0.001,  # Default
    'beta_1': 0.9,
    'beta_2': 0.999,
    'epsilon': 1e-07
}
```

**Loss Function**: Mean Squared Error (MSE)
```python
loss = (1/n) * Σ(y_true - y_pred)²
```

**Callbacks**:

**Early Stopping**:
```python
{
    'monitor': 'val_loss',
    'patience': 5,
    'restore_best_weights': True,
    'min_delta': 0.0001
}
```

**Training Process**:
1. Forward pass through LSTM layers
2. Calculate MSE loss
3. Backpropagation through time (BPTT)
4. Adam optimizer updates weights
5. Validation on 10% of training data
6. Early stopping if no improvement for 5 epochs

### Model File Format

**Format**: Keras Native (.keras)

**Contents**:
- Model architecture (JSON)
- Weights (HDF5)
- Optimizer state
- Training configuration

**File Size**: ~500KB - 2MB depending on architecture

**Loading**:
```python
from tensorflow.keras.models import load_model
model = load_model('BTCUSDT_lstm.keras')
```

## Performance Benchmarks

### Hardware Specifications (Reference)

**CPU Training**:
- Processor: Intel i7-10700K @ 3.8GHz
- RAM: 16GB DDR4
- Storage: SSD

**GPU Training**:
- GPU: NVIDIA RTX 3070
- VRAM: 8GB
- CUDA: 11.8

### Execution Times

| Operation | CPU Time | GPU Time | Data Size |
|-----------|----------|----------|-----------|
| Data Collection (1 symbol) | 2-3 min | N/A | ~44K rows |
| Data Collection (5 symbols) | 10-15 min | N/A | ~220K rows |
| Preprocessing (1 symbol) | 15-30 sec | N/A | ~44K rows |
| Model Training (1 symbol, 40 epochs) | 12-15 min | 3-5 min | ~35K sequences |
| Model Training (early stop ~17 epochs) | 5-8 min | 2-3 min | ~35K sequences |
| Prediction (1000 samples) | 1-2 sec | <1 sec | 1000 sequences |

### Memory Usage

| Component | RAM Usage | VRAM Usage (GPU) |
|-----------|-----------|------------------|
| Data Collection | 200-500 MB | N/A |
| Preprocessing | 300-800 MB | N/A |
| Model Training | 1-2 GB | 2-4 GB |
| Model Inference | 100-300 MB | 500 MB - 1 GB |

### Model Performance Metrics

**Test Set Performance** (20% of data):

| Symbol | Dataset Size | MSE | MAE | R² | Training Time |
|--------|--------------|-----|-----|-----|---------------|
| BTCUSDT | 43,792 | 16,325,779 | 1,956.32 | 0.9191 | 8.5 min |
| ETHUSDT | 43,792 | 4,061.49 | 43.36 | 0.9842 | 7.2 min |
| BNBUSDT | 43,792 | 100.40 | 7.32 | 0.9917 | 6.8 min |
| XRPUSDT | 43,792 | 0.0002 | 0.0083 | 0.9947 | 7.5 min |
| ASTRUSDT | 24,876 | 0.0000 | 0.0009 | 0.9796 | 5.1 min |

**Interpretation**:
- **MSE varies by price scale**: BTC ($40K+) has higher MSE than XRP ($0.50)
- **MAE is more interpretable**: Average prediction error in dollars
- **R² shows model quality**: All models > 0.91, indicating strong fit

### Disk Space Requirements

| Component | Space Required |
|-----------|----------------|
| Raw data (1 symbol, 5 years) | 10-15 MB |
| Processed data (1 symbol) | 12-18 MB |
| Trained model (.keras) | 500 KB - 2 MB |
| Scalers and metadata | 50-100 KB |
| Logs (per run) | 100-500 KB |
| Prediction plots | 200-500 KB |
| **Total per symbol** | **25-40 MB** |
| **Total for 5 symbols** | **125-200 MB** |

## Feature Engineering

### Technical Indicators

#### Simple Moving Average (SMA)
```python
SMA_20 = close.rolling(window=20).mean()
```
**Purpose**: Smooth price data, identify trends

#### Exponential Moving Average (EMA)
```python
EMA_20 = close.ewm(span=20, adjust=False).mean()
```
**Purpose**: Weighted average favoring recent prices

#### Relative Strength Index (RSI)
```python
delta = close.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
RSI_14 = 100 - (100 / (1 + rs))
```
**Purpose**: Measure momentum, identify overbought/oversold conditions  
**Range**: 0-100 (>70 = overbought, <30 = oversold)

#### MACD (Moving Average Convergence Divergence)
```python
ema12 = close.ewm(span=12, adjust=False).mean()
ema26 = close.ewm(span=26, adjust=False).mean()
MACD = ema12 - ema26
MACD_signal = MACD.ewm(span=9, adjust=False).mean()
```
**Purpose**: Identify trend changes and momentum

#### Bollinger Bands
```python
BBM = close.rolling(20).mean()
std_20 = close.rolling(20).std()
BBU = BBM + 2 * std_20
BBL = BBM - 2 * std_20
```
**Purpose**: Measure volatility and price extremes

#### On-Balance Volume (OBV)
```python
obv = [0]
for i in range(1, len(df)):
    if close[i] > close[i-1]:
        obv.append(obv[-1] + volume[i])
    elif close[i] < close[i-1]:
        obv.append(obv[-1] - volume[i])
    else:
        obv.append(obv[-1])
```
**Purpose**: Relate volume to price changes

### Lag Features

**Purpose**: Provide historical context

```python
for lag in [1, 3, 6, 12, 24]:
    df[f'close_lag_{lag}'] = df['close'].shift(lag)
    df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
```

**Interpretation**:
- `close_lag_1`: Price 1 hour ago
- `close_lag_24`: Price 24 hours ago (same time yesterday)

### Returns

**Purpose**: Capture price momentum

```python
return_1h = close.pct_change(1)    # (close[t] - close[t-1]) / close[t-1]
return_3h = close.pct_change(3)
return_6h = close.pct_change(6)
```

**Range**: -1 to +∞ (-1 = 100% loss, 1 = 100% gain)

### Volatility

**Purpose**: Measure price instability

```python
for window in [3, 6, 12, 24]:
    df[f'vol_{window}h'] = close.rolling(window).std()
```

**Interpretation**: Higher values = more volatile market

### Time Features

**Purpose**: Capture cyclical patterns

```python
hour = open_time.dt.hour           # 0-23
dayofweek = open_time.dt.dayofweek # 0-6 (Monday=0)
day = open_time.dt.day             # 1-31
```

**Patterns**:
- Certain hours may have higher volatility
- Weekends may show different behavior
- Month-end effects

### Target Variables

#### Regression Target
```python
target_next_close = close.shift(-1)
```
**Purpose**: Predict next hour's closing price

#### Classification Target
```python
target_up_down = (target_next_close > close).astype(int)
```
**Purpose**: Predict price direction (0=down, 1=up)

### Feature Importance

**Most Important Features** (based on LSTM attention):
1. `close_lag_1` - Most recent price
2. `close` - Current price
3. `volume` - Trading activity
4. `RSI_14` - Momentum indicator
5. `MACD` - Trend indicator

**Least Important Features**:
1. `day` - Day of month
2. `trades` - Number of trades
3. `taker_buy_quote_volume` - Specific volume metric

---

**Document Version**: 1.0  
**Last Updated**: December 15, 2025  
**Author**: Technical Documentation Team
