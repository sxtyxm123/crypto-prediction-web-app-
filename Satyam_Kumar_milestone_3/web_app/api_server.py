"""
Backend API for KRYPTX Web Application - REAL-TIME VERSION

This Flask server provides endpoints for:
- Real-time price predictions using live Binance data
- Current market prices
- Model metrics
- Historical data
"""

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_session import Session
import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import logging
import requests
from functools import wraps

# Add parent directory to path to import realtime module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realtime.inference import LiveInferenceEngine
from auth_manager import AuthManager

app = Flask(__name__)

# Session configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

Session(app)
CORS(app, supports_credentials=True)  # Enable CORS with credentials

# Initialize AuthManager
auth_manager = AuthManager()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MODELS_DIR = "../lstm_models"
SUPPORTED_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ASTRUSDT']

# Cache for inference engines
engines_cache = {}

# Preview mode configuration
PREVIEW_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  # Limited cryptos for preview
PREVIEW_DATA_LIMIT = 24  # Only 24 hours of data in preview


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged-in user"""
    if 'user_id' in session:
        return auth_manager.get_user_by_id(session['user_id'])
    return None

def get_inference_engine(symbol: str) -> LiveInferenceEngine:
    """Get or create inference engine for symbol"""
    if symbol not in engines_cache:
        try:
            engines_cache[symbol] = LiveInferenceEngine(symbol, models_dir=MODELS_DIR)
            logger.info(f"Created inference engine for {symbol}")
        except Exception as e:
            logger.error(f"Failed to create engine for {symbol}: {e}")
            raise
    
    return engines_cache[symbol]

def get_current_price_binance(symbol: str) -> dict:
    """Fetch current price from Binance API"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Get 24h stats
        stats_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        stats_response = requests.get(stats_url, timeout=5)
        stats = stats_response.json()
        
        # Exchange rate (INR to USD - you can fetch from API)
        exchange_rate = 83.5  # Approximate
        
        price_usd = float(data['price'])
        
        return {
            'price_usd': price_usd,
            'price_inr': price_usd * exchange_rate,
            'exchange_rate': exchange_rate,
            'change_24h': float(stats.get('priceChangePercent', 0)),
            'volume_24h': float(stats.get('volume', 0)),
            'high_24h': float(stats.get('highPrice', 0)),
            'low_24h': float(stats.get('lowPrice', 0))
        }
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None

@app.route('/api/cryptocurrencies', methods=['GET'])
def get_cryptocurrencies():
    """Get list of available cryptocurrencies"""
    cryptos = []
    
    for symbol in SUPPORTED_SYMBOLS:
        model_dir = os.path.join(MODELS_DIR, symbol)
        if os.path.exists(model_dir):
            # Get current price
            price_data = get_current_price_binance(symbol)
            
            crypto_info = {
                'symbol': symbol,
                'name': symbol.replace('USDT', ''),
                'available': True
            }
            
            if price_data:
                crypto_info.update(price_data)
            
            cryptos.append(crypto_info)
    
    return jsonify(cryptos)

