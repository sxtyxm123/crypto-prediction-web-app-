# Real Prediction API - Quick Start Guide

## Overview

This API server provides **real predictions** from your trained LSTM models instead of simulated data.

## Setup

### 1. Start the API Server

```bash
cd web_app
python prediction_api.py
```

You should see:
```
============================================================
CRYPTOCURRENCY PREDICTION API SERVER
============================================================

Available Endpoints:
  GET  /api/predict/<symbol>
  GET  /api/current-price/<symbol>
  GET  /api/historical/<symbol>?points=100
  GET  /api/health

Supported Symbols:
  BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ASTRUSDT

Server running on http://localhost:5000
============================================================
```

### 2. Open the Web App

```bash
# In a new terminal
cd web_app
python -m http.server 8000
```

Then open: `http://localhost:8000`

## Features

### Real Predictions

The API now generates **actual predictions** using your trained LSTM models:

- **1-hour forecast**: Uses the model directly on the last 48 hours of data
- **4-hour forecast**: Iterative prediction (predicts 4 times, 1 hour each)
- **24-hour forecast**: Iterative prediction (predicts 24 times)

### Confidence Intervals

- Calculated based on recent price volatility
- 95% confidence bands (upper and lower bounds)
- Confidence decreases for longer-term predictions

### Current Prices

- Fetched from the actual latest data point in your CSV files
- Not simulated or hardcoded

## API Endpoints

### GET /api/predict/<symbol>

Returns predictions for 1h, 4h, and 24h timeframes.

**Example Response**:
```json
{
  "symbol": "BTCUSDT",
  "predictions": {
    "1h": {
      "predicted_price": 89208.92,
      "current_price": 92422.00,
      "change_percent": -3.48,
      "confidence": 0.95,
      "upper_bound": 91500.00,
      "lower_bound": 86900.00
    },
    "4h": { ... },
    "24h": { ... }
  }
}
```

### GET /api/current-price/<symbol>

Returns the most recent actual price from your data.

**Example Response**:
```json
{
  "symbol": "BTCUSDT",
  "price_usd": 92422.00,
  "price_inr": 8348967.00,
  "volume_24h": 28500000000,
  "exchange_rate": 90.34
}
```

## Troubleshooting

### "Model not found"

Make sure your trained models exist in:
```
../lstm_models/BTCUSDT/BTCUSDT_lstm.keras
../lstm_models/ETHUSDT/ETHUSDT_lstm.keras
etc.
```

### "Insufficient data"

Ensure you have at least 48 hours of data in:
```
../crypto_data/BTCUSDT/BTCUSDT_ML_ready.csv
```

### CORS Errors

The API has CORS enabled. If you still get errors, make sure:
1. API server is running on port 5000
2. Web app is accessing `http://localhost:5000`

## Toggle Between Real and Simulated

In `app.js`, line 7:
```javascript
const USE_REAL_API = true;  // Set to false for simulated data
```

---

**Now your predictions will be real!** 🎯
