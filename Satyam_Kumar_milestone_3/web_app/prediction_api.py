"""
Real-time Prediction API for Cryptocurrency Price Forecasting

This module provides endpoints to generate actual predictions using trained LSTM models.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuration
MODELS_DIR = "../lstm_models"
DATA_DIR = "../crypto_data"
SEQUENCE_LENGTH = 48

# Cache for loaded models
models_cache = {}

def load_crypto_assets(symbol):
    """Load model, scalers, and features for a cryptocurrency"""
    if symbol not in models_cache:
        model_dir = os.path.join(MODELS_DIR, symbol)
        
        # Load model
        model_path = os.path.join(model_dir, f"{symbol}_lstm.keras")
        if not os.path.exists(model_path):
            model_path = os.path.join(model_dir, f"{symbol}_lstm.h5")
        
        if not os.path.exists(model_path):
            return None
        
        model = load_model(model_path)
        
        # Load scalers and features
        scaler_X = joblib.load(os.path.join(model_dir, f"{symbol}_scaler_X.pkl"))
        scaler_y = joblib.load(os.path.join(model_dir, f"{symbol}_scaler_y.pkl"))
        features = joblib.load(os.path.join(model_dir, f"{symbol}_features.pkl"))
        
        models_cache[symbol] = {
            'model': model,
            'scaler_X': scaler_X,
            'scaler_y': scaler_y,
            'features': features
        }
    
    return models_cache[symbol]

def load_recent_data(symbol, num_points=100):
    """Load recent historical data"""
    data_path = os.path.join(DATA_DIR, symbol, f"{symbol}_ML_ready.csv")
    
    if not os.path.exists(data_path):
        return None
    
    df = pd.read_csv(data_path)
    df['open_time'] = pd.to_datetime(df['open_time'])
    df = df.sort_values('open_time')
    
    return df.tail(num_points)

@app.route('/api/predict/<symbol>', methods=['GET'])
def predict_price(symbol):
    """Generate real predictions for a cryptocurrency"""
    try:
        # Load model assets
        assets = load_crypto_assets(symbol)
        if not assets:
            return jsonify({'error': f'Model not found for {symbol}'}), 404
        
        model = assets['model']
        scaler_X = assets['scaler_X']
        scaler_y = assets['scaler_y']
        features = assets['features']
        
        # Load recent data
        df = load_recent_data(symbol)
        if df is None or len(df) < SEQUENCE_LENGTH:
            return jsonify({'error': 'Insufficient data'}), 404
        
        # Get the most recent sequence
        recent_data = df[features].tail(SEQUENCE_LENGTH).values
        
        # Scale the data
        recent_scaled = scaler_X.transform(recent_data)
        
        # Reshape for LSTM [samples, timesteps, features]
        X_input = recent_scaled.reshape(1, SEQUENCE_LENGTH, len(features))
        
        # Generate predictions for multiple timeframes
        predictions = {}
        current_price = df['close'].iloc[-1]
        
        # 1-hour prediction
        pred_1h_scaled = model.predict(X_input, verbose=0)
        pred_1h = scaler_y.inverse_transform(pred_1h_scaled)[0][0]
        
        # Calculate confidence based on recent volatility
        recent_volatility = df['close'].pct_change().tail(24).std()
        confidence_1h = max(0.85, min(0.98, 0.95 - recent_volatility * 10))
        
        # Calculate prediction bounds
        std_error_1h = abs(pred_1h - current_price) * 0.5
        
        predictions['1h'] = {
            'predicted_price': float(pred_1h),
            'current_price': float(current_price),
            'change_percent': float(((pred_1h - current_price) / current_price) * 100),
            'confidence': float(confidence_1h),
            'upper_bound': float(pred_1h + 1.96 * std_error_1h),
            'lower_bound': float(pred_1h - 1.96 * std_error_1h),
            'timestamp': (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        # 4-hour prediction (iterative)
        pred_4h = pred_1h
        for _ in range(3):
            # Use previous prediction to generate next
            new_row = recent_scaled[-1].copy()
            new_row[0] = scaler_y.transform([[pred_4h]])[0][0]  # Update close price
            recent_scaled = np.vstack([recent_scaled[1:], new_row])
            X_input = recent_scaled.reshape(1, SEQUENCE_LENGTH, len(features))
            pred_scaled = model.predict(X_input, verbose=0)
            pred_4h = scaler_y.inverse_transform(pred_scaled)[0][0]
        
        confidence_4h = confidence_1h - 0.03
        std_error_4h = abs(pred_4h - current_price) * 0.7
        
        predictions['4h'] = {
            'predicted_price': float(pred_4h),
            'current_price': float(current_price),
            'change_percent': float(((pred_4h - current_price) / current_price) * 100),
            'confidence': float(confidence_4h),
            'upper_bound': float(pred_4h + 1.96 * std_error_4h),
            'lower_bound': float(pred_4h - 1.96 * std_error_4h),
            'timestamp': (datetime.now() + timedelta(hours=4)).isoformat()
        }
        
        # 24-hour prediction (iterative)
        pred_24h = pred_4h
        for _ in range(20):
            new_row = recent_scaled[-1].copy()
            new_row[0] = scaler_y.transform([[pred_24h]])[0][0]
            recent_scaled = np.vstack([recent_scaled[1:], new_row])
            X_input = recent_scaled.reshape(1, SEQUENCE_LENGTH, len(features))
            pred_scaled = model.predict(X_input, verbose=0)
            pred_24h = scaler_y.inverse_transform(pred_scaled)[0][0]
        
        confidence_24h = confidence_1h - 0.07
        std_error_24h = abs(pred_24h - current_price) * 1.2
        
        predictions['24h'] = {
            'predicted_price': float(pred_24h),
            'current_price': float(current_price),
            'change_percent': float(((pred_24h - current_price) / current_price) * 100),
            'confidence': float(confidence_24h),
            'upper_bound': float(pred_24h + 1.96 * std_error_24h),
            'lower_bound': float(pred_24h - 1.96 * std_error_24h),
            'timestamp': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        return jsonify({
            'symbol': symbol,
            'predictions': predictions,
            'model_info': {
                'type': 'LSTM',
                'sequence_length': SEQUENCE_LENGTH,
                'features_count': len(features)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-price/<symbol>', methods=['GET'])
def get_current_price(symbol):
    """Get the most recent actual price from data"""
    try:
        df = load_recent_data(symbol, 1)
        if df is None:
            return jsonify({'error': 'Data not found'}), 404
        
        latest = df.iloc[-1]
        exchange_rate = 90.34
        
        return jsonify({
            'symbol': symbol,
            'price_usd': float(latest['close']),
            'price_inr': float(latest['close']) * exchange_rate,
            'volume_24h': float(latest['volume']),
            'exchange_rate': exchange_rate,
            'timestamp': latest['open_time'].isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical/<symbol>', methods=['GET'])
def get_historical(symbol):
    """Get historical data for charts"""
    try:
        points = int(request.args.get('points', 100))
        df = load_recent_data(symbol, points)
        
        if df is None:
            return jsonify({'error': 'Data not found'}), 404
        
        data = []
        for _, row in df.iterrows():
            data.append({
                'timestamp': row['open_time'].isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        
        return jsonify({
            'symbol': symbol,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(models_cache),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("CRYPTOCURRENCY PREDICTION API SERVER")
    print("=" * 60)
    print("\nAvailable Endpoints:")
    print("  GET  /api/predict/<symbol>")
    print("  GET  /api/current-price/<symbol>")
    print("  GET  /api/historical/<symbol>?points=100")
    print("  GET  /api/health")
    print("\nSupported Symbols:")
    print("  BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ASTRUSDT")
    print("\nServer running on http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