@app.route('/api/current-price/<symbol>', methods=['GET'])
def get_current_price(symbol):
    """Get current market price from Binance"""
    try:
        price_data = get_current_price_binance(symbol)
        
        if price_data is None:
            return jsonify({'error': 'Failed to fetch price'}), 500
        
        return jsonify({
            'symbol': symbol,
            **price_data,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in get_current_price: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/<symbol>', methods=['POST'])
def predict(symbol):
    """
    Make real-time price prediction using live Binance data
    
    This endpoint:
    1. Fetches latest 100 candles from Binance
    2. Applies feature engineering
    3. Generates LSTM prediction
    4. Returns prediction with confidence
    """
    try:
        # Get parameters
        data = request.get_json() or {}
        
        # Get inference engine
        engine = get_inference_engine(symbol)
        
        # Make prediction using live data
        result = engine.predict(use_live_data=True)
        
        if 'error' in result:
            return jsonify(result), 400
        
        logger.info(
            f"Prediction for {symbol}: "
            f"Current=${result['current_price']:,.2f}, "
            f"Predicted=${result['predicted_price']:,.2f}"
        )
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in predict: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/<symbol>', methods=['GET'])
def get_metrics(symbol):
    """Get model performance metrics"""
    try:
        # Load metrics from file if available
        metrics_file = os.path.join(MODELS_DIR, symbol, 'metrics.json')
        
        if os.path.exists(metrics_file):
            import json
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        else:
            # Default metrics (from training)
            default_metrics = {
                'BTCUSDT': {
                    'R2': 0.9191,
                    'MAE': 1956.32,
                    'MSE': 16325779.28,
                    'Directional_Accuracy': 62.5,
                    'MAPE': 2.1
                },
                'ETHUSDT': {
                    'R2': 0.9842,
                    'MAE': 43.36,
                    'MSE': 4061.49,
                    'Directional_Accuracy': 65.3,
                    'MAPE': 1.8
                },
                'BNBUSDT': {
                    'R2': 0.9917,
                    'MAE': 7.32,
                    'MSE': 100.40,
                    'Directional_Accuracy': 68.1,
                    'MAPE': 1.5
                },
                'XRPUSDT': {
                    'R2': 0.9947,
                    'MAE': 0.0083,
                    'MSE': 0.0002,
                    'Directional_Accuracy': 70.2,
                    'MAPE': 1.2
                },
                'ASTRUSDT': {
                    'R2': 0.9796,
                    'MAE': 0.0009,
                    'MSE': 0.0000,
                    'Directional_Accuracy': 64.8,
                    'MAPE': 1.9
                }
            }
            
            metrics = default_metrics.get(symbol, {})
        
        return jsonify({
            'symbol': symbol,
            'metrics': metrics
        })
    
    except Exception as e:
        logger.error(f"Error in get_metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical/<symbol>', methods=['GET'])
def get_historical(symbol):
    """Get historical data from Binance"""
    try:
        num_points = int(request.args.get('points', 100))
        
        # Fetch from Binance
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': '1h',
            'limit': num_points
        }
        
        response = requests.get(url, params=params, timeout=10)
        klines = response.json()
        
        # Convert to friendly format
        data = []
        for kline in klines:
            data.append({
                'timestamp': datetime.fromtimestamp(kline[0] / 1000).isoformat(),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5])
            })
        
        return jsonify({
            'symbol': symbol,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        logger.error(f"Error in get_historical: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        result = auth_manager.register_user(
            name=data.get('name'),
            email=data.get('email'),
            password=data.get('password'),
            phone=data.get('phone'),
            birth_date=data.get('birth_date')
        )
        
        if result['success']:
            # Auto-login after registration
            session['user_id'] = result['user']['id']
            session['user_email'] = result['user']['email']
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in register: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        result = auth_manager.authenticate_user(
            email=data.get('email'),
            password=data.get('password')
        )
        
        if result['success']:
            session['user_id'] = result['user']['id']
            session['user_email'] = result['user']['email']
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@app.route('/api/auth/session', methods=['GET'])
def check_session():
    """Check if user is authenticated"""
    user = get_current_user()
    
    if user:
        return jsonify({
            'authenticated': True,
            'user': user
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 200


@app.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile"""
    user = get_current_user()
    return jsonify({'success': True, 'user': user}), 200


@app.route('/api/auth/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        result = auth_manager.update_profile(
            user_id=session['user_id'],
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            birth_date=data.get('birth_date'),
            preferences=data.get('preferences')
        )
        
        if result['success']:
            # Update session email if changed
            if 'email' in data:
                session['user_email'] = result['user']['email']
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in update_profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        result = auth_manager.change_password(
            user_id=session['user_id'],
            old_password=data.get('old_password'),
            new_password=data.get('new_password')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in change_password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PREVIEW MODE ENDPOINTS
# ============================================================================

@app.route('/api/preview/prices', methods=['GET'])
def get_preview_prices():
    """Get limited price data for preview mode (no auth required)"""
    try:
        prices = []
        
        for symbol in PREVIEW_SYMBOLS:
            price_data = get_current_price_binance(symbol)
            if price_data:
                prices.append({
                    'symbol': symbol,
                    'name': symbol.replace('USDT', ''),
                    **price_data
                })
        
        return jsonify({
            'success': True,
            'prices': prices,
            'preview_mode': True,
            'message': 'Login to access all cryptocurrencies'
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_preview_prices: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXISTING ENDPOINTS (Modified for auth)
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    user = get_current_user()
    
    return jsonify({
        'status': 'healthy',
        'version': '3.0-auth',
        'timestamp': datetime.now().isoformat(),
        'engines_loaded': len(engines_cache),
        'supported_symbols': SUPPORTED_SYMBOLS,
        'authenticated': user is not None,
        'total_users': auth_manager.get_all_users_count()
    })

if __name__ == '__main__':
    print("="*60)
    print("KRYPTX API Server - Real-Time Version")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  GET  /api/cryptocurrencies     - List cryptos with live prices")
    print("  GET  /api/current-price/<symbol> - Get current price")
    print("  POST /api/predict/<symbol>      - Real-time prediction")
    print("  GET  /api/metrics/<symbol>      - Model metrics")
    print("  GET  /api/historical/<symbol>   - Historical data")
    print("  GET  /api/health                - Health check")
    print("\nServer running on http://localhost:5000")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
