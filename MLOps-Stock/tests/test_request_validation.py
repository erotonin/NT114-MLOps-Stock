import math

import pytest

from src.models_logic.request_validation import (
    FEATURE_COLUMNS,
    normalize_ticker,
    validate_feature_matrix,
)


def valid_features(rows=3):
    return {name: [1.0] * rows for name in FEATURE_COLUMNS}


def test_valid_feature_matrix_returns_row_count():
    assert validate_feature_matrix(valid_features(5)) == 5
    assert normalize_ticker(" fpt ") == "FPT"


def test_missing_feature_is_rejected():
    features = valid_features()
    features.pop("close")
    with pytest.raises(ValueError, match="missing required features"):
        validate_feature_matrix(features)


def test_misaligned_feature_lengths_are_rejected():
    features = valid_features()
    features["volume"] = [1.0, 2.0]
    with pytest.raises(ValueError, match="equal lengths"):
        validate_feature_matrix(features)


def test_non_finite_values_are_rejected():
    features = valid_features()
    features["close"][1] = math.nan
    with pytest.raises(ValueError, match="finite"):
        validate_feature_matrix(features)


def test_invalid_ticker_is_rejected():
    with pytest.raises(ValueError, match="alphanumeric"):
        normalize_ticker("FPT-")
