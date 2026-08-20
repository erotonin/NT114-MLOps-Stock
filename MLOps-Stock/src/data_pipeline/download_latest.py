import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data_pipeline.yahoo_data import YahooData


def download_all(symbols=None, data_dir="data"):
    symbols = symbols or ["VNM", "VCB", "HPG", "FPT"]
    provider = YahooData()
    target_dir = Path(data_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    success = True
    for sym in symbols:
        print(f"Downloading data for {sym}...")
        df = provider.get_historical_data(sym, days=1000)
        if df is not None:
            save_path = target_dir / f"{sym.upper()}.csv"
            df.to_csv(save_path)
            print(f"Saved {len(df)} rows to {save_path}")
        else:
            print(f"Failed to fetch data for {sym}")
            success = False

    if not success:
        print("Some downloads failed. Exiting with error.")
        raise RuntimeError("data download failed")


if __name__ == "__main__":
    download_all()
