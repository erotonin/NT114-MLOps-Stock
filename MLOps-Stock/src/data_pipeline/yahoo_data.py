import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.data_pipeline.indicators import add_technical_indicators
except ImportError:
    from indicators import add_technical_indicators

class YahooData:
    def __init__(self):
        # VN30 tickers on Yahoo Finance usually end with .VN (HOSE)
        self.ticker_map = {
            "ACB": "ACB.VN", "BCM": "BCM.VN", "BID": "BID.VN", "BVH": "BVH.VN", 
            "CTG": "CTG.VN", "FPT": "FPT.VN", "GAS": "GAS.VN", "GVR": "GVR.VN", 
            "HDB": "HDB.VN", "HPG": "HPG.VN", "MBB": "MBB.VN", "MSN": "MSN.VN", 
            "MWG": "MWG.VN", "PLX": "PLX.VN", "POW": "POW.VN", "SAB": "SAB.VN", 
            "SHB": "SHB.VN", "SSB": "SSB.VN", "SSI": "SSI.VN", "STB": "STB.VN", 
            "TCB": "TCB.VN", "TPB": "TPB.VN", "VCB": "VCB.VN", "VHM": "VHM.VN", 
            "VIB": "VIB.VN", "VIC": "VIC.VN", "VJC": "VJC.VN", "VNM": "VNM.VN", 
            "VPB": "VPB.VN", "VRE": "VRE.VN"
        }

    def _validate_contract(self, df: pd.DataFrame) -> bool:
        required_cols = {"open", "high", "low", "close", "volume"}
        if df is None or df.empty:
            return False
        if not required_cols.issubset(set(df.columns)):
            return False
        if not df.index.is_monotonic_increasing:
            return False

        # Basic integrity checks.
        if (df["volume"] < 0).any():
            return False
        if (df[["open", "high", "low", "close"]] <= 0).any().any():
            return False
        if (df["high"] < df["low"]).any():
            return False
        return True

    def get_historical_data(self, symbol, days=365):
        """
        Fetches daily OHLCV data from Yahoo Finance for a VN30 symbol.
        """
        yf_ticker = self.ticker_map.get(symbol.upper())
        if not yf_ticker:
            print(f"Symbol {symbol} not mapped to Yahoo ticker.")
            return None
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            df = yf.download(yf_ticker, start=start_date, end=end_date, progress=False)
            if df is not None and not df.empty:
                # Handle MultiIndex if present (Feature vs Ticker)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                # Rename columns to standard lowercase string
                df.columns = [str(col).lower() for col in df.columns]
                # Ensure chronological order and clean duplicate timestamps.
                df = df.sort_index()
                df = df[~df.index.duplicated(keep="last")]
                if not self._validate_contract(df):
                    print(f"Data contract validation failed for {symbol}")
                    return None

                # Technical indicators
                df = add_technical_indicators(df)

                # T+3 target (close price 3 days ahead, aligned with VN T+2.5 settlement)
                df['target'] = df['close'].shift(-3)

                required_cols = [
                    'open', 'high', 'low', 'close', 'volume',
                    'sma_10', 'sma_20', 'rsi', 'macd', 'macd_signal',
                    'bb_upper', 'bb_lower', 'log_return', 'target'
                ]
                clean = df.dropna(subset=required_cols)
                if len(clean) < 80:
                    print(f"Insufficient clean rows after feature pipeline for {symbol}: {len(clean)}")
                    return None
                return clean
            return None
        except Exception as e:
            print(f"Error fetching Yahoo data for {symbol}: {e}")
            return None

if __name__ == "__main__":
    # Test
    provider = YahooData()
    df = provider.get_historical_data("FPT", days=100)
    if df is not None:
        print(f"Successfully fetched {len(df)} rows for FPT.")
        print(df.tail())
    else:
        print("Failed to fetch FPT data.")
