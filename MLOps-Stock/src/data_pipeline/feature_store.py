from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

FEATURE_STORE_VERSION = "v1"
FEATURE_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "sma_10",
    "sma_20",
    "rsi",
    "macd",
    "macd_signal",
    "bb_upper",
    "bb_lower",
    "log_return",
    "target",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize_snapshot(
    symbol: str, source_csv: Path, store_root: Path, version: str = FEATURE_STORE_VERSION
) -> dict[str, object]:
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalnum():
        raise ValueError("symbol must be alphanumeric")
    if not source_csv.exists():
        raise FileNotFoundError(source_csv)

    frame = pd.read_csv(source_csv)
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing feature-store columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("feature-store snapshot cannot be empty")
    if "Date" not in frame.columns:
        raise ValueError("feature-store snapshot requires Date column")

    destination = store_root / symbol / version
    destination.mkdir(parents=True, exist_ok=True)
    feature_path = destination / "features.csv"
    frame.to_csv(feature_path, index=False)

    numeric = frame.loc[:, FEATURE_COLUMNS]
    metadata = {
        "symbol": symbol,
        "feature_store_version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source_csv),
        "feature_columns": list(FEATURE_COLUMNS),
        "row_count": int(len(frame)),
        "date_min": str(frame["Date"].min()),
        "date_max": str(frame["Date"].max()),
        "null_count": int(numeric.isna().sum().sum()),
        "sha256": _sha256(feature_path),
        "bytes": feature_path.stat().st_size,
        "status": "ok",
    }
    metadata_path = destination / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_metadata(store_root: Path, symbol: str, version: str = FEATURE_STORE_VERSION) -> dict[str, object]:
    path = store_root / symbol.strip().upper() / version / "metadata.json"
    return json.loads(path.read_text(encoding="utf-8"))
