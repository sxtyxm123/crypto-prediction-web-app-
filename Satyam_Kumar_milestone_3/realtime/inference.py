"""
Live Inference Engine

Real-time prediction engine that combines:
- WebSocket streaming
- Live feature engineering
- LSTM model inference
- Confidence estimation
"""

import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from typing import Dict, Optional
import logging
import requests
from datetime import datetime

from realtime.binance_ws import BinanceWebSocket
from realtime.live_buffer import LiveDataBuffer
from realtime.live_features import LiveFeatureEngine

logger = logging.getLogger(__name__)


class LiveInferenceEngine:
    """
    Real-time prediction engine for cryptocurrency prices
    
    Features:
    - WebSocket streaming
    - Live feature engineering
    - LSTM inference
    - Confidence estimation
    """
    
    def __init__(self, symbol: str, models_dir: str = "lstm_models"):
        """
        Initialize inference engine
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            models_dir: Directory containing trained models
        """
        self.symbol = symbol.upper()
        self.models_dir = models_dir
        self.symbol_dir = os.path.join(models_dir, self.symbol)
        
        # Load model and scalers
        self.model = self._load_model()
        self.scaler_X = self._load_scaler('X')
        self.scaler_y = self._load_scaler('y')
        self.feature_cols = self._load_features()
        
        # Initialize components
        self.buffer = LiveDataBuffer(sequence_length=48)
        self.feature_engine = LiveFeatureEngine(self._get_config())
        
        # WebSocket (optional - for continuous streaming)
        self.ws_client = None
        
        logger.info(f"Initialized LiveInferenceEngine for {self.symbol}")
    
    def _load_model(self):
        """Load trained LSTM model"""
        model_path = os.path.join(self.symbol_dir, f"{self.symbol}_lstm.keras")
        
        if not os.path.exists(model_path):
            # Try .h5 format
            model_path = os.path.join(self.symbol_dir, f"{self.symbol}_lstm.h5")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found for {self.symbol}")
        
        model = tf.keras.models.load_model(model_path)
        logger.info(f"Loaded model from {model_path}")
        return model
    
    def _load_scaler(self, scaler_type: str):
        """Load feature or target scaler"""
        scaler_path = os.path.join(self.symbol_dir, f"{self.symbol}_scaler_{scaler_type}.pkl")
        
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")
        
        scaler = joblib.load(scaler_path)
        logger.info(f"Loaded scaler_{scaler_type}")
        return scaler
    
    def _load_features(self):
        """Load feature column names"""
        features_path = os.path.join(self.symbol_dir, f"{self.symbol}_features.pkl")
        
        if not os.path.exists(features_path):
            logger.warning(f"Features file not found, using default")
            return self._get_default_features()
        
        features = joblib.load(features_path)
        logger.info(f"Loaded {len(features)} features")
        return features
    
    def _get_default_features(self):
        """Get default feature list"""
        return [
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
    
    def _get_config(self):
        """Get configuration for feature engineering"""
        return {
            'sma_period': 20,
            'ema_period': 20,
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2,
            'lag_periods': [1, 3, 6, 12, 24],
            'volatility_windows': [3, 6, 12, 24]
        }
    
    def get_current_price_from_binance(self) -> float:
        """Fetch current price from Binance REST API"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={self.symbol}"
            response = requests.get(url, timeout=5)
            data = response.json()
            return float(data['price'])
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            return None
    
    def fetch_recent_klines(self, limit: int = 100) -> pd.DataFrame:
        """
        Fetch recent klines from Binance REST API
        
        Args:
            limit: Number of recent candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': self.symbol,
                'interval': '1h',  # Match training data interval
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert types
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            logger.info(f"Fetched {len(df)} recent klines for {self.symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            return None
    
    def predict(self, use_live_data: bool = True) -> Dict:
        """
        Generate prediction
        
        Args:
            use_live_data: If True, fetch latest data from Binance
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Get current price
            current_price = self.get_current_price_from_binance()
            
            if current_price is None:
                return {'error': 'Failed to fetch current price'}
            
            # Fetch recent data if using live data
            if use_live_data:
                df_recent = self.fetch_recent_klines(limit=100)
                
                if df_recent is None or len(df_recent) < 48:
                    return {'error': 'Insufficient historical data'}
                
                # Process features
                df_processed = self.feature_engine.process_buffer(df_recent.to_dict('records'))
                
                # Get last 48 timesteps
                df_sequence = df_processed.tail(48)
                
                # Extract features
                X = df_sequence[self.feature_cols].values
            else:
                # Use buffer (for WebSocket mode)
                if not self.buffer.is_ready():
                    return {'error': 'Buffer not ready'}
                
                X = self.buffer.get_sequence(self.feature_cols)
            
            # Scale features
            X_scaled = self.scaler_X.transform(X)
            
            # Reshape for LSTM: (1, 48, n_features)
            X_seq = X_scaled.reshape(1, 48, -1)
            
            # Predict
            y_pred_scaled = self.model.predict(X_seq, verbose=0)
            
            # Inverse transform
            y_pred = self.scaler_y.inverse_transform(y_pred_scaled)[0][0]
            
            # Calculate metrics
            predicted_return = (y_pred - current_price) / current_price
            trend = "UP" if predicted_return > 0 else "DOWN"
            
            # Calculate confidence (using prediction variance)
            confidence = self._calculate_confidence(X_seq)
            
            # Calculate volatility
            recent_returns = df_processed['return_1h'].tail(24).values
            volatility = np.std(recent_returns[~np.isnan(recent_returns)])
            
            # Prediction bands
            lower_bound = y_pred * (1 - 2 * volatility)
            upper_bound = y_pred * (1 + 2 * volatility)
            
            result = {
                'symbol': self.symbol,
                'current_price': float(current_price),
                'predicted_price': float(y_pred),
                'predicted_return': float(predicted_return),
                'predicted_return_pct': float(predicted_return * 100),
                'trend': trend,
                'confidence': float(confidence),
                'volatility': float(volatility),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(
                f"Prediction: {self.symbol} "
                f"Current=${current_price:,.2f} "
                f"Predicted=${y_pred:,.2f} "
                f"({predicted_return*100:+.2f}%) "
                f"Trend={trend}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _calculate_confidence(self, X_seq: np.ndarray, num_samples: int = 10) -> float:
        """
        Calculate prediction confidence using Monte Carlo Dropout
        
        Args:
            X_seq: Input sequence
            num_samples: Number of MC samples
            
        Returns:
            Confidence score [0, 1]
        """
        try:
            predictions = []
            
            for _ in range(num_samples):
                # Enable dropout during inference
                pred = self.model(X_seq, training=True)
                predictions.append(pred.numpy()[0][0])
            
            predictions = np.array(predictions)
            
            # Confidence = 1 / (1 + normalized_std)
            std = np.std(predictions)
            mean = np.mean(predictions)
            normalized_std = std / (abs(mean) + 1e-10)
            confidence = 1 / (1 + normalized_std)
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.5  # Default confidence
    
    def start_websocket(self):
        """Start WebSocket streaming (optional)"""
        def on_candle(candle):
            # Process candle with features
            buffer_data = self.buffer.get_buffer() + [candle]
            df_processed = self.feature_engine.process_buffer(buffer_data)
            
            # Add to buffer
            latest_features = df_processed.iloc[-1].to_dict()
            self.buffer.add_candle(latest_features)
            
            logger.info(f"Added candle to buffer: {len(self.buffer.buffer)}/48")
        
        self.ws_client = BinanceWebSocket(
            symbol=self.symbol,
            interval="1h",
            on_candle_callback=on_candle
        )
        
        self.ws_client.start()
        logger.info(f"Started WebSocket for {self.symbol}")
    
    def stop_websocket(self):
        """Stop WebSocket streaming"""
        if self.ws_client:
            self.ws_client.stop()
            logger.info(f"Stopped WebSocket for {self.symbol}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create inference engine
    engine = LiveInferenceEngine(symbol="BTCUSDT")
    
    # Make prediction
    print("\n" + "="*60)
    print("LIVE PREDICTION")
    print("="*60)
    
    result = engine.predict(use_live_data=True)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nSymbol: {result['symbol']}")
        print(f"Current Price: ${result['current_price']:,.2f}")
        print(f"Predicted Price: ${result['predicted_price']:,.2f}")
        print(f"Expected Return: {result['predicted_return_pct']:+.2f}%")
        print(f"Trend: {result['trend']}")
        print(f"Confidence: {result['confidence']*100:.1f}%")
        print(f"Volatility: {result['volatility']*100:.2f}%")
        print(f"Prediction Range: ${result['lower_bound']:,.2f} - ${result['upper_bound']:,.2f}")
