import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_sma(prices: pd.Series, window: int = 20) -> pd.Series:
    """Simple Moving Average"""
    return prices.rolling(window=window).mean()

def calculate_ema(prices: pd.Series, window: int = 20) -> pd.Series:
    """Exponential Moving Average"""
    return prices.ewm(span=window, adjust=False).mean()

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: pd.Series) -> tuple:
    """MACD (Moving Average Convergence Divergence)"""
    ema_12 = prices.ewm(span=12, adjust=False).mean()
    ema_26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def detect_trend(prices: pd.Series, short_window: int = 20, long_window: int = 50) -> str:
    """Detect trend based on SMA crossover"""
    sma_short = calculate_sma(prices, short_window)
    sma_long = calculate_sma(prices, long_window)
    
    if len(prices) < long_window:
        return "INSUFFICIENT_DATA"
    
    current_short = sma_short.iloc[-1]
    current_long = sma_long.iloc[-1]
    prev_short = sma_short.iloc[-2]
    prev_long = sma_long.iloc[-2]
    
    # Golden Cross (bullish)
    if prev_short <= prev_long and current_short > current_long:
        return "GOLDEN_CROSS_BULLISH"
    
    # Death Cross (bearish)
    if prev_short >= prev_long and current_short < current_long:
        return "DEATH_CROSS_BEARISH"
    
    # Uptrend
    if current_short > current_long:
        return "UPTREND"
    
    # Downtrend
    if current_short < current_long:
        return "DOWNTREND"
    
    return "SIDEWAYS"

def get_signal(indicators: dict) -> str:
    """Generate trading signal from indicators"""
    rsi = indicators.get('rsi', 50)
    trend = indicators.get('trend', 'SIDEWAYS')
    macd_hist = indicators.get('macd_histogram', 0)
    
    # Strong Buy
    if rsi < 30 and trend == "UPTREND" and macd_hist > 0:
        return "STRONG_BUY"
    
    # Buy
    if rsi < 30 or (trend == "GOLDEN_CROSS_BULLISH"):
        return "BUY"
    
    # Strong Sell
    if rsi > 70 and trend == "DOWNTREND" and macd_hist < 0:
        return "STRONG_SELL"
    
    # Sell
    if rsi > 70 or (trend == "DEATH_CROSS_BEARISH"):
        return "SELL"
    
    # Hold
    return "HOLD"

def analyze_coin(df: pd.DataFrame) -> dict:
    """Analyze a single coin and return indicators"""
    if len(df) < 50:
        return {
            'signal': 'INSUFFICIENT_DATA',
            'trend': 'INSUFFICIENT_DATA',
            'rsi': None,
            'sma_20': None,
            'sma_50': None
        }
    
    prices = df['current_price']
    
    # Calculate indicators
    sma_20 = calculate_sma(prices, 20).iloc[-1]
    sma_50 = calculate_sma(prices, 50).iloc[-1]
    rsi = calculate_rsi(prices, 14).iloc[-1]
    macd, signal, histogram = calculate_macd(prices)
    trend = detect_trend(prices)
    
    current_price = prices.iloc[-1]
    
    indicators = {
        'current_price': current_price,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'rsi': rsi,
        'macd': macd.iloc[-1],
        'macd_signal': signal.iloc[-1],
        'macd_histogram': histogram.iloc[-1],
        'trend': trend
    }
    
    indicators['signal'] = get_signal(indicators)
    
    return indicators