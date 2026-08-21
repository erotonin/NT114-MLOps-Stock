from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline.feature_store import materialize_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize local CSV snapshots into a versioned feature store.")
    parser.add_argument("--symbols", default="FPT,VCB,VNM,HPG")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "feature_store")
    args = parser.parse_args()

    output = args.output.resolve()
    records = []
    for raw_symbol in args.symbols.split(","):
        symbol = raw_symbol.strip().upper()
        if not symbol:
            continue
        record = materialize_snapshot(
            symbol,
            ROOT / "data" / f"{symbol}.csv",
            output,
            version=args.version,
        )
        records.append(record)

    if not records:
        raise ValueError("at least one symbol is required")
    catalog = {
        "feature_store_version": args.version,
        "root": str(output),
        "symbols": records,
        "status": "ok",
    }
    catalog_path = output / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(json.dumps(catalog, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
