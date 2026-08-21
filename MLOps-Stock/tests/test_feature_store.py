from pathlib import Path

import pandas as pd
import pytest

from src.data_pipeline.feature_store import FEATURE_COLUMNS, load_metadata, materialize_snapshot


def make_snapshot(path: Path) -> None:
    frame = pd.DataFrame({"Date": ["2026-01-01", "2026-01-02"]})
    for column in FEATURE_COLUMNS:
        frame[column] = [1.0, 2.0]
    frame.to_csv(path, index=False)


def test_materialize_snapshot_creates_versioned_artifact(tmp_path):
    source = tmp_path / "FPT.csv"
    store = tmp_path / "store"
    make_snapshot(source)

    metadata = materialize_snapshot("fpt", source, store, version="v1")
    assert metadata["status"] == "ok"
    assert metadata["symbol"] == "FPT"
    assert metadata["feature_store_version"] == "v1"
    assert metadata["row_count"] == 2
    assert metadata["null_count"] == 0
    assert (store / "FPT" / "v1" / "features.csv").exists()
    assert load_metadata(store, "FPT", "v1")["sha256"] == metadata["sha256"]


def test_materialize_snapshot_rejects_missing_column(tmp_path):
    source = tmp_path / "FPT.csv"
    frame = pd.DataFrame({"Date": ["2026-01-01"], "close": [1.0]})
    frame.to_csv(source, index=False)
    with pytest.raises(ValueError, match="missing feature-store columns"):
        materialize_snapshot("FPT", source, tmp_path / "store")
