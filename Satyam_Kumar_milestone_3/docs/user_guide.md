# User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the System](#running-the-system)
5. [Understanding the Output](#understanding-the-output)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

## Getting Started

### What is This System?

This is an automated cryptocurrency price prediction system that uses artificial intelligence to forecast future prices. It analyzes historical price data, calculates technical indicators, and trains deep learning models to make predictions.

### Who Should Use This?

- **Researchers**: Studying cryptocurrency price patterns
- **Developers**: Building trading algorithms
- **Students**: Learning about machine learning and finance
- **Analysts**: Exploring cryptocurrency market dynamics

### What You'll Need

- A computer with Windows, Mac, or Linux
- Python 3.8 or newer installed
- Internet connection for downloading data
- At least 4GB of RAM
- 2GB of free disk space

## Installation

### Step 1: Install Python

**Windows**:
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ Check "Add Python to PATH"
4. Click "Install Now"

**Mac**:
```bash
# Using Homebrew
brew install python@3.11
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Verify Python Installation

Open a terminal/command prompt and run:
```bash
python --version
```

You should see something like: `Python 3.11.7`

### Step 3: Navigate to Project Directory

```bash
cd "c:/Users/hp/Desktop/New folder/final"
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- TensorFlow (deep learning)
- Pandas (data processing)
- NumPy (numerical computing)
- Scikit-learn (machine learning tools)
- Matplotlib (visualization)
- And other required packages

**Installation Time**: 5-10 minutes depending on your internet speed

### Step 5: Verify Installation

```bash
python -c "import tensorflow; import pandas; print('✓ All packages installed successfully')"
```

## Configuration

### Understanding config.json

The `config.json` file controls all system parameters. Here's what each section means:

#### Data Collection Settings

```json
"data_collection": {
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ASTRUSDT"],
  "interval": "1h",
  "start_date": "2020-01-01",
  "end_date": "2025-01-01",
  "max_retries": 3,
  "request_delay": 0.2
}
```

- **symbols**: Which cryptocurrencies to analyze
- **interval**: Time between data points (`1h` = hourly, `1d` = daily)
- **start_date**: How far back to collect data
- **end_date**: End of data collection period
- **max_retries**: How many times to retry failed API calls
- **request_delay**: Seconds to wait between API requests

#### Model Settings

```json
"model": {
  "sequence_length": 48,
  "epochs": 40,
  "batch_size": 64,
  "lstm_units": [64, 32],
  "dropout_rate": 0.2
}
```

- **sequence_length**: How many hours of history to use for prediction
- **epochs**: Maximum training iterations
- **batch_size**: Number of samples processed together
- **lstm_units**: Size of neural network layers
- **dropout_rate**: Regularization to prevent overfitting

### Common Configuration Changes

#### Analyze Different Cryptocurrencies

```json
"symbols": ["SOLUSDT", "ADAUSDT", "DOGEUSDT"]
```

Available symbols: Any trading pair on Binance ending in USDT

#### Change Date Range

```json
"start_date": "2022-01-01",
"end_date": "2024-12-31"
```

**Note**: More data = better models, but longer processing time

#### Adjust Model Complexity

**Faster training (less accurate)**:
```json
"epochs": 20,
"lstm_units": [32, 16]
```

**Better accuracy (slower training)**:
```json
"epochs": 60,
"lstm_units": [128, 64]
```

## Running the System

### Complete Workflow

#### Step 1: Collect Data

```bash
python data_collector_enhanced.py
```

**What happens**:
- Connects to Binance API
- Downloads historical price data
- Calculates technical indicators
- Saves data to `crypto_data/` folder

**Expected output**:
```
==============================
Processing BTCUSDT ...
==============================
✓ Saved: crypto_data\BTCUSDT\BTCUSDT_ML_ready.csv
  Shape: (43792, 40)
  Size: 12.45 MB
  Time: 2.3m
```

**Duration**: 2-5 minutes per cryptocurrency

#### Step 2: Preprocess Data

```bash
python data_preprocessing_enhanced.py
```

**What happens**:
- Loads collected data
- Validates data quality
- Splits into training and test sets
- Scales features for machine learning
- Saves scalers for later use

**Expected output**:
```
================================
Processing BTCUSDT
================================
BTCUSDT ->
  X_train_final: (35033, 10)
  X_test_final : (8759, 10)
  y_train_scaled: (35033, 1)
  y_test_scaled : (8759, 1)
```

**Duration**: 10-30 seconds per cryptocurrency

#### Step 3: Train Models

```bash
python model_training_enhanced.py
```

**What happens**:
- Builds LSTM neural networks
- Trains models on historical data
- Generates prediction charts
- Saves trained models
- Calculates performance metrics

**Expected output**:
```
=======================================
Training LSTM for BTCUSDT
=======================================
Total usable rows: 43792
Features: 34
X_train_seq shape: (34985, 48, 34)
X_test_seq shape: (8711, 48, 34)

Epoch 1/40
492/492 ━━━━━━━━━━━━━━━━━━━━ 31s 50ms/step - loss: 0.0041

LSTM Metrics for BTCUSDT:
  MSE: 16325779.2784
  MAE: 1956.3239
  R2 : 0.9191

Training completed in 8.5m
```

**Duration**: 5-15 minutes per cryptocurrency

### Using Jupyter Notebooks

If you prefer interactive development:

1. **Start Jupyter**:
   ```bash
   jupyter notebook
   ```

2. **Open a notebook**:
   - `datacollector.ipynb`
   - `data pre processing.ipynb`
   - `models .ipynb`

3. **Run cells**: Click "Run" or press Shift+Enter

## Understanding the Output

### Directory Structure After Running

```
final/
├── crypto_data/
│   └── BTCUSDT/
│       ├── BTCUSDT_ML_ready.csv      # Processed data
│       └── scalers/
│           ├── BTCUSDT_scaler_X.pkl  # Feature scaler
│           └── BTCUSDT_scaler_y.pkl  # Target scaler
│
├── lstm_models/
│   └── BTCUSDT/
│       ├── BTCUSDT_lstm.keras              # Trained model
│       ├── BTCUSDT_scaler_X.pkl            # Feature scaler
│       ├── BTCUSDT_scaler_y.pkl            # Target scaler
│       ├── BTCUSDT_features.pkl            # Feature list
│       └── BTCUSDT_lstm_predictions.png    # Prediction chart
│
└── logs/
    ├── data_collector_20251215_134500.log
    ├── data_preprocessing_20251215_135000.log
    └── model_training_20251215_140000.log
```

### Interpreting Metrics

#### Mean Squared Error (MSE)
- **What it is**: Average squared difference between predictions and actual values
- **Lower is better**: 0 = perfect predictions
- **Scale**: Depends on price range (BTC has higher MSE than XRP)

#### Mean Absolute Error (MAE)
- **What it is**: Average absolute difference in price
- **Interpretation**: "On average, predictions are off by $X"
- **Example**: MAE of 1956 for BTC means predictions are ±$1956 on average

#### R² Score (Coefficient of Determination)
- **What it is**: How well the model explains price variance
- **Range**: 0 to 1 (can be negative for very bad models)
- **Interpretation**:
  - 0.9+ = Excellent
  - 0.7-0.9 = Good
  - 0.5-0.7 = Moderate
  - < 0.5 = Poor

### Reading Prediction Charts

The generated PNG files show:
- **Blue line**: Actual prices
- **Orange line**: Predicted prices

**Good model**: Lines closely follow each other  
**Poor model**: Lines diverge significantly

## Troubleshooting

### Common Errors and Solutions

#### Error: "ModuleNotFoundError: No module named 'tensorflow'"

**Solution**:
```bash
pip install tensorflow
```

#### Error: "FileNotFoundError: config.json not found"

**Solution**: Make sure you're in the correct directory
```bash
cd "c:/Users/hp/Desktop/New folder/final"
```

#### Error: "API request failed: Connection timeout"

**Possible causes**:
1. No internet connection
2. Binance API is down
3. Firewall blocking requests

**Solutions**:
- Check internet connection
- Try again later
- Check firewall settings
- Increase timeout in config.json

#### Error: "Insufficient memory"

**Solutions**:
- Reduce `batch_size` in config.json
- Process fewer symbols at once
- Close other applications
- Use a computer with more RAM

#### Warning: "Model not converging"

**Solutions**:
- Increase `epochs` in config.json
- Reduce `learning_rate` (add to config)
- Check data quality
- Try different `lstm_units` configuration

### Checking Logs

Logs are saved in the `logs/` directory with timestamps.

**To view logs**:
```bash
# Windows
type logs\model_training_*.log

# Mac/Linux
cat logs/model_training_*.log
```

**What to look for**:
- `ERROR`: Something went wrong
- `WARNING`: Potential issue
- `INFO`: Normal operation
- `DEBUG`: Detailed information

### Getting Help

1. **Check logs**: Look for ERROR messages
2. **Verify configuration**: Ensure config.json is valid JSON
3. **Test internet**: Try accessing https://api.binance.com/api/v3/ping
4. **Check disk space**: Ensure you have 2GB+ free
5. **Verify Python version**: Must be 3.8 or higher

## FAQ

### General Questions

**Q: How accurate are the predictions?**  
A: R² scores of 0.9+ indicate good fit to historical data, but past performance doesn't guarantee future results. Use predictions as one input among many for decision-making.

**Q: Can I use this for real trading?**  
A: This is a research/educational tool. Real trading requires additional considerations like transaction costs, slippage, risk management, and regulatory compliance.

**Q: How often should I retrain models?**  
A: Recommended: Weekly or monthly, as market conditions change. More frequent retraining captures recent patterns.

**Q: Can I add more cryptocurrencies?**  
A: Yes! Edit the `symbols` list in config.json. Any Binance USDT pair works (e.g., "SOLUSDT", "ADAUSDT").

### Technical Questions

**Q: Why LSTM instead of other algorithms?**  
A: LSTMs excel at sequence prediction and can capture long-term dependencies in time-series data. See [architecture.md](architecture.md) for details.

**Q: What's the difference between .h5 and .keras formats?**  
A: `.keras` is the modern format (TensorFlow 2.13+) with better compatibility and features. The enhanced scripts use `.keras`.

**Q: Can I use GPU for faster training?**  
A: Yes! TensorFlow automatically uses GPU if available. Install `tensorflow-gpu` and CUDA drivers.

**Q: How do I make predictions on new data?**  
A: Load the saved model and scalers:
```python
from tensorflow.keras.models import load_model
import joblib

model = load_model('lstm_models/BTCUSDT/BTCUSDT_lstm.keras')
scaler_X = joblib.load('lstm_models/BTCUSDT/BTCUSDT_scaler_X.pkl')
scaler_y = joblib.load('lstm_models/BTCUSDT/BTCUSDT_scaler_y.pkl')

# Scale new data and predict
X_scaled = scaler_X.transform(new_data)
prediction_scaled = model.predict(X_scaled)
prediction = scaler_y.inverse_transform(prediction_scaled)
```

### Data Questions

**Q: How much historical data do I need?**  
A: Minimum: 6 months. Recommended: 2+ years for robust models.

**Q: What if data collection fails partway through?**  
A: The script saves progress. Re-running will continue from where it left off (though it may re-fetch some data).

**Q: Can I use data from other sources?**  
A: Yes, but you'll need to format it to match the expected CSV structure. See [technical_specs.md](technical_specs.md) for schema details.

**Q: What's the maximum date range?**  
A: Limited by Binance data availability (typically 2017 onwards for major cryptocurrencies).

### Performance Questions

**Q: Why is training so slow?**  
A: LSTM training is computationally intensive. Solutions:
- Use GPU acceleration
- Reduce `epochs` or `batch_size`
- Train on fewer symbols
- Use a more powerful computer

**Q: How can I speed up data collection?**  
A: The script includes rate limiting to respect API limits. You can reduce `request_delay` slightly, but too low may cause API bans.

**Q: Can I run multiple trainings in parallel?**  
A: Yes, but ensure you have enough RAM and CPU/GPU resources. Each training process is independent.

---

**Need More Help?**

- Review the [Technical Specifications](technical_specs.md)
- Check the [Architecture Documentation](architecture.md)
- Examine the [API Reference](api_reference.md)
- Look at log files in the `logs/` directory

**Document Version**: 1.0  
**Last Updated**: December 15, 2025
