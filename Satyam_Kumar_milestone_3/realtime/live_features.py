"""
Live Feature Engineering

Applies IDENTICAL feature engineering to live data as used in training.
This ensures consistency between training and inference.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


class LiveFeatureEngine:
    """
    Real-time feature engineering that matches training pipeline
    
    CRITICAL: Must use exact same calculations as data_collector_enhanced.py
    """
    
    def __init__(self, config: Dict):
        """
        Initialize feature engine
        
        Args:
            config: Configuration dictionary with indicator parameters
        """
        self.config = config
        
        # Technical indicator parameters
        self.sma_period = config.get('sma_period', 20)
        self.ema_period = config.get('ema_period', 20)
        self.rsi_period = config.get('rsi_period', 14)
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)
        self.lag_periods = config.get('lag_periods', [1, 3, 6, 12, 24])
        self.vol_windows = config.get('volatility_windows', [3, 6, 12, 24])
        
        logger.info("Initialized LiveFeatureEngine")
    
    def calculate_sma(self, df: pd.DataFrame, period: int, col: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average"""
        return df[col].rolling(window=period, min_periods=1).mean()
    
    def calculate_ema(self, df: pd.DataFrame, period: int, col: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df[col].ewm(span=period, adjust=False, min_periods=1).mean()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame) -> tuple:
        """Calculate MACD and Signal line"""
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False, min_periods=1).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False, min_periods=1).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=self.macd_signal, adjust=False, min_periods=1).mean()
        
        return macd, signal
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> tuple:
        """Calculate Bollinger Bands"""
        sma = df['close'].rolling(window=self.bb_period, min_periods=1).mean()
        std = df['close'].rolling(window=self.bb_period, min_periods=1).std()
        
        upper = sma + (std * self.bb_std)
        lower = sma - (std * self.bb_std)
        
        return upper, sma, lower
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return obv
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all technical indicators"""
        df = df.copy()
        
        # SMA and EMA
        df['SMA_20'] = self.calculate_sma(df, self.sma_period)
        df['EMA_20'] = self.calculate_ema(df, self.ema_period)
        
        # RSI
        df['RSI_14'] = self.calculate_rsi(df, self.rsi_period)
        
        # MACD
        df['MACD'], df['MACD_signal'] = self.calculate_macd(df)
        
        # Bollinger Bands
        df['BBU'], df['BBM'], df['BBL'] = self.calculate_bollinger_bands(df)
        
        # OBV
        df['OBV'] = self.calculate_obv(df)
        
        return df
    
    def add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged features"""
        df = df.copy()
        
        for lag in self.lag_periods:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        return df
    
    def add_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add return features"""
        df = df.copy()
        
        df['return_1h'] = df['close'].pct_change(1)
        df['return_3h'] = df['close'].pct_change(3)
        df['return_6h'] = df['close'].pct_change(6)
        
        return df
    
    def add_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility features"""
        df = df.copy()
        
        returns = df['close'].pct_change()
        
        for window in self.vol_windows:
            df[f'vol_{window}h'] = returns.rolling(window=window, min_periods=1).std()
        
        return df
    
    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        df = df.copy()
        
        if 'open_time' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['open_time']):
                df['open_time'] = pd.to_datetime(df['open_time'])
            
            df['hour'] = df['open_time'].dt.hour
            df['dayofweek'] = df['open_time'].dt.dayofweek
            df['day'] = df['open_time'].dt.day
        
        return df
    
    def process_buffer(self, buffer_data: List[Dict]) -> pd.DataFrame:
        """
        Process buffer data with all features
        
        Args:
            buffer_data: List of candle dictionaries
            
        Returns:
            DataFrame with all features
        """
        # Convert to DataFrame
        df = pd.DataFrame(buffer_data)
        
        # Add all features
        df = self.add_technical_indicators(df)
        df = self.add_lag_features(df)
        df = self.add_returns(df)
        df = self.add_volatility(df)
        df = self.add_time_features(df)
        
        # Fill NaN values
        df = df.fillna(method='bfill').fillna(0)
        
        return df
    
    def get_latest_features(self, buffer_data: List[Dict], feature_cols: List[str]) -> Dict:
        """
        Get features for the latest candle
        
        Args:
            buffer_data: List of candle dictionaries
            feature_cols: List of feature column names
            
        Returns:
            Dictionary of features for latest candle
        """
        df = self.process_buffer(buffer_data)
        
        # Get latest row
        latest = df.iloc[-1]
        
        # Extract only required features
        features = {col: latest[col] for col in feature_cols if col in latest.index}
        
        return features


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config = {
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
    
    engine = LiveFeatureEngine(config)
    
    # Simulate buffer data
    buffer_data = []
    for i in range(50):
        candle = {
            'open_time': pd.Timestamp.now() - pd.Timedelta(minutes=50-i),
            'open': 100 + i + np.random.randn(),
            'high': 105 + i + np.random.randn(),
            'low': 95 + i + np.random.randn(),
            'close': 102 + i + np.random.randn(),
            'volume': 1000 + i * 10
        }
        buffer_data.append(candle)
    
    # Process buffer
    df_processed = engine.process_buffer(buffer_data)
    print(f"\nProcessed DataFrame shape: {df_processed.shape}")
    print(f"Columns: {list(df_processed.columns)}")
    print(f"\nLatest candle features:")
    print(df_processed.iloc[-1][['close', 'SMA_20', 'RSI_14', 'MACD']])
