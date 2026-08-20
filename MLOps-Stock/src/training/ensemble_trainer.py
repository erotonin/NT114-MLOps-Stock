import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import json
import random
import joblib
import mlflow

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.models_logic.tft_model import TFTSkeleton
from src.models_logic.lgbm_model import LGBMModel
from src.data_pipeline.yahoo_data import YahooData

class EnsembleDataset(Dataset):
    def __init__(self, data, target, window_size=60):
        self.data = torch.FloatTensor(data)
        self.target = torch.FloatTensor(target)
        self.window_size = window_size

    def __len__(self):
        return len(self.data) - self.window_size

    def __getitem__(self, idx):
        return (
            self.data[idx : idx + self.window_size],
            self.target[idx + self.window_size]
        )

def train_ensemble(symbol="FPT", epochs=50, window_size=60, data_dir="data", models_dir="models"):
    # nosemgrep: hardcoded-password-assignment
    MODELS_DIR = os.fspath(models_dir)
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    import pandas as pd
    data_path = os.path.join(os.fspath(data_dir), f"{symbol.upper()}.csv")
    if not os.path.exists(data_path):
        raise RuntimeError(f"Data file {data_path} not found. Ensure DVC pull was executed.")
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    if df.empty:
        raise RuntimeError(f"No valid training data for {symbol} in {data_path}")
    
    # 13 Features
    features = [
        'open', 'high', 'low', 'close', 'volume', 
        'sma_10', 'sma_20', 'rsi', 'macd', 'macd_signal', 
        'bb_upper', 'bb_lower', 'log_return'
    ]
    X = df[features].values
    y = df['target'].values

    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    # Split First to avoid Data Leakage
    split_idx = int(len(df) * 0.8)
    
    X_train_raw, X_val_raw = X[:split_idx], X[split_idx:]
    y_train_raw, y_val_raw = y[:split_idx], y[split_idx:]
    
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    
    # Fit ONLY on training data
    X_train = scaler_x.fit_transform(X_train_raw)
    y_train = scaler_y.fit_transform(y_train_raw.reshape(-1, 1)).flatten()
    
    # Transform validation data
    X_val = scaler_x.transform(X_val_raw)
    y_val = scaler_y.transform(y_val_raw.reshape(-1, 1)).flatten()
    
    # --- 1. Train TFT (Deep Learning) ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tft = TFTSkeleton(num_features=len(features)).to(device)
    
    train_ds = EnsembleDataset(X_train, y_train, window_size)
    val_ds = EnsembleDataset(X_val, y_val, window_size)
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)
    
    optimizer = optim.Adam(tft.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    best_val_loss = float("inf")
    best_state = None
    patience = 10
    patience_count = 0
    
    print(f"Training TFT for {symbol}...")
    for epoch in range(epochs):
        tft.train()
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            pred = tft(bx).flatten()
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()

        tft.eval()
        val_losses = []
        with torch.no_grad():
            for vx, vy in val_loader:
                vx, vy = vx.to(device), vy.to(device)
                vpred = tft(vx).flatten()
                val_losses.append(criterion(vpred, vy).item())

        epoch_val_loss = float(np.mean(val_losses)) if val_losses else float("inf")
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in tft.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1

        if patience_count >= patience:
            print(f"TFT early stopping at epoch {epoch + 1}, best val loss={best_val_loss:.5f}")
            break
    
    if best_state is not None:
        tft.load_state_dict(best_state)
    tft.eval()
    
    # --- 2. Train LightGBM (GBDT) ---
    print(f"Training LightGBM for {symbol}...")
    lgbm = LGBMModel()
    lgbm.train(X_train, y_train, X_val, y_val)
    
    # --- 3. Train Stacking Meta-Learner ---
    print(f"Training Stacking Meta-Learner for {symbol}...")
    tft_preds_val = []
    with torch.no_grad():
        for bx, by in val_loader:
            tft_preds_val.extend(tft(bx.to(device)).cpu().numpy().flatten())
    
    lgbm_preds_val = lgbm.predict(X_val[window_size:])
    
    meta_X = np.column_stack([tft_preds_val, lgbm_preds_val])
    meta_y = y_val[window_size:]
    if len(meta_X) < 40:
        raise RuntimeError(
            f"Not enough validation samples for meta split on {symbol}: {len(meta_X)}"
        )

    meta_split_idx = int(len(meta_X) * 0.6)
    meta_split_idx = max(20, min(meta_split_idx, len(meta_X) - 20))
    meta_X_train, meta_X_test = meta_X[:meta_split_idx], meta_X[meta_split_idx:]
    meta_y_train, meta_y_test = meta_y[:meta_split_idx], meta_y[meta_split_idx:]

    meta_learner = LinearRegression()
    meta_learner.fit(meta_X_train, meta_y_train)
    
    # --- 4. Save ALL artifacts directly to MODELS_DIR ---
    print(f"Saving all artifacts for {symbol} to {MODELS_DIR}...")
    sym = symbol.upper()
    
    # Save scalers
    joblib.dump(scaler_x, os.path.join(MODELS_DIR, f"{sym}_scaler_x.pkl"))
    joblib.dump(scaler_y, os.path.join(MODELS_DIR, f"{sym}_scaler_y.pkl"))
    
    # Save TFT model
    tft_path = os.path.join(MODELS_DIR, f"{sym}_tft_model.pt")
    torch.save(tft.cpu().state_dict(), tft_path)
    
    # Save LightGBM model
    lgbm_path = os.path.join(MODELS_DIR, f"{sym}_lgbm_model.pkl")
    joblib.dump(lgbm.model, lgbm_path)
    
    # Save Meta-Learner
    meta_path = os.path.join(MODELS_DIR, f"{sym}_meta_learner.pkl")
    joblib.dump(meta_learner, meta_path)
    
    # Manifest
    manifest = {
        "symbol": sym,
        "run_type": "stacking_ensemble",
        "horizon": 3,
        "model_version": os.getenv("MODEL_VERSION", "local-" + sym.lower()),
        "code_commit": os.getenv("GIT_COMMIT", "working-tree"),
        "data_version": os.getenv("DATA_VERSION", "local-snapshot"),
        "meta_input_space": "scaled_target",
        "artifacts": [
            f"{sym}_scaler_x.pkl", f"{sym}_scaler_y.pkl",
            f"{sym}_tft_model.pt", f"{sym}_lgbm_model.pkl", f"{sym}_meta_learner.pkl"
        ],
        "features": features,
        "window_size": window_size,
        "tft_best_val_loss": best_val_loss,
    }

    # Final Verification
    ensemble_preds = meta_learner.predict(meta_X_test)
    mae = np.mean(np.abs(ensemble_preds - meta_y_test))
    rmse = np.sqrt(np.mean((ensemble_preds - meta_y_test) ** 2))
    
    prev_close_val_all = df['close'].values[split_idx + window_size - 1 : -1]
    y_true_val_price_all = y_val_raw[window_size:]
    prev_close_val = prev_close_val_all[meta_split_idx:]
    y_true_val_price = y_true_val_price_all[meta_split_idx:]
    pred_price = scaler_y.inverse_transform(ensemble_preds.reshape(-1, 1)).flatten()
    directional_acc = np.mean((pred_price > prev_close_val) == (y_true_val_price > prev_close_val)) * 100.0

    manifest["mae"] = float(mae)
    manifest["rmse"] = float(rmse)
    manifest["directional_acc"] = float(directional_acc)
    manifest["validation_samples"] = int(len(meta_y_test))
    manifest_path = os.path.join(MODELS_DIR, f"{sym}_artifact_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
            
    print(f"Validation (Stacked): MAE={mae:.4f}, RMSE={rmse:.4f}, Directional Acc={directional_acc:.2f}%")
    
    # --- 5. MLflow Tracking ---
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{os.path.abspath('mlflow.db')}")
    if tracking_uri.startswith("file:") and os.getenv("MLFLOW_ALLOW_FILE_STORE", "false").lower() != "true":
        tracking_uri = f"sqlite:///{os.path.abspath('mlflow.db')}"
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("stock_ensemble_training")
    with mlflow.start_run(run_name=f"train_{sym}_{random.randint(1000,9999)}"):
        mlflow.log_param("symbol", sym)
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("window_size", window_size)
        mlflow.log_param("features", len(features))
        mlflow.log_param("horizon", 3)
        mlflow.log_param("data_version", manifest["data_version"])
        mlflow.set_tag("model_version", manifest["model_version"])
        mlflow.set_tag("code_commit", manifest["code_commit"])
        
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("directional_acc", directional_acc)
        mlflow.log_metric("tft_best_val_loss", best_val_loss)
        
        # Log all artifacts in MODELS_DIR related to this symbol
        for f in manifest["artifacts"]:
            mlflow.log_artifact(os.path.join(MODELS_DIR, f), artifact_path="models")
        mlflow.log_artifact(manifest_path, artifact_path="models")
        
    return tft, lgbm, meta_learner

if __name__ == "__main__":
    train_ensemble(symbol="FPT", epochs=10)
