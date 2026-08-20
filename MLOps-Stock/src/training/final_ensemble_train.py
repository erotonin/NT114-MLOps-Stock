import traceback
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.training.ensemble_trainer import train_ensemble

import argparse

def train_production_models(symbols=None):
    if not symbols:
        symbols = ["VNM", "VCB", "HPG", "FPT"]
    print(f"Starting Production Training for: {symbols}")
    
    failed = []
    
    for symbol in symbols:
        try:
            print(f"\nTraining Hybrid Ensemble for {symbol}...")
            train_ensemble(symbol=symbol, epochs=30)
            print(f"Completed {symbol}")
        except Exception as e:
            print(f"Error training {symbol}: {e}")
            traceback.print_exc()
            failed.append(symbol)

    if failed:
        print(f"\nTraining failed for: {failed}")
        sys.exit(1)
    else:
        print("\nAll models trained successfully! Artifacts saved to ./models/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Stock Predictor Models')
    parser.add_argument('--symbol', type=str, default=None, help='A specific stock symbol to train')
    args = parser.parse_args()
    
    if args.symbol:
        train_production_models([args.symbol.upper()])
    else:
        train_production_models()
