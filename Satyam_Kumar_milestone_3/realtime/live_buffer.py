"""
Live Data Buffer for Real-Time Inference

Maintains a rolling window of processed candles with features
for LSTM sequence generation.
"""

import numpy as np
import pandas as pd
from collections import deque
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LiveDataBuffer:
    """
    Maintains rolling window for live inference
    
    Features:
    - Fixed-size rolling buffer
    - Feature-ready data storage
    - Sequence generation for LSTM
    """
    
    def __init__(self, sequence_length: int = 48, max_size: int = 100):
        """
        Initialize buffer
        
        Args:
            sequence_length: Number of timesteps for LSTM input
            max_size: Maximum buffer size
        """
        self.sequence_length = sequence_length
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        
        logger.info(f"Initialized buffer: seq_len={sequence_length}, max_size={max_size}")
    
    def add_candle(self, candle_with_features: Dict):
        """
        Add processed candle with features to buffer
        
        Args:
            candle_with_features: Dictionary with OHLCV + technical indicators
        """
        self.buffer.append(candle_with_features)
        
        if len(self.buffer) >= self.sequence_length:
            logger.debug(f"Buffer ready: {len(self.buffer)}/{self.sequence_length} candles")
    
    def is_ready(self) -> bool:
        """Check if buffer has enough data for prediction"""
        return len(self.buffer) >= self.sequence_length
    
    def get_sequence(self, feature_cols: List[str]) -> Optional[np.ndarray]:
        """
        Get latest sequence for LSTM prediction
        
        Args:
            feature_cols: List of feature column names
            
        Returns:
            numpy array of shape (sequence_length, n_features) or None
        """
        if not self.is_ready():
            logger.warning(f"Buffer not ready: {len(self.buffer)}/{self.sequence_length}")
            return None
        
        # Get last sequence_length candles
        recent_candles = list(self.buffer)[-self.sequence_length:]
        
        # Convert to DataFrame
        df = pd.DataFrame(recent_candles)
        
        # Extract features in correct order
        try:
            sequence = df[feature_cols].values
            logger.debug(f"Generated sequence: shape={sequence.shape}")
            return sequence
        except KeyError as e:
            logger.error(f"Missing features in buffer: {e}")
            return None
    
    def get_latest_candle(self) -> Optional[Dict]:
        """Get most recent candle"""
        return self.buffer[-1] if self.buffer else None
    
    def get_buffer_size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        logger.info("Buffer cleared")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert buffer to DataFrame"""
        return pd.DataFrame(list(self.buffer))


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create buffer
    buffer = LiveDataBuffer(sequence_length=48)
    
    # Simulate adding candles
    feature_cols = ['open', 'high', 'low', 'close', 'volume', 'SMA_20', 'RSI_14']
    
    for i in range(50):
        candle = {
            'timestamp': i,
            'open': 100 + i,
            'high': 105 + i,
            'low': 95 + i,
            'close': 102 + i,
            'volume': 1000 + i * 10,
            'SMA_20': 100 + i * 0.5,
            'RSI_14': 50 + (i % 20)
        }
        buffer.add_candle(candle)
        
        if buffer.is_ready():
            sequence = buffer.get_sequence(feature_cols)
            print(f"Candle {i}: Sequence shape = {sequence.shape}")
