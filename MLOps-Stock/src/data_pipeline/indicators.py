import pandas as pd
import numpy as np

def add_technical_indicators(df):
    """
    Adds a comprehensive set of indicators: SMA, RSI, MACD, Bollinger Bands, and Log Returns.
    """
    if df is None or len(df) < 26:
        return df
    
    # 1. Simple Moving Averages
    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    
    # 2. RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 3. MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # 4. Bollinger Bands
    ma_20 = df['close'].rolling(window=20).mean()
    std_20 = df['close'].rolling(window=20).std()
    df['bb_upper'] = ma_20 + (std_20 * 2)
    df['bb_lower'] = ma_20 - (std_20 * 2)
    
    # 5. Price Return
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # Keep indicator NaNs (warm-up window) to avoid future leakage.
    # Downstream pipeline should drop rows with NaNs after all features/targets are created.
    return df
