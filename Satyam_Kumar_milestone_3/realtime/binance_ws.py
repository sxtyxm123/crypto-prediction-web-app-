"""
Binance WebSocket Client for Real-Time Price Streaming

Connects to Binance WebSocket API to receive live kline (candlestick) data
and maintains a rolling buffer for real-time predictions.
"""

import websocket
import json
import threading
import time
from collections import deque
from typing import Callable, Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BinanceWebSocket:
    """
    Real-time kline streaming from Binance WebSocket API
    
    Features:
    - Streams 1-minute candlestick data
    - Processes only closed candles
    - Maintains rolling buffer
    - Thread-safe operations
    """
    
    def __init__(
        self,
        symbol: str,
        interval: str = "1m",
        buffer_size: int = 100,
        on_candle_callback: Optional[Callable] = None
    ):
        """
        Initialize WebSocket client
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (default: '1m')
            buffer_size: Maximum buffer size
            on_candle_callback: Function to call when candle closes
        """
        self.symbol = symbol.lower()
        self.interval = interval
        self.buffer = deque(maxlen=buffer_size)
        self.on_candle_callback = on_candle_callback
        
        # WebSocket URL
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{interval}"
        
        # Connection state
        self.ws = None
        self.is_running = False
        self.thread = None
        
        logger.info(f"Initialized WebSocket for {symbol} ({interval})")
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Check if it's a kline event
            if 'k' not in data:
                return
            
            kline = data['k']
            
            # Only process closed candles
            if kline['x']:  # is_closed
                candle = {
                    'timestamp': kline['t'],
                    'open_time': datetime.fromtimestamp(kline['t'] / 1000),
                    'close_time': datetime.fromtimestamp(kline['T'] / 1000),
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v']),
                    'quote_volume': float(kline['q']),
                    'trades': int(kline['n'])
                }
                
                # Add to buffer
                self.buffer.append(candle)
                
                logger.info(
                    f"New candle: {self.symbol.upper()} "
                    f"Close: ${candle['close']:,.2f} "
                    f"Volume: {candle['volume']:.2f}"
                )
                
                # Call callback if provided
                if self.on_candle_callback:
                    self.on_candle_callback(candle)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_running = False
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        logger.info(f"WebSocket connected: {self.symbol.upper()}")
        self.is_running = True
    
    def start(self):
        """Start WebSocket connection in background thread"""
        if self.is_running:
            logger.warning("WebSocket already running")
            return
        
        def run_websocket():
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            self.ws.run_forever()
        
        self.thread = threading.Thread(target=run_websocket, daemon=True)
        self.thread.start()
        
        logger.info(f"Started WebSocket thread for {self.symbol.upper()}")
    
    def stop(self):
        """Stop WebSocket connection"""
        if self.ws:
            self.ws.close()
        self.is_running = False
        logger.info(f"Stopped WebSocket for {self.symbol.upper()}")
    
    def get_buffer(self) -> List[Dict]:
        """Get current buffer as list"""
        return list(self.buffer)
    
    def get_latest_candle(self) -> Optional[Dict]:
        """Get most recent candle"""
        return self.buffer[-1] if self.buffer else None
    
    def get_current_price(self) -> Optional[float]:
        """Get current close price"""
        latest = self.get_latest_candle()
        return latest['close'] if latest else None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def on_new_candle(candle):
        print(f"\n🕯️ New Candle Closed!")
        print(f"Time: {candle['close_time']}")
        print(f"Price: ${candle['close']:,.2f}")
        print(f"Volume: {candle['volume']:.2f}")
    
    # Start streaming
    ws_client = BinanceWebSocket(
        symbol="BTCUSDT",
        interval="1m",
        on_candle_callback=on_new_candle
    )
    
    ws_client.start()
    
    print("WebSocket started. Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
            if ws_client.buffer:
                current_price = ws_client.get_current_price()
                print(f"\rCurrent BTC Price: ${current_price:,.2f}", end="")
    except KeyboardInterrupt:
        print("\n\nStopping WebSocket...")
        ws_client.stop()
