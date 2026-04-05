"""
Test script for real-time inference engine

This script tests the live prediction functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realtime.inference import LiveInferenceEngine
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_live_prediction(symbol='BTCUSDT'):
    """Test live prediction for a symbol"""
    print("="*70)
    print(f"TESTING REAL-TIME PREDICTION FOR {symbol}")
    print("="*70)
    
    try:
        # Create inference engine
        print(f"\n1. Loading model and scalers for {symbol}...")
        engine = LiveInferenceEngine(symbol=symbol)
        print("   ✓ Model loaded successfully")
        
        # Make prediction
        print(f"\n2. Fetching live data from Binance and making prediction...")
        result = engine.predict(use_live_data=True)
        
        if 'error' in result:
            print(f"   ✗ Error: {result['error']}")
            return False
        
        # Display results
        print("\n" + "="*70)
        print("PREDICTION RESULTS")
        print("="*70)
        print(f"\n📊 Symbol: {result['symbol']}")
        print(f"💵 Current Price: ${result['current_price']:,.2f}")
        print(f"🔮 Predicted Price (1h): ${result['predicted_price']:,.2f}")
        print(f"📈 Expected Return: {result['predicted_return_pct']:+.2f}%")
        print(f"{'📈' if result['trend'] == 'UP' else '📉'} Trend: {result['trend']}")
        print(f"🎯 Confidence: {result['confidence']*100:.1f}%")
        print(f"📊 Volatility: {result['volatility']*100:.2f}%")
        print(f"📉 Lower Bound: ${result['lower_bound']:,.2f}")
        print(f"📈 Upper Bound: ${result['upper_bound']:,.2f}")
        print(f"⏰ Timestamp: {result['timestamp']}")
        
        print("\n" + "="*70)
        print("✓ TEST PASSED")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test Bitcoin
    success = test_live_prediction('BTCUSDT')
    
    if success:
        print("\n\n🎉 Real-time prediction is working correctly!")
        print("The API server will now show LIVE prices from Binance.")
    else:
        print("\n\n❌ There was an issue. Please check the error messages above.")
