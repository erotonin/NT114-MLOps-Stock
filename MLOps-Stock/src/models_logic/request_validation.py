from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

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
)


def normalize_ticker(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if not symbol or len(symbol) > 12 or not symbol.isalnum():
        raise ValueError("ticker must be 1-12 alphanumeric characters")
    return symbol


def validate_feature_matrix(
    features: Mapping[str, Sequence[float]], *, min_rows: int = 1
) -> int:
    if not isinstance(features, Mapping):
        raise ValueError("features must be an object containing feature arrays")

    missing = [name for name in FEATURE_COLUMNS if name not in features]
    if missing:
        raise ValueError(f"missing required features: {', '.join(missing)}")

    lengths = {}
    for name in FEATURE_COLUMNS:
        values = features[name]
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
            raise ValueError(f"feature '{name}' must be an array")
        lengths[name] = len(values)

    unique_lengths = set(lengths.values())
    if len(unique_lengths) != 1:
        raise ValueError(f"feature arrays must have equal lengths: {lengths}")

    rows = next(iter(unique_lengths), 0)
    if rows < min_rows:
        raise ValueError(f"at least {min_rows} rows are required; received {rows}")

    for name in FEATURE_COLUMNS:
        for index, value in enumerate(features[name]):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"feature '{name}' at index {index} must be numeric")
            if not math.isfinite(float(value)):
                raise ValueError(f"feature '{name}' at index {index} must be finite")

    return rows
